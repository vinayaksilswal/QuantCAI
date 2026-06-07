"""
Post-Quantum Cryptography (PQC) Scanner Engine
================================================
Enterprise-grade scanning engine that evaluates a domain's TLS configuration
against post-quantum cryptographic threats based on NIST FIPS 203/204/205
migration timelines.

This module performs:
  1. TLS handshake and cipher suite extraction
  2. Full certificate chain cryptographic analysis
  3. Key exchange quantum-safety assessment
  4. Structured risk scoring and CBOM generation

Risk scoring maps to NIST SP 1800-38C "Migration to Post-Quantum Cryptography"
and aligns with the CNSA 2.0 timeline (NSA, 2022).

Copyright (c) 2026 QuantCAI — All rights reserved.
"""

from __future__ import annotations

import asyncio
import logging
import socket
import ssl
import uuid
import ipaddress
from datetime import datetime, timezone
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import (
    dsa,
    ec,
    ed448,
    ed25519,
    rsa,
    x448,
    x25519,
)
from cryptography.x509.oid import ExtensionOID

from models.cyclonedx_models import (
    CycloneDXCBOM,
    Component,
    CryptoProperties,
    AlgorithmProperties,
    CertificateProperties,
    ProtocolProperties,
    CipherSuiteAlgorithm,
    Metadata,
    Tool,
    Dependency
)


logger = logging.getLogger("quantcai.pqc_scanner")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CONNECTION_TIMEOUT_S = 5
_DEFAULT_PORT = 443

# NIST-referenced PQC hybrid key exchange identifiers
# These appear in cipher suite names when the server supports PQC hybrids
PQC_HYBRID_KEYWORDS: frozenset[str] = frozenset({
    "mlkem",           # ML-KEM (FIPS 203) generic
    "x25519mlkem768",  # X25519 + ML-KEM-768 hybrid
    "x25519_mlkem768", # alternate formatting
    "secp256r1mlkem768",
    "mlkem768",
    "mlkem1024",
    "kyber",           # draft-era naming (Kyber → ML-KEM)
    "x25519kyber768",
    "pq_hybrid",
})

# Quantum-vulnerable key exchange prefixes
VULNERABLE_KEX_PREFIXES: tuple[str, ...] = (
    "ECDHE",
    "DHE",
    "ECDH",
    "DH",
)

# TLS version risk mapping
TLS_VERSION_RISK: dict[str, dict[str, Any]] = {
    "TLSv1":   {"label": "TLS 1.0", "risk": "CRITICAL", "points": 20},
    "TLSv1.1": {"label": "TLS 1.1", "risk": "CRITICAL", "points": 20},
    "TLSv1.2": {"label": "TLS 1.2", "risk": "WARNING",  "points": 5},
    "TLSv1.3": {"label": "TLS 1.3", "risk": "OK",       "points": 0},
}

# NIST SP 800-131A rev 2 & CNSA 2.0 references
NIST_REFERENCES: dict[str, str] = {
    "RSA":     "NIST SP 800-131A Rev 2 — RSA keys vulnerable to Shor's algorithm; "
               "migrate to ML-DSA (FIPS 204) by 2030",
    "ECC":     "NIST SP 800-186 — ECC keys (ECDSA/ECDH) vulnerable to Shor's algorithm; "
               "migrate to ML-DSA (FIPS 204) for signatures, ML-KEM (FIPS 203) for KEM",
    "DSA":     "NIST SP 800-131A Rev 2 — DSA is deprecated and quantum-vulnerable; "
               "migrate to ML-DSA (FIPS 204)",
    "EdDSA":   "NIST IR 8413 — Ed25519/Ed448 quantum safety is under active research; "
               "consider SLH-DSA (FIPS 205) as future-proof alternative",
    "KEX":     "CNSA 2.0 (NSA) — ECDHE/DHE key exchanges broken by CRQC; "
               "deploy ML-KEM-768 (FIPS 203) hybrid key exchange",
    "TLS_OLD": "NIST SP 800-52 Rev 2 — TLS 1.0/1.1 MUST be disabled; "
               "TLS 1.3 strongly recommended",
}


# ---------------------------------------------------------------------------
# Risk Score Weights (additive model, clamped to [0, 100])
# ---------------------------------------------------------------------------

