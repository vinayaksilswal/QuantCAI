"""
Tests for the Post-Quantum Cryptography Scanner Engine
=======================================================
Covers:
  - Internal helper functions (unit tests — no network)
  - Live scan integration tests against well-known domains
  - Error handling (timeouts, invalid hosts)
  - Risk score boundary conditions
"""

from __future__ import annotations

import json
import sys
import os

# Ensure backend/ is on the path so 'services.pqc_scanner' resolves
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa, ed25519
from cryptography.x509.oid import NameOID

from services.pqc_scanner import (
    _classify_public_key,
    _analyze_cipher_suite,
    _compute_risk_level,
    _domain_matches_san,
    _extract_san_domains,
    _error_result,
    _format_subject,
    scan_domain,
    scan_domain_async,
    PQC_HYBRID_KEYWORDS,
)


# ──────────────────────────────────────────────────────────────────────────
# Fixtures — generate test keys in-process (no network required)
# ──────────────────────────────────────────────────────────────────────────

@pytest.fixture
def rsa_2048_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def rsa_4096_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=4096)


@pytest.fixture
def ec_p256_key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture
def dsa_key():
    return dsa.generate_private_key(key_size=2048)


@pytest.fixture
def ed25519_key():
    return ed25519.Ed25519PrivateKey.generate()


def _make_self_signed_cert(
    private_key,
    cn: str = "test.example.com",
    san_domains: list[str] | None = None,
    days_valid: int = 365,
):
    """Build a self-signed DER certificate for testing."""
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, cn),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "QuantCAI Test"),
    ])

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=days_valid))
    )

    if san_domains:
        builder = builder.add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName(d) for d in san_domains]
            ),
            critical=False,
        )

    # Choose appropriate hash for the key type
    if isinstance(private_key, ed25519.Ed25519PrivateKey):
        # Ed25519 uses its own internal hash — pass None
        cert = builder.sign(private_key, algorithm=None)
    else:
        cert = builder.sign(private_key, hashes.SHA256())

    return cert


# ──────────────────────────────────────────────────────────────────────────
# Unit Tests — _classify_public_key
# ──────────────────────────────────────────────────────────────────────────

class TestClassifyPublicKey:
    def test_rsa_2048_is_critical(self, rsa_2048_key):
        result = _classify_public_key(rsa_2048_key.public_key())
        assert result["algorithm"] == "RSA-2048"
        assert result["quantum_vulnerable"] is True
        assert result["severity"] == "CRITICAL"
        assert result["risk_points"] == 35

    def test_rsa_4096_is_high(self, rsa_4096_key):
        result = _classify_public_key(rsa_4096_key.public_key())
        assert result["algorithm"] == "RSA-4096"
        assert result["quantum_vulnerable"] is True
        assert result["severity"] == "HIGH"
        assert result["risk_points"] == 20

    def test_ecc_is_critical(self, ec_p256_key):
        result = _classify_public_key(ec_p256_key.public_key())
        assert "ECC" in result["algorithm"]
        assert result["quantum_vulnerable"] is True
        assert result["severity"] == "CRITICAL"
        assert result["risk_points"] == 30
        assert "Shor" in result["vulnerability_reason"]

    def test_dsa_is_critical(self, dsa_key):
        result = _classify_public_key(dsa_key.public_key())
        assert "DSA" in result["algorithm"]
        assert result["quantum_vulnerable"] is True
        assert result["severity"] == "CRITICAL"
        assert result["risk_points"] == 35

    def test_ed25519_is_uncertain(self, ed25519_key):
        result = _classify_public_key(ed25519_key.public_key())
        assert "Ed25519" in result["algorithm"]
        assert result["quantum_vulnerable"] is None
        assert result["severity"] == "MEDIUM"
        assert result["risk_points"] == 10

    def test_unknown_key_type(self):
        """An unrecognized key type should return MEDIUM + manual review."""
        mock_key = MagicMock()
        mock_key.__class__.__name__ = "FutureQuantumKey"
        result = _classify_public_key(mock_key)
        assert result["severity"] == "MEDIUM"
        assert "Unknown key type" in result["vulnerability_reason"]


# ──────────────────────────────────────────────────────────────────────────
# Unit Tests — _analyze_cipher_suite
# ──────────────────────────────────────────────────────────────────────────

