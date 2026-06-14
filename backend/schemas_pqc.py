from pydantic import BaseModel, Field
from typing import List, Optional

class ScanRequest(BaseModel):
    domain: str = Field(..., description="Domain name to scan (e.g., github.com)")
    port: int = Field(443, description="Target TLS port (default is 443)")

class TlsDetails(BaseModel):
    version: str = Field(..., description="Negotiated TLS version (e.g., TLSv1.3)")
    cipher_suite: str = Field(..., description="Negotiated cipher suite name")
    key_exchange: Optional[str] = Field(None, description="Negotiated key exchange mechanism")
    key_exchange_group: Optional[str] = Field(None, description="Negotiated key exchange group/curve")
    key_exchange_bits: Optional[int] = Field(None, description="Key exchange key size in bits")
    quantum_safe: bool = Field(..., description="Whether the negotiated key exchange is quantum resistant")

class CertificateInfo(BaseModel):
    index: int = Field(..., description="Index in the certificate chain (0 = leaf)")
    subject: str = Field(..., description="Subject distinguished name")
    issuer: str = Field(..., description="Issuer distinguished name")
    serial_number: str = Field(..., description="Certificate serial number")
    algorithm: str = Field(..., description="Public key algorithm and key size (e.g., RSA-2048, ECC-secp256r1)")
    signature_algorithm: str = Field(..., description="Signature algorithm (e.g., sha256WithRSAEncryption)")
    quantum_vulnerable: Optional[bool] = Field(..., description="True if signature or key is quantum vulnerable")
    severity: str = Field(..., description="Vulnerability severity level")
    expires_at: str = Field(..., description="Expiration date string (YYYY-MM-DD)")
    days_until_expiry: int = Field(..., description="Days remaining until the certificate expires")
    expiry_warning: bool = Field(..., description="True if certificate expires within 90 days")
    extends_past_2030: bool = Field(..., description="True if a vulnerable certificate is valid past PQC migration deadline (2030)")

class Finding(BaseModel):
    severity: str = Field(..., description="Severity level: CRITICAL, HIGH, MEDIUM, WARNING, LOW, COMPLIANT")
    category: str = Field(..., description="Vulnerability category (e.g., CERTIFICATE_KEY, KEY_EXCHANGE, TLS_VERSION)")
    title: str = Field(..., description="Title of the vulnerability or compliance status")
    description: str = Field(..., description="Detailed description of the finding and its quantum threat model")
    affected_asset: str = Field(..., description="The name of the asset affected (e.g., certificate CN, TLS session)")
    remediation: str = Field(..., description="Actionable steps to resolve the vulnerability")
    nist_reference: Optional[str] = Field(None, description="NIST/CNSA/FIPS standards references")

class CBOMSummary(BaseModel):
    total_assets: int = Field(..., description="Total cryptographic assets analyzed")
    vulnerable_assets: int = Field(..., description="Total assets identified as quantum vulnerable")
    compliant_assets: int = Field(..., description="Total assets identified as quantum compliant")
    pqc_readiness_pct: float = Field(..., description="Percentage of assets that are quantum resistant")

class ScanResponse(BaseModel):
    domain: str = Field(..., description="Scanned domain")
    port: int = Field(..., description="Scanned port")
    scan_timestamp: str = Field(..., description="ISO timestamp of the scan")
    scan_duration_ms: int = Field(..., description="Total scan time in milliseconds")
    overall_risk_score: float = Field(..., description="Quantified quantum risk score (0-100)")
    risk_level: str = Field(..., description="Overall risk classification (CRITICAL, HIGH, MEDIUM, LOW, COMPLIANT)")
    hndl_risk_level: str = Field(..., description="Harvest Now, Decrypt Later risk level (CRITICAL, HIGH, MEDIUM, LOW, COMPLIANT)")
    quantum_risk_grade: str = Field(..., description="Quantum safety letter grade (Grade A, B, C, D, F)")
    tls_details: TlsDetails = Field(..., description="Negotiated TLS configuration details")
    certificates: List[CertificateInfo] = Field(..., description="List of certificate chain details")
    findings: List[Finding] = Field(..., description="Actionable security findings")
    cbom_summary: CBOMSummary = Field(..., description="CBOM summary statistics")