_SCORE_RSA_2048    = 35.0
_SCORE_RSA_4096    = 20.0
_SCORE_RSA_OTHER   = 25.0
_SCORE_ECC         = 30.0
_SCORE_DSA         = 35.0
_SCORE_EDDSA       = 10.0
_SCORE_ECDHE_KEX   = 15.0
_SCORE_DHE_KEX     = 15.0
_SCORE_TLS_12      = 5.0
_SCORE_TLS_OLD     = 20.0
_SCORE_PQC_HYBRID  = -20.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _classify_public_key(
    public_key: Any,
) -> dict[str, Any]:
    """Classify a certificate's public key and return quantum-risk metadata."""

    if isinstance(public_key, rsa.RSAPublicKey):
        key_size = public_key.key_size
        algo_label = f"RSA-{key_size}"

        if key_size <= 2048:
            return {
                "algorithm": algo_label,
                "quantum_vulnerable": True,
                "vulnerability_reason": (
                    f"RSA-{key_size} is a legacy key size vulnerable to Shor's algorithm on a CRQC. "
                    "NIST and CNSA 2.0 mandate migrating to post-quantum signature schemes (e.g., ML-DSA / FIPS 204) by 2030."
                ),
                "severity": "CRITICAL",
                "risk_points": _SCORE_RSA_2048 if key_size == 2048 else _SCORE_RSA_2048 + 50.0,
            }
        elif key_size < 4096:
            return {
                "algorithm": algo_label,
                "quantum_vulnerable": True,
                "vulnerability_reason": (
                    f"RSA-{key_size} is quantum-vulnerable; larger keys only increase "
                    "classical attack cost, not quantum attack cost"
                ),
                "severity": "HIGH",
                "risk_points": _SCORE_RSA_OTHER,
            }
        else:
            return {
                "algorithm": algo_label,
                "quantum_vulnerable": True,
                "vulnerability_reason": (
                    f"RSA-{key_size} provides no meaningful quantum resistance — "
                    "Shor's algorithm is agnostic to key size"
                ),
                "severity": "HIGH",
                "risk_points": _SCORE_RSA_4096,
            }

    elif isinstance(public_key, ec.EllipticCurvePublicKey):
        curve_name = public_key.curve.name
        key_size = public_key.key_size
        algo_label = f"ECC-{curve_name}-{key_size}"
        
        is_legacy_256 = (key_size == 256 or curve_name in ("secp256r1", "prime256v1", "secp256k1"))
        
        return {
            "algorithm": algo_label,
            "quantum_vulnerable": True,
            "vulnerability_reason": (
                f"Elliptic Curve ({curve_name}-{key_size}) is a legacy ECC-256 configuration completely broken by Shor's algorithm on a CRQC. "
                "Prioritize migration to ML-DSA (FIPS 204) for digital signatures and ML-KEM (FIPS 203) for key exchange per CNSA 2.0."
                if is_legacy_256 else
                f"Elliptic Curve ({curve_name}) is broken by Shor's algorithm. Migrate to post-quantum alternatives per NIST guidelines."
            ),
            "severity": "CRITICAL" if is_legacy_256 else "HIGH",
            "risk_points": _SCORE_ECC,
        }

    elif isinstance(public_key, dsa.DSAPublicKey):
        key_size = public_key.key_size
        algo_label = f"DSA-{key_size}"
        return {
            "algorithm": algo_label,
            "quantum_vulnerable": True,
            "vulnerability_reason": (
                "DSA relies on discrete logarithm problem — trivially broken by "
                "Shor's algorithm; also deprecated by NIST"
            ),
            "severity": "CRITICAL",
            "risk_points": _SCORE_DSA,
        }

    elif isinstance(public_key, (ed25519.Ed25519PublicKey, ed448.Ed448PublicKey)):
        algo_label = type(public_key).__name__.replace("PublicKey", "")
        return {
            "algorithm": algo_label,
            "quantum_vulnerable": None,  # uncertain
            "vulnerability_reason": (
                f"{algo_label} is based on elliptic curve arithmetic and IS vulnerable "
                "to Shor's algorithm, but research into hash-based alternatives (SLH-DSA) "
                "is ongoing — status UNCERTAIN"
            ),
            "severity": "MEDIUM",
            "risk_points": _SCORE_EDDSA,
        }

    else:
        algo_label = type(public_key).__name__
        return {
            "algorithm": algo_label,
            "quantum_vulnerable": None,
            "vulnerability_reason": f"Unknown key type: {algo_label} — manual review required",
            "severity": "MEDIUM",
            "risk_points": 100.0,
        }


def _extract_san_domains(cert: x509.Certificate) -> list[str]:
    """Extract Subject Alternative Name DNS entries from a certificate."""
    try:
        san_ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        return san_ext.value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        return []