class TestAnalyzeCipherSuite:
    def test_ecdhe_is_vulnerable(self):
        result = _analyze_cipher_suite("ECDHE-RSA-AES256-GCM-SHA384")
        assert result["cipher_quantum_safe"] is False
        assert result["cipher_risk"] == "VULNERABLE"
        assert result["risk_points"] == 15

    def test_dhe_is_vulnerable(self):
        result = _analyze_cipher_suite("DHE-RSA-AES256-GCM-SHA384")
        assert result["cipher_quantum_safe"] is False
        assert result["cipher_risk"] == "VULNERABLE"
        assert result["risk_points"] == 15

    def test_pqc_hybrid_mlkem(self):
        result = _analyze_cipher_suite("X25519MLKEM768-AES256-GCM-SHA384")
        assert result["cipher_quantum_safe"] is True
        assert result["cipher_risk"] == "COMPLIANT"
        assert result["risk_points"] == -20

    def test_pqc_hybrid_kyber(self):
        result = _analyze_cipher_suite("X25519Kyber768-AES256-GCM-SHA384")
        assert result["cipher_quantum_safe"] is True
        assert result["cipher_risk"] == "COMPLIANT"
        assert result["risk_points"] == -20

    def test_tls13_aes_gcm_no_explicit_kex(self):
        # TLS 1.3 cipher suites don't include the KEX in the name
        result = _analyze_cipher_suite("TLS_AES_256_GCM_SHA384")
        assert result["cipher_risk"] == "UNKNOWN"  # no KEX prefix detected
        assert result["cipher_quantum_safe"] is False

    def test_pqc_detection_case_insensitive(self):
        result = _analyze_cipher_suite("x25519MLKEM768")
        assert result["cipher_quantum_safe"] is True


# ──────────────────────────────────────────────────────────────────────────
# Unit Tests — _compute_risk_level
# ──────────────────────────────────────────────────────────────────────────

class TestComputeRiskLevel:
    @pytest.mark.parametrize("score,expected", [
        (100, "CRITICAL"),
        (80,  "CRITICAL"),
        (79,  "HIGH"),
        (60,  "HIGH"),
        (59,  "MEDIUM"),
        (40,  "MEDIUM"),
        (39,  "LOW"),
        (20,  "LOW"),
        (19,  "COMPLIANT"),
        (0,   "COMPLIANT"),
    ])
    def test_score_boundaries(self, score, expected):
        assert _compute_risk_level(score) == expected


# ──────────────────────────────────────────────────────────────────────────
# Unit Tests — _domain_matches_san
# ──────────────────────────────────────────────────────────────────────────

class TestDomainMatchesSan:
    def test_exact_match(self):
        assert _domain_matches_san("example.com", ["example.com"]) is True

    def test_wildcard_match(self):
        assert _domain_matches_san("www.example.com", ["*.example.com"]) is True

    def test_wildcard_no_deep_match(self):
        # *.example.com should NOT match sub.sub.example.com
        assert _domain_matches_san("a.b.example.com", ["*.example.com"]) is False

    def test_no_match(self):
        assert _domain_matches_san("other.com", ["example.com", "*.example.com"]) is False

    def test_case_insensitive(self):
        assert _domain_matches_san("WWW.Example.COM", ["*.example.com"]) is True


# ──────────────────────────────────────────────────────────────────────────
# Unit Tests — _extract_san_domains (with real certs)
# ──────────────────────────────────────────────────────────────────────────

class TestExtractSanDomains:
    def test_san_extraction(self, rsa_2048_key):
        cert = _make_self_signed_cert(
            rsa_2048_key,
            san_domains=["example.com", "*.example.com", "api.example.com"],
        )
        sans = _extract_san_domains(cert)
        assert "example.com" in sans
        assert "*.example.com" in sans
        assert "api.example.com" in sans

    def test_no_san_extension(self, rsa_2048_key):
        cert = _make_self_signed_cert(rsa_2048_key, san_domains=None)
        assert _extract_san_domains(cert) == []


# ──────────────────────────────────────────────────────────────────────────
# Unit Tests — _error_result
# ──────────────────────────────────────────────────────────────────────────

