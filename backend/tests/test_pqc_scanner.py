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
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa, ed25519
from cryptography.x509.oid import NameOID

from services.pqc_scanner import (
    _classify_public_key,
    _analyze_key_exchange,
    _analyze_symmetric_strength,
    _compute_risk_level,
    _domain_matches_san,
    _extract_san_domains,
    _error_result,
    _format_subject,
    _normalize_group,
    scan_domain,
    scan_domain_async,
    PQC_HYBRID_KEYWORDS,
    PQC_NAMED_GROUPS,
    CLASSICAL_NAMED_GROUPS,
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
# Unit Tests — _analyze_key_exchange
#
# TLS 1.3 encodes NO key exchange information in the cipher suite name; the
# key exchange is the negotiated named group. The previous implementation
# matched keywords against the suite name, so it reported every TLS 1.3 host
# as quantum-vulnerable with a +50 penalty — including hosts actually running
# ML-KEM. The superseded test asserted that behaviour as correct, which is a
# large part of why it survived.
# ──────────────────────────────────────────────────────────────────────────

class TestAnalyzeKeyExchangeTls12:
    """TLS 1.2 and earlier DO embed the exchange in the suite name."""

    def test_ecdhe_is_vulnerable(self):
        result = _analyze_key_exchange("ECDHE-RSA-AES256-GCM-SHA384", "TLSv1.2")
        assert result["cipher_quantum_safe"] is False
        assert result["cipher_risk"] == "VULNERABLE"
        assert result["risk_points"] == 15

    def test_dhe_is_vulnerable(self):
        result = _analyze_key_exchange("DHE-RSA-AES256-GCM-SHA384", "TLSv1.2")
        assert result["cipher_quantum_safe"] is False
        assert result["cipher_risk"] == "VULNERABLE"
        assert result["risk_points"] == 15


class TestAnalyzeKeyExchangeTls13:
    """TLS 1.3 must be judged on the negotiated group, never the suite name."""

    def test_mlkem_group_is_compliant(self):
        result = _analyze_key_exchange(
            "TLS_AES_256_GCM_SHA384", "TLSv1.3", group="X25519MLKEM768"
        )
        assert result["cipher_quantum_safe"] is True
        assert result["cipher_risk"] == "COMPLIANT"
        assert result["risk_points"] == -20

    def test_classical_group_is_vulnerable(self):
        result = _analyze_key_exchange(
            "TLS_AES_256_GCM_SHA384", "TLSv1.3", group="x25519"
        )
        assert result["cipher_quantum_safe"] is False
        assert result["cipher_risk"] == "VULNERABLE"
        assert result["risk_points"] == 15

    def test_draft_kyber_group_flagged_as_pre_standard(self):
        """Kyber draft groups are post-quantum but not ratified FIPS 203."""
        result = _analyze_key_exchange(
            "TLS_AES_256_GCM_SHA384", "TLSv1.3", group="X25519Kyber768Draft00"
        )
        assert result["cipher_quantum_safe"] is True
        assert result["cipher_risk"] == "WARNING"
        assert "FIPS 203" in result["cipher_reason"]

    def test_group_detection_is_case_and_separator_insensitive(self):
        for variant in ("x25519mlkem768", "X25519-MLKEM-768", "X25519_MLKEM_768"):
            result = _analyze_key_exchange("TLS_AES_256_GCM_SHA384", "TLSv1.3", group=variant)
            assert result["cipher_quantum_safe"] is True, variant

    def test_unmeasurable_group_is_undetermined_not_vulnerable(self):
        """
        The regression guard. An inability to read the group is a scanner
        limitation, not a finding about the target, and must carry no risk
        points — the old code charged 50 and declared the host vulnerable.
        """
        result = _analyze_key_exchange("TLS_AES_256_GCM_SHA384", "TLSv1.3")
        assert result["cipher_quantum_safe"] is None
        assert result["cipher_risk"] == "UNDETERMINED"
        assert result["risk_points"] == 0.0

    def test_capability_probe_resolves_undetermined_case(self):
        confirmed = _analyze_key_exchange(
            "TLS_AES_256_GCM_SHA384", "TLSv1.3", pqc_capable=True
        )
        assert confirmed["cipher_quantum_safe"] is True
        assert confirmed["risk_points"] == -20

        refused = _analyze_key_exchange(
            "TLS_AES_256_GCM_SHA384", "TLSv1.3", pqc_capable=False
        )
        assert refused["cipher_quantum_safe"] is False
        assert refused["risk_points"] == 15

    def test_negotiated_pqc_group_wins_over_probe(self):
        """A measured PQC group is authoritative even if a probe failed."""
        result = _analyze_key_exchange(
            "TLS_AES_256_GCM_SHA384", "TLSv1.3",
            group="X25519MLKEM768", pqc_capable=False,
        )
        assert result["cipher_quantum_safe"] is True


class TestGroupTables:
    def test_group_tables_are_disjoint(self):
        """A group cannot be both post-quantum and classical."""
        assert not (PQC_NAMED_GROUPS & CLASSICAL_NAMED_GROUPS)

    def test_group_tables_are_prenormalized(self):
        """Lookups normalize the input, so the tables must already be normal."""
        for group in PQC_NAMED_GROUPS | CLASSICAL_NAMED_GROUPS:
            assert _normalize_group(group) == group, f"{group!r} is not normalized"


class TestCnsaTimeline:
    """
    The "2030 deadline" in most vendor material is CNSA 2.0's software and
    firmware signing date. Web servers must prefer PQC from 2025 and use it
    exclusively by 2033. Citing 2030 at a TLS endpoint is the wrong system
    class and fails procurement scrutiny.
    """

    def test_scanner_targets_the_web_server_class(self):
        from services.pqc_scanner import _SCAN_SYSTEM_CLASS, CNSA_2_0_TIMELINE
        assert _SCAN_SYSTEM_CLASS == "web_servers_browsers_cloud"
        assert CNSA_2_0_TIMELINE[_SCAN_SYSTEM_CLASS]["exclusive"] == 2033
        assert CNSA_2_0_TIMELINE[_SCAN_SYSTEM_CLASS]["prefer"] == 2025

    def test_signing_and_web_deadlines_are_not_conflated(self):
        from services.pqc_scanner import CNSA_2_0_TIMELINE
        signing = CNSA_2_0_TIMELINE["software_firmware_signing"]["exclusive"]
        web = CNSA_2_0_TIMELINE["web_servers_browsers_cloud"]["exclusive"]
        assert signing == 2030
        assert web == 2033
        assert signing != web, "These are distinct deadlines and must not be merged."

    def test_rsa_remediation_does_not_cite_the_signing_deadline_as_the_web_one(self):
        from services.pqc_scanner import _remediation_for_key
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
        text = _remediation_for_key(key)
        assert "2033" in text


class TestEdgeTermination:
    """
    Most observed PQ-TLS deployment sits at a handful of CDNs. Reporting an
    edge result as origin compliance would put a false claim into a CBOM.
    """

    def test_cloudflare_issuer_is_detected(self):
        from services.pqc_scanner import detect_edge_termination
        assert detect_edge_termination("CN=Cloudflare Inc ECC CA-3, O=Cloudflare, Inc.", []) == "Cloudflare"

    def test_ordinary_issuer_is_treated_as_origin(self):
        from services.pqc_scanner import detect_edge_termination
        assert detect_edge_termination("CN=Internal Corp Issuing CA, O=Example Corp", ["example.com"]) is None

    def test_large_san_list_implies_shared_edge_certificate(self):
        from services.pqc_scanner import detect_edge_termination
        many = [f"host{i}.example.com" for i in range(60)]
        assert detect_edge_termination("CN=Some CA", many) is not None

    def test_detection_is_case_insensitive(self):
        from services.pqc_scanner import detect_edge_termination
        assert detect_edge_termination("cn=CLOUDFLARE INC ECC CA-3", []) == "Cloudflare"


class TestSymmetricStrength:
    """Grover halves symmetric strength; CNSA 2.0 therefore requires AES-256."""

    def test_aes256_is_compliant(self):
        assert _analyze_symmetric_strength("TLS_AES_256_GCM_SHA384", 256) is None

    def test_aes128_is_flagged(self):
        finding = _analyze_symmetric_strength("TLS_AES_128_GCM_SHA256", 128)
        assert finding is not None
        assert finding["severity"] == "HIGH"
        assert "64 bits" in finding["description"]

    def test_unknown_bits_does_not_fabricate_a_finding(self):
        assert _analyze_symmetric_strength("UNKNOWN", 0) is None


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


# ──────────────────────────────────────────────────────────────────────────
# New Unit Tests: CycloneDX 1.6, Internal IPs, and Route Gating
# ──────────────────────────────────────────────────────────────────────────

def test_cyclonedx_cbom_generation_and_validation():
    from models.cyclonedx_models import CycloneDXCBOM
    from services.pqc_scanner import generate_cyclonedx_cbom
    
    # Construct a valid dummy scan result
    dummy_scan = {
        "domain": "test.example.com",
        "scan_timestamp": "2026-06-07T14:45:00Z",
        "tls_version": "TLSv1.3",
        "cipher_suite": "TLS_AES_256_GCM_SHA384",
        "certificates": [
            {
                "index": 0,
                "subject": "CN=test.example.com",
                "issuer": "CN=QuantCAI CA",
                "algorithm": "ECC-secp256r1-256",
                "signature_algorithm": "ecdsa-with-SHA256",
                "expires_at": "2027-06-07",
                "quantum_vulnerable": True
            }
        ]
    }
    
    cbom_dict = generate_cyclonedx_cbom(dummy_scan)
    
    # Validate structure using the Pydantic model
    cbom = CycloneDXCBOM(**cbom_dict)
    
    assert cbom.bomFormat == "CycloneDX"
    assert cbom.specVersion == "1.6"
    assert len(cbom.components) == 3  # TLS protocol, cert-0, and cert-0's algorithm
    
    # Check that it contains cryptographic assets
    assert cbom.components[0].type == "cryptographic-asset"
    assert cbom.components[0].cryptoProperties.assetType == "protocol"
    assert cbom.components[0].cryptoProperties.protocolProperties.version == "1.3"


@patch("services.pqc_scanner.socket.create_connection")
@patch("services.pqc_scanner.ssl.create_default_context")
def test_scan_domain_internal_ip_config(mock_ssl_ctx, mock_create_conn):
    import ssl
    # Mock ssl context and wrap_socket
    mock_ctx_instance = MagicMock()
    mock_ssl_ctx.return_value = mock_ctx_instance
    mock_ssock = MagicMock()
    # Mock cipher() and version() and getpeercert() to avoid exceptions
    mock_ssock.cipher.return_value = ("ECDHE-RSA-AES256-GCM-SHA384", "TLSv1.3", 256)
    mock_ssock.version.return_value = "TLSv1.3"
    mock_ssock.getpeercert.return_value = b"mock_der_bytes"
    mock_ssock._sslobj.get_verified_chain.return_value = None
    mock_ctx_instance.wrap_socket.return_value.__enter__.return_value = mock_ssock
    
    # Run scan for internal domain
    result = scan_domain("192.168.1.100", port=8443)
    
    # Assert connection was made on custom port
    mock_create_conn.assert_called_with(("192.168.1.100", 8443), timeout=5)
    
    # Assert check_hostname and verify_mode are disabled for internal domain
    assert mock_ctx_instance.check_hostname is False
    assert mock_ctx_instance.verify_mode == ssl.CERT_NONE
    
    # Run scan for external domain
    mock_ctx_instance.check_hostname = True
    mock_ctx_instance.verify_mode = ssl.CERT_REQUIRED
    scan_domain("google.com")
    
    # Assert check_hostname and verify_mode are enabled for external domain
    assert mock_ctx_instance.check_hostname is True
    assert mock_ctx_instance.verify_mode == ssl.CERT_REQUIRED


@pytest.mark.asyncio
@patch("routers.pqc.redis_client", new_callable=AsyncMock)
@patch("routers.pqc.scan_domain_async", new_callable=AsyncMock)
async def test_enterprise_scan_role_based_access(mock_scan, mock_redis):
    # Import locally to avoid scope/pollution issues
    from main import app
    from security import create_access_token
    from core.database import async_session_factory
    from httpx import ASGITransport, AsyncClient
    import models as DBmodels
    from sqlalchemy import text
    
    # Setup test users
    suffix = os.urandom(4).hex()
    email_free = f"free_pqc_{suffix}@example.com"
    email_pro = f"pro_pqc_{suffix}@example.com"
    email_ent = f"ent_pqc_{suffix}@example.com"
    email_root = f"root_pqc_{suffix}@example.com"
    
    async with async_session_factory() as session:
        user_free = DBmodels.User(email=email_free, name="Free PQC User", hashed_password="pwd", role=DBmodels.UserRole.LEARNER, is_active=True)
        user_pro = DBmodels.User(email=email_pro, name="Pro PQC User", hashed_password="pwd", role=DBmodels.UserRole.LEARNER, is_active=True)
        user_ent = DBmodels.User(email=email_ent, name="Ent PQC User", hashed_password="pwd", role=DBmodels.UserRole.ENTERPRISE_USER, is_active=True)
        user_root = DBmodels.User(email=email_root, name="Root PQC User", hashed_password="pwd", role=DBmodels.UserRole.ROOT, is_active=True)
        session.add_all([user_free, user_pro, user_ent, user_root])
        await session.flush()
        
        # Add subscription plans
        sub_free = DBmodels.Subscription(user_id=user_free.id, plan=DBmodels.SubscriptionPlan.FREE, status=DBmodels.SubscriptionStatus.ACTIVE)
        sub_pro = DBmodels.Subscription(user_id=user_pro.id, plan=DBmodels.SubscriptionPlan.PRO, status=DBmodels.SubscriptionStatus.ACTIVE)
        sub_ent = DBmodels.Subscription(user_id=user_ent.id, plan=DBmodels.SubscriptionPlan.ENTERPRISE, status=DBmodels.SubscriptionStatus.ACTIVE)
        # Root doesn't need a sub as root role is allowed
        session.add_all([sub_free, sub_pro, sub_ent])
        await session.commit()
        
        free_id, pro_id, ent_id, root_id = user_free.id, user_pro.id, user_ent.id, user_root.id
        
    try:
        # Create JWT tokens
        token_free = create_access_token({"sub": str(free_id), "type": "access", "role": "learner", "token_version": 0})
        token_pro = create_access_token({"sub": str(pro_id), "type": "access", "role": "learner", "token_version": 0})
        token_ent = create_access_token({"sub": str(ent_id), "type": "access", "role": "enterprise_user", "token_version": 0})
        token_root = create_access_token({"sub": str(root_id), "type": "access", "role": "root", "token_version": 0})
        
        # Configure scan mock
        mock_scan.return_value = {
            "domain": "test.example.com",
            "scan_timestamp": "2026-06-07T14:45:00Z",
            "tls_version": "TLSv1.3",
            "cipher_suite": "TLS_AES_256_GCM_SHA384",
            "certificates": []
        }
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Free user request - should return 403 Forbidden
            res = await client.get("/api/v1/enterprise/scan/test.example.com/cyclonedx", headers={"Authorization": f"Bearer {token_free}"})
            assert res.status_code == 403
            
            # 2. Pro user request - should return 200 OK.
            # CBOM export was deliberately opened up from Enterprise-only to
            # Pro-and-above: it is the clearest reason to upgrade from Free,
            # and gating it at Enterprise left the Pro tier without its
            # headline deliverable. Exports still consume the monthly scan
            # quota, so this is not an unmetered bypass.
            res = await client.get("/api/v1/enterprise/scan/test.example.com/cyclonedx", headers={"Authorization": f"Bearer {token_pro}"})
            assert res.status_code == 200
            assert res.json()["bomFormat"] == "CycloneDX"


            # 3. Enterprise user request - should return 200 OK
            res = await client.get("/api/v1/enterprise/scan/test.example.com/cyclonedx", headers={"Authorization": f"Bearer {token_ent}"})
            assert res.status_code == 200
            assert res.json()["bomFormat"] == "CycloneDX"
            
            # 4. Root user request - should return 200 OK
            res = await client.get("/api/v1/enterprise/scan/test.example.com/cyclonedx", headers={"Authorization": f"Bearer {token_root}"})
            assert res.status_code == 200
            assert res.json()["bomFormat"] == "CycloneDX"
            
    finally:
        # Cleanup
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM usage_events WHERE user_id IN (:u1, :u2, :u3, :u4)"), {"u1": free_id, "u2": pro_id, "u3": ent_id, "u4": root_id})
            await session.execute(text("DELETE FROM subscriptions WHERE user_id IN (:u1, :u2, :u3)"), {"u1": free_id, "u2": pro_id, "u3": ent_id})
            await session.execute(text("DELETE FROM users WHERE id IN (:u1, :u2, :u3, :u4)"), {"u1": free_id, "u2": pro_id, "u3": ent_id, "u4": root_id})
            await session.commit()


@pytest.mark.asyncio
@patch("routers.pqc.redis_client", new_callable=AsyncMock)
@patch("routers.pqc.scanner_engine.scan_tls_pqc")
async def test_post_pqc_scan_endpoint(mock_scan, mock_redis):
    from main import app
    from security import create_access_token
    from core.database import async_session_factory
    from httpx import ASGITransport, AsyncClient
    import models as DBmodels
    from sqlalchemy import text
    
    suffix = os.urandom(4).hex()
    email_pro = f"pro_post_{suffix}@example.com"
    email_free = f"free_post_{suffix}@example.com"
    
    async with async_session_factory() as session:
        user_pro = DBmodels.User(email=email_pro, name="Pro Post User", hashed_password="pwd", role=DBmodels.UserRole.LEARNER, is_active=True)
        user_free = DBmodels.User(email=email_free, name="Free Post User", hashed_password="pwd", role=DBmodels.UserRole.LEARNER, is_active=True)
        session.add_all([user_pro, user_free])
        await session.flush()
        
        sub_pro = DBmodels.Subscription(user_id=user_pro.id, plan=DBmodels.SubscriptionPlan.PRO, status=DBmodels.SubscriptionStatus.ACTIVE)
        sub_free = DBmodels.Subscription(user_id=user_free.id, plan=DBmodels.SubscriptionPlan.FREE, status=DBmodels.SubscriptionStatus.ACTIVE)
        session.add_all([sub_pro, sub_free])
        await session.commit()
        
        pro_id, free_id = user_pro.id, user_free.id
        
    try:
        token_pro = create_access_token({"sub": str(pro_id), "type": "access", "role": "learner", "token_version": 0})
        token_free = create_access_token({"sub": str(free_id), "type": "access", "role": "learner", "token_version": 0})
        
        # Configure mocks
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_scan.return_value = {
            "domain": "github.com",
            "port": 443,
            "scan_timestamp": "2026-06-13T19:40:00Z",
            "scan_duration_ms": 120,
            "overall_risk_score": 50.0,
            "risk_level": "MEDIUM",
            "hndl_risk_level": "CRITICAL",
            "quantum_risk_grade": "Grade C",
            "tls_details": {
                "version": "TLS 1.3",
                "cipher_suite": "TLS_AES_256_GCM_SHA384",
                "key_exchange": "ECDHE",
                "key_exchange_group": "X25519",
                "key_exchange_bits": 256,
                "quantum_safe": False
            },
            "certificates": [
                {
                    "index": 0,
                    "subject": "CN=github.com",
                    "issuer": "CN=DigiCert",
                    "serial_number": "111",
                    "algorithm": "ECC-secp256r1-256",
                    "signature_algorithm": "ecdsa-with-SHA256",
                    "quantum_vulnerable": True,
                    "severity": "CRITICAL",
                    "expires_at": "2027-01-01",
                    "days_until_expiry": 200,
                    "expiry_warning": False,
                    "extends_past_2030": False
                }
            ],
            "findings": [
                {
                    "severity": "CRITICAL",
                    "category": "KEY_EXCHANGE",
                    "title": "Vulnerable KEX",
                    "description": "ECDHE is vulnerable",
                    "affected_asset": "TLS session",
                    "remediation": "Deploy hybrid KEX",
                    "nist_reference": "FIPS 203"
                }
            ],
            "cbom_summary": {
                "total_assets": 1,
                "vulnerable_assets": 1,
                "compliant_assets": 0,
                "pqc_readiness_pct": 0.0
            }
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Test 1: Scan with Pro User payload (POST)
            res = await client.post(
                "/api/v1/pqc/scan", 
                json={"domain": "github.com", "port": 443}, 
                headers={"Authorization": f"Bearer {token_pro}"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["domain"] == "github.com"
            assert data["port"] == 443
            assert data["tls_details"]["quantum_safe"] is False
            
            # Test 2: Scan with Free User payload (POST) - should still allow first scans under limit
            res_free = await client.post(
                "/api/v1/pqc/scan", 
                json={"domain": "github.com", "port": 443}, 
                headers={"Authorization": f"Bearer {token_free}"}
            )
            assert res_free.status_code == 200
            
    finally:
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM usage_events WHERE user_id IN (:u1, :u2)"), {"u1": pro_id, "u2": free_id})
            await session.execute(text("DELETE FROM subscriptions WHERE user_id IN (:u1, :u2)"), {"u1": pro_id, "u2": free_id})
            await session.execute(text("DELETE FROM users WHERE id IN (:u1, :u2)"), {"u1": pro_id, "u2": free_id})
            await session.commit()