def _domain_matches_san(domain: str, san_list: list[str]) -> bool:
    """Check if a domain is covered by any SAN entry (including wildcards)."""
    domain_lower = domain.lower()
    for san in san_list:
        san_lower = san.lower()
        if san_lower == domain_lower:
            return True
        # Wildcard matching: *.example.com covers sub.example.com
        if san_lower.startswith("*."):
            wildcard_base = san_lower[2:]
            # Domain must be exactly one level deeper
            if domain_lower.endswith(f".{wildcard_base}"):
                # Ensure no extra dots in the matched prefix
                prefix = domain_lower[: -(len(wildcard_base) + 1)]
                if "." not in prefix:
                    return True
    return False


def _analyze_cipher_suite(cipher_name: str) -> dict[str, Any]:
    """Analyze a negotiated cipher suite for quantum safety."""
    cipher_upper = cipher_name.upper().replace("-", "_")

    # Check for PQC hybrid first
    cipher_check = cipher_name.lower().replace("-", "").replace("_", "")
    is_pqc = any(kw in cipher_check for kw in PQC_HYBRID_KEYWORDS)

    if is_pqc:
        return {
            "cipher_quantum_safe": True,
            "cipher_risk": "COMPLIANT",
            "cipher_reason": (
                f"Cipher suite '{cipher_name}' uses a PQC hybrid key exchange — "
                "compliant with CNSA 2.0 and FIPS 203 (ML-KEM)"
            ),
            "risk_points": _SCORE_PQC_HYBRID,
        }

    # Check for vulnerable key exchanges
    for prefix in VULNERABLE_KEX_PREFIXES:
        if cipher_upper.startswith(prefix):
            return {
                "cipher_quantum_safe": False,
                "cipher_risk": "VULNERABLE",
                "cipher_reason": (
                    f"Key exchange '{prefix}' in '{cipher_name}' is quantum-vulnerable — "
                    "a CRQC can solve the underlying DH/ECDH problem in polynomial time"
                ),
                "risk_points": _SCORE_ECDHE_KEX,
            }

    # Fallback — no recognized KEX prefix, conservative warning
    return {
        "cipher_quantum_safe": False,
        "cipher_risk": "UNKNOWN",
        "cipher_reason": (
            f"Cipher suite '{cipher_name}' — could not determine key exchange "
            "quantum safety; manual review recommended"
        ),
        "risk_points": 50.0,
    }


def _compute_risk_level(score: float) -> str:
    """Map a numeric risk score to a human-readable risk level."""
    if score >= 80.0:
        return "CRITICAL"
    elif score >= 60.0:
        return "HIGH"
    elif score >= 40.0:
        return "MEDIUM"
    elif score >= 20.0:
        return "LOW"
    else:
        return "COMPLIANT"


def _format_subject(name: x509.Name) -> str:
    """Format an x509 Name into a human-readable string (e.g. 'CN=example.com, O=Org')."""
    parts: list[str] = []
    for attr in name:
        try:
            oid_name = attr.oid._name  # type: ignore[attr-defined]
        except AttributeError:
            oid_name = attr.oid.dotted_string
        parts.append(f"{oid_name}={attr.value}")
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Public API — Synchronous
# ---------------------------------------------------------------------------