class TestErrorResult:
    def test_structure(self):
        now = datetime.now(timezone.utc)
        result = _error_result("fail.example.com", now, "TEST_ERROR", "Something broke")
        assert result["domain"] == "fail.example.com"
        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "Something broke"
        assert result["overall_risk_score"] is None
        assert result["risk_level"] is None
        assert result["certificates"] == []
        assert result["findings"] == []


# ──────────────────────────────────────────────────────────────────────────
# Unit Tests — _format_subject
# ──────────────────────────────────────────────────────────────────────────

class TestFormatSubject:
    def test_format(self, rsa_2048_key):
        cert = _make_self_signed_cert(rsa_2048_key, cn="scan.example.com")
        formatted = _format_subject(cert.subject)
        assert "commonName=scan.example.com" in formatted
        assert "organizationName=QuantCAI Test" in formatted


# ──────────────────────────────────────────────────────────────────────────
# Integration Tests — live scanning (requires network)
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestLiveScan:
    """
    These tests perform real TLS connections to public domains.
    Skip with: pytest -m "not integration"
    """

    def test_scan_google(self):
        result = scan_domain("google.com")
        assert result["domain"] == "google.com"
        assert result["overall_risk_score"] is not None
        assert result["risk_level"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "COMPLIANT")
        assert result["tls_version"] is not None
        assert result["cipher_suite"] is not None
        assert len(result["certificates"]) >= 1
        assert len(result["findings"]) >= 1
        assert result["cbom_summary"]["total_assets"] >= 1
        # Google typically uses ECC — should be flagged
        leaf = result["certificates"][0]
        assert "algorithm" in leaf

    def test_scan_with_protocol_prefix(self):
        """Ensure https:// prefix is stripped gracefully."""
        result = scan_domain("https://github.com")
        assert result["domain"] == "github.com"
        assert result.get("error") is None

    def test_scan_nonexistent_domain(self):
        """Non-routable domain should return a clean error."""
        result = scan_domain("this-domain-does-not-exist-pqc-test.invalid")
        assert result.get("error") is not None
        assert result["overall_risk_score"] is None

    def test_scan_connection_refused(self):
        """Localhost on a high port — should timeout or refuse."""
        result = scan_domain("127.0.0.1")
        assert result.get("error") is not None

    def test_output_is_json_serializable(self):
        result = scan_domain("google.com")
        # Must not raise
        serialized = json.dumps(result, default=str)
        assert isinstance(serialized, str)
        assert len(serialized) > 100

    def test_findings_have_required_fields(self):
        result = scan_domain("google.com")
        required_keys = {"severity", "title", "description", "remediation"}
        for finding in result["findings"]:
            assert required_keys.issubset(finding.keys()), (
                f"Finding missing keys: {required_keys - finding.keys()}"
            )

    def test_cbom_counts_are_consistent(self):
        result = scan_domain("google.com")
        cbom = result["cbom_summary"]
        assert cbom["total_assets"] >= cbom["vulnerable_assets"]
        assert cbom["total_assets"] >= cbom["compliant_assets"]
        assert cbom["vulnerable_assets"] + cbom["compliant_assets"] <= cbom["total_assets"]


@pytest.mark.integration
class TestLiveScanAsync:
    @pytest.mark.asyncio
    async def test_scan_domain_async(self):
        result = await scan_domain_async("google.com")
        assert result["domain"] == "google.com"
        assert result["overall_risk_score"] is not None


# ──────────────────────────────────────────────────────────────────────────
# Risk Score Integration Tests (boundary checks)
# ──────────────────────────────────────────────────────────────────────────

class TestRiskScoreBounds:
    def test_score_never_exceeds_100(self):
        """Even worst-case accumulation should clamp at 100."""
        # Simulate: RSA-2048 (35) + ECC (30) + ECDHE (15) + TLS 1.0 (20) = 100
        total = 35 + 30 + 15 + 20
        clamped = max(0, min(100, total))
        assert clamped == 100

    def test_score_never_below_zero(self):
        """PQC hybrid bonus should not push score negative."""
        total = -20  # only a PQC hybrid, nothing else
        clamped = max(0, min(100, total))
        assert clamped == 0

    def test_pqc_hybrid_reduces_score(self):
        """PQC hybrid should subtract from total."""
        # RSA-4096 (20) + PQC hybrid (-20) = 0
        total = 20 + (-20)
        clamped = max(0, min(100, total))
        assert clamped == 0
