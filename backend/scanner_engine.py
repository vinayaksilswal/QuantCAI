import socket
import ssl
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import ipaddress

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import (
    dsa,
    ec,
    ed448,
    ed25519,
    rsa,
)
from cryptography.x509.oid import ExtensionOID

logger = logging.getLogger("quantcai.scanner_engine")

# ---------------------------------------------------------------------------
# SSRF Prevention — IP Blocklist (Security: Finding #2)
# ---------------------------------------------------------------------------
# These ranges must NEVER be scanned. Prevents DNS rebinding, SSRF to cloud
# metadata services (AWS IMDS, GCP metadata), and internal network probing.
_BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),         # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),      # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),     # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / AWS IMDS
    ipaddress.ip_network("100.64.0.0/10"),      # Carrier-grade NAT
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
    ipaddress.ip_network("fc00::/7"),           # IPv6 unique local
]

_BLOCKED_HOSTNAMES = frozenset({
    "localhost",
    "metadata.google.internal",
    "metadata",
    "169.254.169.254",
})

def validate_scan_target(domain: str, port: int) -> str:
    """
    Resolves the domain to an IP address and validates it is not in any
    blocked range. Returns the resolved IP string for connection.

    This function eliminates the DNS-rebinding TOCTOU by resolving ONCE
    and using the validated IP for the actual socket connection.

    Raises:
        ValueError: If the target resolves to a blocked IP or hostname.
    """
    domain_clean = domain.strip().lower()

    # Strip protocol prefixes
    for prefix in ("https://", "http://"):
        if domain_clean.startswith(prefix):
            domain_clean = domain_clean[len(prefix):]
    domain_clean = domain_clean.split("/")[0].split(":")[0]

    # Block known internal hostnames
    if domain_clean in _BLOCKED_HOSTNAMES:
        raise ValueError(f"Scanning internal hostname '{domain_clean}' is not permitted")
    if domain_clean.endswith((".local", ".lan", ".internal")):
        raise ValueError(f"Scanning internal hostname '{domain_clean}' is not permitted")

    # Resolve ALL addresses (prevents rebinding via round-robin)
    try:
        addr_infos = socket.getaddrinfo(domain_clean, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise ValueError(f"DNS resolution failed for '{domain_clean}': {e}")

    if not addr_infos:
        raise ValueError(f"No DNS records found for '{domain_clean}'")

    # Validate EVERY resolved IP against the blocklist
    resolved_ip = addr_infos[0][4][0]
    for addr_info in addr_infos:
        ip_str = addr_info[4][0]
        ip = ipaddress.ip_address(ip_str)
        for blocked in _BLOCKED_IP_RANGES:
            if ip in blocked:
                raise ValueError(
                    f"Target '{domain_clean}' resolves to blocked IP {ip_str} "
                    f"(range: {blocked}). Internal/cloud metadata scanning is prohibited."
                )

    return resolved_ip


# Hybrid/PQC keywords to recognize quantum-resistant key exchanges
PQC_HYBRID_KEYWORDS = {
    "mlkem",
    "mlkem768",
    "mlkem1024",
    "kyber",
    "x25519mlkem768",
    "x25519_mlkem768",
    "secp256r1mlkem768",
    "x25519kyber768",
    "x25519kyber768draft00",
}

def analyze_key_exchange(cipher_name: str, tls_version: str) -> Dict[str, Any]:
    """
    Analyzes the key exchange mechanism for a given cipher suite and TLS version.
    """
    cipher_upper = cipher_name.upper().replace("-", "_")
    cipher_lower = cipher_name.lower().replace("-", "").replace("_", "")
    
    # 1. Check for known post-quantum/hybrid key exchange
    is_pqc = any(kw in cipher_lower for kw in PQC_HYBRID_KEYWORDS)
    if is_pqc:
        kex_name = "X25519 + ML-KEM-768 (Hybrid)" if "768" in cipher_lower else "Hybrid PQC (ML-KEM)"
        return {
            "key_exchange": kex_name,
            "key_exchange_group": "x25519_mlkem768" if "768" in cipher_lower else "ml_kem",
            "key_exchange_bits": 384, # estimate representation for hybrid
            "quantum_safe": True,
            "reason": f"Uses a PQC hybrid key exchange ({cipher_name}) which protects against Shor's algorithm.",
            "risk_points": -20.0
        }
        
    # 2. Check for classical vulnerable key exchanges
    vulnerable_kex = None
    kex_bits = None
    kex_group = None
    
    if "ECDHE" in cipher_upper:
        vulnerable_kex = "ECDHE"
        kex_bits = 256
        kex_group = "ECDH (secp256r1/X25519)"
    elif "DHE" in cipher_upper:
        vulnerable_kex = "DHE"
        kex_bits = 2048
        kex_group = "DH (finite field)"
    elif "ECDH" in cipher_upper:
        vulnerable_kex = "ECDH"
        kex_bits = 256
        kex_group = "Static ECDH"
    elif "DH" in cipher_upper:
        vulnerable_kex = "DH"
        kex_bits = 2048
        kex_group = "Static DH"
        
    if vulnerable_kex:
        return {
            "key_exchange": vulnerable_kex,
            "key_exchange_group": kex_group,
            "key_exchange_bits": kex_bits,
            "quantum_safe": False,
            "reason": f"Negotiated {vulnerable_kex} key exchange which is completely vulnerable to Shor's algorithm on a CRQC.",
            "risk_points": 15.0
        }
        
    # 3. For TLS 1.3, key exchange is negotiate via ephemeral keys, but names don't contain ECDHE (e.g. TLS_AES_256_GCM_SHA384)
    if tls_version == "TLS 1.3" or tls_version == "TLSv1.3":
        return {
            "key_exchange": "ECDHE (assumed)",
            "key_exchange_group": "X25519 or secp256r1",
            "key_exchange_bits": 256,
            "quantum_safe": False,
            "reason": "TLS 1.3 session negotiated standard classical ECDHE. Highly vulnerable to Harvest Now, Decrypt Later (HNDL).",
            "risk_points": 15.0
        }
        
    # 4. Fallback/Unknown
    return {
        "key_exchange": "Unknown",
        "key_exchange_group": "Unknown",
        "key_exchange_bits": None,
        "quantum_safe": False,
        "reason": f"Could not determine key exchange for cipher {cipher_name}. Assumed vulnerable.",
        "risk_points": 20.0
    }

def classify_certificate_key(public_key: Any) -> Dict[str, Any]:
    """
    Classifies the public key of a certificate and returns its quantum-safety characteristics.
    """
    if isinstance(public_key, rsa.RSAPublicKey):
        key_size = public_key.key_size
        algo_label = f"RSA-{key_size}"
        
        if key_size <= 2048:
            return {
                "algorithm": algo_label,
                "quantum_vulnerable": True,
                "reason": f"RSA-{key_size} is a legacy key size vulnerable to Shor's algorithm. Must migrate to ML-DSA (FIPS 204) by 2030.",
                "severity": "CRITICAL",
                "risk_points": 35.0
            }
        else:
            return {
                "algorithm": algo_label,
                "quantum_vulnerable": True,
                "reason": f"RSA-{key_size} is quantum-vulnerable. Increased key sizes do not protect against Shor's algorithm.",
                "severity": "HIGH",
                "risk_points": 25.0
            }
            
    elif isinstance(public_key, ec.EllipticCurvePublicKey):
        curve_name = public_key.curve.name
        key_size = public_key.key_size
        algo_label = f"ECC-{curve_name}-{key_size}"
        is_legacy = key_size == 256 or curve_name in ("secp256r1", "prime256v1")
        
        return {
            "algorithm": algo_label,
            "quantum_vulnerable": True,
            "reason": f"Elliptic Curve cryptography ({curve_name}) is completely broken by Shor's algorithm. Must migrate to ML-DSA.",
            "severity": "CRITICAL" if is_legacy else "HIGH",
            "risk_points": 30.0
        }
        
    elif isinstance(public_key, dsa.DSAPublicKey):
        return {
            "algorithm": f"DSA-{public_key.key_size}",
            "quantum_vulnerable": True,
            "reason": "DSA is deprecated and relies on discrete logarithms, which are trivially broken by Shor's algorithm.",
            "severity": "CRITICAL",
            "risk_points": 35.0
        }
        
    elif hasattr(public_key, "__class__") and public_key.__class__.__name__ in ("Ed25519PublicKey", "Ed448PublicKey"):
        algo_label = public_key.__class__.__name__.replace("PublicKey", "")
        return {
            "algorithm": algo_label,
            "quantum_vulnerable": None, # Uncertain
            "reason": f"{algo_label} is based on elliptic curves and is quantum-vulnerable, but research into hash-based signatures is ongoing.",
            "severity": "MEDIUM",
            "risk_points": 10.0
        }
        
    else:
        algo_label = type(public_key).__name__
        return {
            "algorithm": algo_label,
            "quantum_vulnerable": None,
            "reason": f"Unknown public key algorithm: {algo_label}. Needs manual audit.",
            "severity": "MEDIUM",
            "risk_points": 20.0
        }

def scan_tls_pqc(domain: str, port: int = 443) -> Dict[str, Any]:
    """
    Executes a PQC scanner audit against the target domain and port.
    Returns a dictionary structured to match the ScanResponse schema.
    """
    scan_start = datetime.now(timezone.utc)
    domain_clean = domain.strip().lower()
    
    # Clean up domain format
    if domain_clean.startswith("https://"):
        domain_clean = domain_clean[8:]
    elif domain_clean.startswith("http://"):
        domain_clean = domain_clean[7:]
    if "/" in domain_clean:
        domain_clean = domain_clean.split("/")[0]
    if ":" in domain_clean:
        domain_clean = domain_clean.split(":")[0]
        
    logger.info(f"Initiating PQC TLS audit for target {domain_clean}:{port}")
    
    # 1. SSRF validation — resolve and validate BEFORE connecting (Finding #2)
    try:
        resolved_ip = validate_scan_target(domain_clean, port)
        logger.info(f"SSRF check passed: {domain_clean} -> {resolved_ip}")
    except ValueError as ssrf_err:
        logger.warning(f"SSRF blocked for {domain_clean}:{port}: {ssrf_err}")
        raise ConnectionError(f"Scan target rejected: {ssrf_err}")

    # 2. Establish socket and perform SSL handshake using validated IP
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED

        # Connect to the pre-validated IP (not re-resolving the domain)
        with socket.create_connection((resolved_ip, port), timeout=5) as raw_sock:
            # Explicitly pass the original domain string for SNI to prevent Host Mismatch (Security: Finding #2)
            with ctx.wrap_socket(raw_sock, server_hostname=domain) as ssock:
                cipher_info = ssock.cipher() # (name, version, bits)
                tls_version_raw = ssock.version()
                
                # Fetch certificates
                der_chain = ssock.getpeercert(binary_form=True)
                
                # Attempt full chain resolution via private API if verified chain exists
                chain_ders = []
                try:
                    raw_chain = ssock._sslobj.get_verified_chain()
                    if raw_chain:
                        chain_ders = [c.public_bytes(ssl._ssl.ENCODING_DER) for c in raw_chain]
                except Exception:
                    pass
                    
                if not chain_ders:
                    if isinstance(der_chain, bytes):
                        chain_ders = [der_chain]
                    elif isinstance(der_chain, (list, tuple)):
                        chain_ders = list(der_chain)
                    else:
                        chain_ders = [ssock.getpeercert(binary_form=True)]
                        
    except Exception as e:
        logger.error(f"Failed connection to {domain_clean}:{port}: {e}")
        # Build standard error mock assessment to not fail the flow
        raise ConnectionError(f"TLS handshake failed: {str(e)}")

    # 2. Extract configuration values
    cipher_suite = cipher_info[0] if cipher_info else "UNKNOWN"
    tls_version = tls_version_raw or "TLSv1.3"
    
    # Format version string
    tls_version_str = tls_version.replace("TLSv", "TLS ")
    
    # Analyze KEX
    kex_analysis = analyze_key_exchange(cipher_suite, tls_version_str)
    
    tls_details = {
        "version": tls_version_str,
        "cipher_suite": cipher_suite,
        "key_exchange": kex_analysis["key_exchange"],
        "key_exchange_group": kex_analysis["key_exchange_group"],
        "key_exchange_bits": kex_analysis["key_exchange_bits"],
        "quantum_safe": kex_analysis["quantum_safe"]
    }
    
    # 3. Analyze Certificate Chain
    certificates = []
    findings = []
    total_assets = 0
    vulnerable_assets = 0
    compliant_assets = 0
    
    risk_points = 0.0
    # Add key exchange risk points
    risk_points += kex_analysis["risk_points"]
    
    # Add TLS version risk points
    if "1.3" in tls_version_str:
        pass # compliant
    elif "1.2" in tls_version_str:
        risk_points += 5.0
        findings.append({
            "severity": "WARNING",
            "category": "TLS_VERSION",
            "title": "TLS Version 1.2 Detected",
            "description": "TLS 1.2 is currently active. While classically secure, it does not natively support modern PQC hybrid key exchanges without non-standard extensions. Upgrade to TLS 1.3.",
            "affected_asset": "TLS session protocol",
            "remediation": "Upgrade server TLS stack to support TLS 1.3 only, disabling older TLS protocols.",
            "nist_reference": "NIST SP 800-52 Rev 2"
        })
    else:
        risk_points += 20.0
        findings.append({
            "severity": "CRITICAL",
            "category": "TLS_VERSION",
            "title": f"Deprecated TLS Version ({tls_version_str})",
            "description": "Legacy TLS version is active. Legacy versions lack crucial cryptographic controls and do not support quantum-safe migration paths.",
            "affected_asset": "TLS session protocol",
            "remediation": "Disable legacy TLS versions (1.0, 1.1) immediately, enforcing TLS 1.2 and 1.3.",
            "nist_reference": "NIST SP 800-52 Rev 2"
        })

    for idx, der in enumerate(chain_ders):
        total_assets += 1
        try:
            cert = x509.load_der_x509_certificate(der)
            
            # Form subjects
            subject = ", ".join(f"{attr.oid._name or attr.oid.dotted_string}={attr.value}" for attr in cert.subject)
            issuer = ", ".join(f"{attr.oid._name or attr.oid.dotted_string}={attr.value}" for attr in cert.issuer)
            
            # Key classification
            pub_key = cert.public_key()
            key_classification = classify_certificate_key(pub_key)
            
            # Expiry date
            try:
                expires_at = cert.not_valid_after_utc
            except AttributeError:
                expires_at = cert.not_valid_after.replace(tzinfo=timezone.utc)
                
            days_until_expiry = (expires_at - datetime.now(timezone.utc)).days
            expiry_warning = days_until_expiry < 90
            
            # 2030 threshold check
            extends_past_2030 = expires_at.year >= 2030
            
            # Signature algorithm
            sig_algo = cert.signature_algorithm_oid._name or cert.signature_algorithm_oid.dotted_string
            
            is_vuln = key_classification["quantum_vulnerable"]
            if is_vuln is True:
                vulnerable_assets += 1
                risk_points += key_classification["risk_points"]
            elif is_vuln is False:
                compliant_assets += 1
            else:
                vulnerable_assets += 1 # assume vulnerable if uncertain
                risk_points += key_classification["risk_points"]
                
            severity = key_classification["severity"]
            if extends_past_2030 and is_vuln is not False:
                severity = "CRITICAL"
                
            certificates.append({
                "index": idx,
                "subject": subject,
                "issuer": issuer,
                "serial_number": str(cert.serial_number),
                "algorithm": key_classification["algorithm"],
                "signature_algorithm": sig_algo,
                "quantum_vulnerable": is_vuln,
                "severity": severity,
                "expires_at": expires_at.strftime("%Y-%m-%d"),
                "days_until_expiry": days_until_expiry,
                "expiry_warning": expiry_warning,
                "extends_past_2030": extends_past_2030
            })
            
            # Add certificate key finding
            asset_label = "Leaf Certificate" if idx == 0 else f"Intermediate CA Certificate #{idx}"
            findings.append({
                "severity": severity,
                "category": "CERTIFICATE_KEY",
                "title": f"Quantum-Vulnerable {key_classification['algorithm']} Key ({asset_label})",
                "description": key_classification["reason"] + (" Furthermore, this certificate extends past the 2030 quantum-readiness deadline." if extends_past_2030 else ""),
                "affected_asset": subject,
                "remediation": "Migrate to ML-DSA-65 (FIPS 204) for digital signatures during your next renewal cycle.",
                "nist_reference": "NIST SP 800-131A Rev 2 & FIPS 204"
            })
            
            if expiry_warning:
                findings.append({
                    "severity": "WARNING" if days_until_expiry > 30 else "HIGH",
                    "category": "CERTIFICATE_EXPIRY",
                    "title": f"Certificate Expiring Soon ({asset_label})",
                    "description": f"The certificate expires in {days_until_expiry} days on {expires_at.strftime('%Y-%m-%d')}.",
                    "affected_asset": subject,
                    "remediation": "Renew the certificate, preferably migrating to PQC-compliant options if supported by your CA.",
                    "nist_reference": "NIST SP 800-57 Part 1"
                })
                
        except Exception as cert_err:
            logger.error(f"Error parsing cert index {idx}: {cert_err}")
            vulnerable_assets += 1
            certificates.append({
                "index": idx,
                "subject": f"Unknown CN (failed parse: {cert_err})",
                "issuer": "Unknown Issuer",
                "serial_number": "0",
                "algorithm": "Unknown",
                "signature_algorithm": "Unknown",
                "quantum_vulnerable": True,
                "severity": "HIGH",
                "expires_at": "1970-01-01",
                "days_until_expiry": 0,
                "expiry_warning": True,
                "extends_past_2030": False
            })

    # Add general key exchange finding if vulnerable
    if not kex_analysis["quantum_safe"]:
        findings.append({
            "severity": "CRITICAL",
            "category": "KEY_EXCHANGE",
            "title": f"Quantum-Vulnerable Key Exchange ({kex_details_name(kex_analysis['key_exchange'])})",
            "description": kex_analysis["reason"],
            "affected_asset": f"TLS session to {domain_clean}:{port}",
            "remediation": "Configure the TLS server to use a hybrid quantum-safe key exchange mechanism such as X25519MLKEM768 or secp256r1MLKEM768.",
            "nist_reference": "NIST FIPS 203 (ML-KEM) & CNSA 2.0 Timeline"
        })

    # Compute overall risk score and grade
    clamped_score = round(max(0.0, min(100.0, risk_points)), 1)
    
    # Risk Level mapping
    if clamped_score >= 80.0:
        overall_risk = "CRITICAL"
    elif clamped_score >= 60.0:
        overall_risk = "HIGH"
    elif clamped_score >= 40.0:
        overall_risk = "MEDIUM"
    elif clamped_score >= 20.0:
        overall_risk = "LOW"
    else:
        overall_risk = "COMPLIANT"

    # Harvest Now, Decrypt Later (HNDL) risk level - completely relies on Key Exchange safety
    if not kex_analysis["quantum_safe"]:
        hndl_risk = "CRITICAL" # CRITICAL because classical ECDHE/DHE traffic can be decrypted later
    else:
        hndl_risk = "COMPLIANT"

    # Quantum Risk Grade mapping
    if clamped_score < 10.0:
        grade = "Grade A"
    elif clamped_score < 30.0:
        grade = "Grade B"
    elif clamped_score < 50.0:
        grade = "Grade C"
    elif clamped_score < 75.0:
        grade = "Grade D"
    else:
        grade = "Grade F"

    # CBOM stats
    pqc_readiness = round((compliant_assets / total_assets * 100.0) if total_assets > 0 else 0.0, 1)
    cbom_summary = {
        "total_assets": total_assets,
        "vulnerable_assets": vulnerable_assets,
        "compliant_assets": compliant_assets,
        "pqc_readiness_pct": pqc_readiness
    }
    
    # Sort findings by severity order
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "WARNING": 3, "LOW": 4, "COMPLIANT": 5}
    findings.sort(key=lambda f: severity_order.get(f["severity"], 99))
    
    scan_duration = int((datetime.now(timezone.utc) - scan_start).total_seconds() * 1000)
    
    return {
        "domain": domain_clean,
        "port": port,
        "scan_timestamp": scan_start.isoformat(),
        "scan_duration_ms": scan_duration,
        "overall_risk_score": clamped_score,
        "risk_level": overall_risk,
        "hndl_risk_level": hndl_risk,
        "quantum_risk_grade": grade,
        "tls_details": tls_details,
        "certificates": certificates,
        "findings": findings,
        "cbom_summary": cbom_summary
    }

def kex_details_name(kex: str) -> str:
    if kex == "ECDHE":
        return "ECDHE"
    if kex == "DHE":
        return "DHE"
    return kex