def scan_domain(domain: str, port: Optional[int] = None) -> dict[str, Any]:
    """
    Perform a comprehensive post-quantum cryptography readiness scan
    against a TLS-enabled domain or IP target.
    """

    scan_start = datetime.now(timezone.utc)
    domain = domain.strip().lower()

    # Strip accidental protocol/path prefixes
    if domain.startswith("https://"):
        domain = domain[len("https://"):]
    if domain.startswith("http://"):
        domain = domain[len("http://"):]
    
    # Split host and port
    if ":" in domain:
        parts = domain.split(":")
        host = parts[0].split("/")[0]
        try:
            port = int(parts[1].split("/")[0])
        except ValueError:
            port = port or _DEFAULT_PORT
    else:
        host = domain.split("/")[0]
        port = port or _DEFAULT_PORT

    # ── TLS Handshake ─────────────────────────────────────────────────
    try:
        ctx = ssl.create_default_context()
        
        # Check if the host is internal (private network or localhost)
        is_internal = False
        try:
            if host.lower() == "localhost" or host.endswith(".local") or host.endswith(".lan"):
                is_internal = True
            else:
                try:
                    ip = ipaddress.ip_address(host)
                    if ip.is_private or ip.is_loopback:
                        is_internal = True
                except ValueError:
                    # Resolve domain name to check resolved IP
                    try:
                        ip_str = socket.gethostbyname(host)
                        ip = ipaddress.ip_address(ip_str)
                        if ip.is_private or ip.is_loopback:
                            is_internal = True
                    except Exception:
                        pass
        except Exception:
            pass

        if is_internal:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection(
            (host, port), timeout=_CONNECTION_TIMEOUT_S
        ) as raw_sock:
            server_hostname = host if not is_internal else None
            # Also avoid passing raw IP as server_hostname to avoid SNI parse failures
            is_ip = False
            try:
                socket.inet_aton(host)
                is_ip = True
            except socket.error:
                pass
            if is_ip:
                server_hostname = None

            with ctx.wrap_socket(raw_sock, server_hostname=server_hostname) as ssock:
                # Cipher suite
                cipher_info = ssock.cipher()  # (name, version, bits)
                tls_version_raw = ssock.version()  # e.g. "TLSv1.3"

                # Certificate chain (DER-encoded)
                der_chain: list[bytes] = ssock.getpeercert(binary_form=True)  # type: ignore[assignment]
                peer_cert_decoded = ssock.getpeercert()

                # Try to pull the full chain via the undocumented _sslobj
                chain_ders: list[bytes] = []
                try:
                    # CPython ≥ 3.13 exposes get_verified_chain()
                    raw_chain = ssock._sslobj.get_verified_chain()  # type: ignore[union-attr]
                    if raw_chain:
                        chain_ders = [
                            cert_obj.public_bytes(ssl._ssl.ENCODING_DER)  # type: ignore[attr-defined]
                            for cert_obj in raw_chain
                        ]
                except (AttributeError, Exception):
                    pass

                if not chain_ders:
                    # Fallback: only the leaf cert is available
                    if isinstance(der_chain, bytes):
                        chain_ders = [der_chain]
                    elif isinstance(der_chain, (list, tuple)):
                        chain_ders = list(der_chain)
                    else:
                        chain_ders = [ssock.getpeercert(binary_form=True)]  # type: ignore

    except socket.timeout:
        logger.warning("Connection to %s:%d timed out after %ds", host, port, _CONNECTION_TIMEOUT_S)
        return _error_result(domain, scan_start, "CONNECTION_TIMEOUT",
                             f"Connection to {host}:{port} timed out after {_CONNECTION_TIMEOUT_S}s")

    except ConnectionRefusedError:
        logger.warning("Connection to %s:%d refused", host, port)
        return _error_result(domain, scan_start, "CONNECTION_REFUSED",
                             f"Connection to {host}:{port} was refused by the remote host")

    except ssl.SSLCertVerificationError as exc:
        logger.warning("Certificate verification failed for %s:%d: %s", host, port, exc)
        return _error_result(domain, scan_start, "CERTIFICATE_ERROR",
                             f"Certificate verification failed: {exc}")

    except ssl.SSLError as exc:
        logger.warning("SSL error for %s:%d: %s", host, port, exc)
        return _error_result(domain, scan_start, "SSL_ERROR",
                             f"SSL/TLS handshake error: {exc}")

    except OSError as exc:
        logger.warning("Network error connecting to %s:%d: %s", host, port, exc)
        return _error_result(domain, scan_start, "NETWORK_ERROR",
                             f"Network error: {exc}")

    except Exception as exc:
        logger.exception("Unexpected error scanning %s:%d", host, port)
        return _error_result(domain, scan_start, "UNEXPECTED_ERROR",
                             f"Unexpected error: {exc}")

    # ── Parse Cipher Info ─────────────────────────────────────────────
    cipher_name = cipher_info[0] if cipher_info else "UNKNOWN"
    cipher_tls_version = cipher_info[1] if cipher_info and len(cipher_info) > 1 else ""
    cipher_bits = cipher_info[2] if cipher_info and len(cipher_info) > 2 else 0

    tls_label = tls_version_raw or cipher_tls_version or "UNKNOWN"
    tls_meta = TLS_VERSION_RISK.get(tls_label, {"label": tls_label, "risk": "UNKNOWN", "points": 0})

    cipher_analysis = _analyze_cipher_suite(cipher_name)

    # ── Analyze Certificate Chain ─────────────────────────────────────
    risk_points: float = 0.0
    cert_results: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    total_assets = 0
    vulnerable_assets = 0
    compliant_assets = 0

    for idx, der_bytes in enumerate(chain_ders):
        total_assets += 1
        try:
            cert = x509.load_der_x509_certificate(der_bytes)
        except Exception as exc:
            logger.warning("Failed to parse certificate #%d in chain for %s: %s", idx, domain, exc)
            cert_results.append({
                "index": idx,
                "error": f"Failed to parse certificate: {exc}",
            })
            vulnerable_assets += 1
            continue

        # Subject / Issuer
        subject_str = _format_subject(cert.subject)
        issuer_str = _format_subject(cert.issuer)

        # Signature algorithm
        sig_algo = cert.signature_algorithm_oid._name if hasattr(  # type: ignore[attr-defined]
            cert.signature_algorithm_oid, '_name'
        ) else str(cert.signature_algorithm_oid.dotted_string)

        # Expiry analysis (compat: cryptography < 42 uses not_valid_after)
        try:
            expires_at = cert.not_valid_after_utc  # type: ignore[attr-defined]
        except AttributeError:
            # cryptography < 42: not_valid_after returns a naive UTC datetime
            expires_at = cert.not_valid_after.replace(tzinfo=timezone.utc)
        days_until_expiry = (expires_at - datetime.now(timezone.utc)).days
        expiry_warning = days_until_expiry < 90

        # SAN coverage (leaf cert only)
        san_domains = _extract_san_domains(cert)
        san_covers_domain = _domain_matches_san(domain, san_domains) if idx == 0 else None

        # Public key classification
        pub_key = cert.public_key()
        key_info = _classify_public_key(pub_key)

        cert_risk_points = key_info["risk_points"]
        risk_points += cert_risk_points

        if key_info["quantum_vulnerable"] is True:
            vulnerable_assets += 1
        elif key_info["quantum_vulnerable"] is False:
            compliant_assets += 1
        else:
            # uncertain
            vulnerable_assets += 1

        cert_record: dict[str, Any] = {
            "index": idx,
            "subject": subject_str,
            "issuer": issuer_str,
            "serial_number": str(cert.serial_number),
            "algorithm": key_info["algorithm"],
            "signature_algorithm": sig_algo,
            "quantum_vulnerable": key_info["quantum_vulnerable"],
            "vulnerability_reason": key_info["vulnerability_reason"],
            "severity": key_info["severity"],
            "expires_at": expires_at.strftime("%Y-%m-%d"),
            "days_until_expiry": days_until_expiry,
            "expiry_warning": expiry_warning,
        }

        if idx == 0:
            cert_record["san_domains"] = san_domains
            cert_record["san_covers_domain"] = san_covers_domain

        cert_results.append(cert_record)

        # ── Build Findings ────────────────────────────────────────────
        # Certificate key finding
        cert_label = "Leaf" if idx == 0 else f"Intermediate/Root #{idx}"
        findings.append({
            "severity": key_info["severity"],
            "category": "CERTIFICATE_KEY",
            "title": f"{key_info['algorithm']} Public Key Detected ({cert_label} Certificate)",
            "description": key_info["vulnerability_reason"],
            "affected_asset": subject_str,
            "nist_reference": NIST_REFERENCES.get(
                _key_family(pub_key), "See NIST PQC Migration resources"
            ),
            "remediation": _remediation_for_key(pub_key),
        })

        # Expiry finding
        if expiry_warning:
            findings.append({
                "severity": "WARNING" if days_until_expiry > 30 else "HIGH",
                "category": "CERTIFICATE_EXPIRY",
                "title": f"Certificate Expiring in {days_until_expiry} Days ({cert_label})",
                "description": (
                    f"The certificate for '{subject_str}' expires on {expires_at.strftime('%Y-%m-%d')} "
                    f"({days_until_expiry} days remaining). Renew before migration."
                ),
                "affected_asset": subject_str,
                "nist_reference": "NIST SP 800-57 Part 1 Rev 5 — Crypto period management",
                "remediation": "Renew certificate and consider deploying PQC-capable certificate upon renewal.",
            })

        # SAN mismatch finding (leaf only)
        if idx == 0 and san_covers_domain is False:
            findings.append({
                "severity": "WARNING",
                "category": "CERTIFICATE_SAN",
                "title": f"Domain '{domain}' Not Covered by Certificate SAN",
                "description": (
                    f"The leaf certificate's Subject Alternative Names {san_domains} "
                    f"do not cover the scanned domain '{domain}'."
                ),
                "affected_asset": subject_str,
                "nist_reference": "RFC 6125 — Representation and Verification of Domain-Based Application Service Identity",
                "remediation": "Ensure the certificate SAN includes the target domain.",
            })

    # ── Cipher / KEX Finding ──────────────────────────────────────────
    risk_points += cipher_analysis["risk_points"]

    findings.append({
        "severity": "CRITICAL" if cipher_analysis["cipher_risk"] == "VULNERABLE" else (
            "COMPLIANT" if cipher_analysis["cipher_risk"] == "COMPLIANT" else "MEDIUM"
        ),
        "category": "KEY_EXCHANGE",
        "title": (
            f"{'Quantum-Vulnerable' if not cipher_analysis['cipher_quantum_safe'] else 'PQC-Compliant'} "
            f"Key Exchange: {cipher_name}"
        ),
        "description": cipher_analysis["cipher_reason"],
        "affected_asset": f"TLS session to {host}:{port}",
        "nist_reference": NIST_REFERENCES.get("KEX", ""),
        "remediation": (
            "Deploy ML-KEM-768 (FIPS 203) hybrid key exchange (e.g. X25519MLKEM768) "
            "on the server. Requires TLS 1.3 and updated TLS library (e.g. OpenSSL 3.5+)."
            if not cipher_analysis["cipher_quantum_safe"]
            else "No action required — PQC hybrid key exchange is deployed."
        ),
    })

    # ── TLS Version Finding ───────────────────────────────────────────
    risk_points += tls_meta["points"]

    if tls_meta["risk"] in ("CRITICAL", "WARNING"):
        findings.append({
            "severity": tls_meta["risk"],
            "category": "TLS_VERSION",
            "title": f"TLS Version {tls_meta['label']} Detected",
            "description": (
                f"The server negotiated {tls_meta['label']}. "
                + ("This version is deprecated and insecure. " if tls_meta["risk"] == "CRITICAL" else "")
                + "TLS 1.3 is required for PQC hybrid key exchange support."
            ),
            "affected_asset": f"TLS session to {host}:{port}",
            "nist_reference": NIST_REFERENCES["TLS_OLD"],
            "remediation": (
                "Upgrade to TLS 1.3 to enable PQC hybrid cipher suites. "
                "Disable TLS 1.0 and 1.1 immediately."
            ),
        })

    # ── Clamp & Finalize Score ────────────────────────────────────────
    risk_points = round(max(0.0, min(100.0, risk_points)), 1)
    risk_level = _compute_risk_level(risk_points)

    # Sort findings by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "WARNING": 3, "LOW": 4, "COMPLIANT": 5}
    findings.sort(key=lambda f: severity_order.get(f["severity"], 99))

    report: dict[str, Any] = {
        "domain": domain,
        "scan_timestamp": scan_start.isoformat(),
        "scan_duration_ms": int((datetime.now(timezone.utc) - scan_start).total_seconds() * 1000),
        "overall_risk_score": risk_points,
        "risk_level": risk_level,
        "tls_version": tls_meta["label"],
        "tls_version_risk": tls_meta["risk"],
        "cipher_suite": cipher_name,
        "cipher_bits": cipher_bits,
        "cipher_quantum_safe": cipher_analysis["cipher_quantum_safe"],
        "certificates": cert_results,
        "findings": findings,
        "cbom_summary": {
            "total_assets": total_assets,
            "vulnerable_assets": vulnerable_assets,
            "compliant_assets": compliant_assets,
            "pqc_readiness_pct": round(
                (compliant_assets / total_assets * 100) if total_assets > 0 else 0, 1
            ),
        },
        "compliance_frameworks": {
            "nist_pqc_migration": "https://csrc.nist.gov/projects/post-quantum-cryptography",
            "cnsa_2_0": "https://media.defense.gov/2022/Sep/07/2003071834/-1/-1/0/CSA_CNSA_2.0_ALGORITHMS_.PDF",
            "fips_203_ml_kem": "https://csrc.nist.gov/pubs/fips/203/final",
            "fips_204_ml_dsa": "https://csrc.nist.gov/pubs/fips/204/final",
            "fips_205_slh_dsa": "https://csrc.nist.gov/pubs/fips/205/final",
        },
    }

    logger.info(
        "PQC scan completed for %s — risk=%d (%s), certs=%d, findings=%d",
        domain, risk_points, risk_level, len(cert_results), len(findings),
    )

    return report


