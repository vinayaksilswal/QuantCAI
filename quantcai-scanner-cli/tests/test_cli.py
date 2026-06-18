import json
from click.testing import CliRunner
from unittest.mock import patch
from quantcai_scanner.main import cli

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "QuantCAI" in result.output
    assert "scan" in result.output

def test_scan_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['scan', '--help'])
    assert result.exit_code == 0
    assert "Scan a domain or IP" in result.output

@patch('quantcai_scanner.main.scan_domain')
def test_scan_success(mock_scan):
    mock_scan.return_value = {
        "domain": "example.com",
        "scan_timestamp": "2026-06-18T10:00:00Z",
        "scan_duration_ms": 250,
        "overall_risk_score": 15.0,
        "risk_level": "LOW",
        "tls_version": "TLS 1.3",
        "tls_version_risk": "OK",
        "cipher_suite": "TLS_AES_256_GCM_SHA384",
        "cipher_bits": 256,
        "cipher_quantum_safe": False,
        "certificates": [],
        "findings": [
            {
                "severity": "LOW",
                "category": "KEY_EXCHANGE",
                "title": "Quantum-Vulnerable Key Exchange",
                "description": "ECDHE key exchange is vulnerable.",
                "remediation": "Deploy ML-KEM-768."
            }
        ],
        "cbom_summary": {
            "total_assets": 1,
            "vulnerable_assets": 1,
            "compliant_assets": 0,
            "pqc_readiness_pct": 0.0
        }
    }
    
    runner = CliRunner()
    result = runner.invoke(cli, ['scan', 'example.com'])
    assert result.exit_code == 0
    assert "QuantCAI PQC Scanner Report" in result.output
    assert "LOW" in result.output
    assert "TLS 1.3" in result.output

@patch('quantcai_scanner.main.scan_domain')
def test_scan_critical_exit_code(mock_scan):
    mock_scan.return_value = {
        "domain": "vulnerable.com",
        "scan_timestamp": "2026-06-18T10:00:00Z",
        "scan_duration_ms": 250,
        "overall_risk_score": 85.0,
        "risk_level": "CRITICAL",
        "tls_version": "TLS 1.0",
        "tls_version_risk": "CRITICAL",
        "cipher_suite": "TLS_RSA_WITH_AES_256_CBC_SHA",
        "cipher_bits": 256,
        "cipher_quantum_safe": False,
        "certificates": [],
        "findings": [
            {
                "severity": "CRITICAL",
                "category": "TLS_VERSION",
                "title": "TLS Version 1.0 Detected",
                "description": "TLS 1.0 is obsolete.",
                "remediation": "Upgrade to TLS 1.3."
            }
        ],
        "cbom_summary": {
            "total_assets": 1,
            "vulnerable_assets": 1,
            "compliant_assets": 0,
            "pqc_readiness_pct": 0.0
        }
    }
    
    runner = CliRunner()
    result = runner.invoke(cli, ['scan', 'vulnerable.com'])
    # Should exit with code 1 for CRITICAL or HIGH risk levels
    assert result.exit_code == 1
    assert "CRITICAL" in result.output

def test_scan_enterprise_source_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ['scan', '--source', 'setup.py'])
    assert result.exit_code == 0
    assert "Source Code AST Scanning is an Enterprise feature" in result.output