# ---------------------------------------------------------------------------
# Public API — Async wrapper
# ---------------------------------------------------------------------------

async def scan_domain_async(domain: str, port: Optional[int] = None) -> dict[str, Any]:
    """
    Async wrapper around :func:`scan_domain`.

    Runs the blocking TLS scan in a thread pool executor via
    ``asyncio.to_thread`` so it can be called from async FastAPI
    route handlers without blocking the event loop.

    Parameters
    ----------
    domain : str
        Target domain — same semantics as :func:`scan_domain`.
    port : int, optional
        Optional custom port to scan.

    Returns
    -------
    dict
        Identical output to :func:`scan_domain`.
    """
    return await asyncio.to_thread(scan_domain, domain, port)


# ---------------------------------------------------------------------------
# Private helpers (finding generation)
# ---------------------------------------------------------------------------

def _key_family(pub_key: Any) -> str:
    """Return a simplified key family string for NIST reference lookup."""
    if isinstance(pub_key, rsa.RSAPublicKey):
        return "RSA"
    elif isinstance(pub_key, ec.EllipticCurvePublicKey):
        return "ECC"
    elif isinstance(pub_key, dsa.DSAPublicKey):
        return "DSA"
    elif isinstance(pub_key, (ed25519.Ed25519PublicKey, ed448.Ed448PublicKey)):
        return "EdDSA"
    return "UNKNOWN"


def _remediation_for_key(pub_key: Any) -> str:
    """Return actionable remediation guidance for a given key type."""
    if isinstance(pub_key, rsa.RSAPublicKey):
        return (
            "Replace RSA certificates with ML-DSA-65 (FIPS 204) for digital signatures. "
            "For key exchange, deploy ML-KEM-768 (FIPS 203). "
            "Target migration completion by 2030 per CNSA 2.0 timeline."
        )
    elif isinstance(pub_key, ec.EllipticCurvePublicKey):
        return (
            "Replace ECDSA certificates with ML-DSA-65 (FIPS 204) for signatures. "
            "Replace ECDH key exchange with ML-KEM-768 (FIPS 203). "
            "ECC provides zero quantum resistance — prioritize migration."
        )
    elif isinstance(pub_key, dsa.DSAPublicKey):
        return (
            "DSA is deprecated by NIST and quantum-vulnerable. "
            "Immediately replace with ML-DSA-65 (FIPS 204) for signatures."
        )
    elif isinstance(pub_key, (ed25519.Ed25519PublicKey, ed448.Ed448PublicKey)):
        return (
            "Monitor NIST guidance on EdDSA quantum safety. "
            "Consider proactive migration to SLH-DSA (FIPS 205) for hash-based signatures "
            "or ML-DSA-65 (FIPS 204) as a lattice-based alternative."
        )
    return "Consult NIST PQC migration guidance for this key type."


def _error_result(
    domain: str,
    scan_start: datetime,
    error_code: str,
    error_message: str,
) -> dict[str, Any]:
    """Build a standardized error result when scanning cannot complete."""
    return {
        "domain": domain,
        "scan_timestamp": scan_start.isoformat(),
        "scan_duration_ms": int((datetime.now(timezone.utc) - scan_start).total_seconds() * 1000),
        "overall_risk_score": None,
        "risk_level": None,
        "error": {
            "code": error_code,
            "message": error_message,
        },
        "tls_version": None,
        "cipher_suite": None,
        "cipher_quantum_safe": None,
        "certificates": [],
        "findings": [],
        "cbom_summary": {
            "total_assets": 0,
            "vulnerable_assets": 0,
            "compliant_assets": 0,
            "pqc_readiness_pct": 0.0,
        },
    }


# ---------------------------------------------------------------------------
# CLI Entrypoint (for standalone testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "google.com"
    print(f"\n{'=' * 72}")
    print(f"  QuantCAI PQC Scanner -- Scanning: {target}")
    print(f"{'=' * 72}\n")

    result = scan_domain(target)
    print(json.dumps(result, indent=2, default=str))

    if result.get("error"):
        print(f"\n[!] Scan encountered an error: {result['error']['message']}")
        sys.exit(1)

    print(f"\n{'-' * 72}")
    print(f"  Risk Score : {result['overall_risk_score']}/100  [{result['risk_level']}]")
    print(f"  TLS        : {result['tls_version']}")
    print(f"  Cipher     : {result['cipher_suite']} "
          f"({'PQC OK' if result['cipher_quantum_safe'] else 'Quantum-Vulnerable'})")
    print(f"  Certs      : {result['cbom_summary']['total_assets']} total, "
          f"{result['cbom_summary']['vulnerable_assets']} vulnerable")
    print(f"{'-' * 72}")

    severity_icons = {
        "CRITICAL": "[!!]", "HIGH": "[!]", "MEDIUM": "[~]",
        "WARNING": "[~]", "LOW": "[.]", "COMPLIANT": "[OK]",
    }
    for f in result["findings"]:
        icon = severity_icons.get(f["severity"], "[?]")
        print(f"  {icon} [{f['severity']}] {f['title']}")
    print()


def generate_cyclonedx_cbom(scan_result: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a machine-readable CycloneDX 1.6 compliant Cryptographic Bill of Materials (CBOM)
    from a standard scan result.
    """
    timestamp = scan_result.get("scan_timestamp") or datetime.now(timezone.utc).isoformat()
    domain = scan_result.get("domain") or "unknown"
    
    components = []
    dependencies = []
    
    # 1. Add Protocol (TLS) component
    tls_version = scan_result.get("tls_version") or "TLSv1.3"
    cipher_suite = scan_result.get("cipher_suite") or "UNKNOWN"
    
    protocol_properties = ProtocolProperties(
        type="tls",
        version=tls_version.replace("TLSv", "").replace("TLS ", ""),
        cipherSuites=[
            CipherSuiteAlgorithm(
                name=cipher_suite,
                algorithms=[]  # Filled in below based on certificates
            )
        ]
    )
    
    protocol_component = Component(
        bom_ref="crypto/protocol/tls",
        type="cryptographic-asset",
        name=tls_version,
        description=f"TLS Session configured for {domain}",
        cryptoProperties=CryptoProperties(
            assetType="protocol",
            protocolProperties=protocol_properties
        )
    )
    components.append(protocol_component)
    
    # 2. Add Certificates and Algorithms
    depends_on = []
    for idx, cert in enumerate(scan_result.get("certificates", [])):
        cert_ref = f"crypto/certificate/cert-{idx}"
        depends_on.append(cert_ref)
        
        # Extract metadata
        expires_at = cert.get("expires_at")
        subject = cert.get("subject")
        issuer = cert.get("issuer")
        sig_algo = cert.get("signature_algorithm") or "sha256WithRSAEncryption"
        
        cert_properties = CertificateProperties(
            subjectName=subject,
            issuerName=issuer,
            validTo=expires_at,
            signatureAlgorithm=sig_algo
        )
        
        cert_component = Component(
            bom_ref=cert_ref,
            type="cryptographic-asset",
            name=f"Certificate {idx}: {subject.split('commonName=')[-1].split(',')[0] if 'commonName=' in subject else subject}",
            description=f"Certificate in the chain of {domain}",
            cryptoProperties=CryptoProperties(
                assetType="certificate",
                certificateProperties=cert_properties
            )
        )
        components.append(cert_component)
        
        # Add the algorithm of the certificate
        algo_name = cert.get("algorithm") or "UNKNOWN"
        algo_ref = f"crypto/algorithm/{algo_name.lower().replace('-', '').replace('_', '')}"
        
        # Parse algorithm details
        primitive = "signature"
        curve = None
        key_len = None
        
        if "rsa" in algo_name.lower():
            primitive = "signature"
            try:
                key_len = int(algo_name.split("-")[-1])
            except Exception:
                key_len = 2048
        elif "ecc" in algo_name.lower() or "ecdsa" in algo_name.lower():
            primitive = "signature"
            # e.g., ECC-secp256r1-256
            parts = algo_name.split("-")
            if len(parts) >= 2:
                curve = parts[1]
            try:
                key_len = int(parts[-1])
            except Exception:
                key_len = 256
                
        algo_properties = AlgorithmProperties(
            primitive=primitive,
            parameterSetIdentifier=algo_name.lower(),
            curve=curve,
            keyLength=key_len
        )
        
        algo_component = Component(
            bom_ref=algo_ref,
            type="cryptographic-asset",
            name=algo_name,
            description=f"Cryptographic algorithm used by certificate {idx}",
            cryptoProperties=CryptoProperties(
                assetType="algorithm",
                algorithmProperties=algo_properties
            )
        )
        components.append(algo_component)
        
        # Link certificate to its signature algorithm
        dependencies.append(Dependency(
            ref=cert_ref,
            dependsOn=[algo_ref]
        ))
        
        # Link algorithm used to the protocol list
        if protocol_properties.cipherSuites:
            protocol_properties.cipherSuites[0].algorithms.append(algo_ref)
            
    # Add dependency link for protocol pointing to all certs in chain
    dependencies.append(Dependency(
        ref="crypto/protocol/tls",
        dependsOn=depends_on
    ))
    
    # Construct CBOM
    cbom = CycloneDXCBOM(
        serialNumber=f"urn:uuid:{uuid.uuid4()}",
        version=1,
        metadata=Metadata(timestamp=timestamp),
        components=components,
        dependencies=dependencies
    )
    
    try:
        return cbom.model_dump(by_alias=True)
    except AttributeError:
        # Pydantic v1 fallback
        return cbom.dict(by_alias=True)

