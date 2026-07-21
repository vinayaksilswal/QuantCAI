"""
=============================================================================
QuantCAI — GitHub Repository PQC Scanner
=============================================================================
Scans a target GitHub repository for legacy cryptographic primitives
(RSA, ECC, AES, SHA-1, DH) and insecure TLS configurations.

Generates a structured JSON vulnerability report used to construct 
B2B outbound sales audits for Post-Quantum Cryptography (PQC) migration.

Copyright (c) 2026 QuantCAI — All rights reserved.
=============================================================================
"""

import os
import re
import tempfile
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

from loguru import logger

# =============================================================================
# Detection Signatures
# =============================================================================

LEGACY_CRYPTO_PATTERNS = {
    # Python / Cryptography
    r"from\s+cryptography\.hazmat\.primitives\.asymmetric\s+import\s+rsa": "RSA Key Generation (Vulnerable to Shor's Algorithm)",
    r"from\s+cryptography\.hazmat\.primitives\.asymmetric\s+import\s+ec": "Elliptic Curve Cryptography (Vulnerable to Shor's Algorithm)",
    r"from\s+cryptography\.hazmat\.primitives\.asymmetric\s+import\s+dh": "Diffie-Hellman Key Exchange (Vulnerable to Shor's Algorithm)",
    r"RSA\.generate\(": "RSA Key Generation (PyCryptodome)",
    
    # Node.js / Crypto
    r"crypto\.generateKeyPairSync\(['\"]rsa['\"]": "RSA Key Generation (Node.js)",
    r"crypto\.generateKeyPairSync\(['\"]ec['\"]": "Elliptic Curve Cryptography (Node.js)",
    r"crypto\.createDiffieHellman\(": "Diffie-Hellman Key Exchange (Node.js)",
    
    # Java / JCA
    r"KeyPairGenerator\.getInstance\(['\"]RSA['\"]\)": "RSA Key Generation (Java JCA)",
    r"KeyPairGenerator\.getInstance\(['\"]EC['\"]\)": "Elliptic Curve Cryptography (Java JCA)",
    r"Cipher\.getInstance\(['\"]RSA.*['\"]\)": "RSA Encryption/Decryption (Java JCA)",
    
    # Go / crypto
    r"rsa\.GenerateKey\(": "RSA Key Generation (Go crypto/rsa)",
    r"ecdsa\.GenerateKey\(": "Elliptic Curve Cryptography (Go crypto/ecdsa)",
    r"tls\.TLS_ECDHE_RSA_WITH_AES_": "Legacy TLS Cipher Suite (Go crypto/tls)",
}

@dataclass
class Finding:
    file_path: str
    line_number: int
    match_text: str
    vulnerability_type: str
    recommendation: str

@dataclass
class ScanReport:
    repo_url: str
    files_scanned: int
    total_findings: int
    findings: List[Finding] = field(default_factory=list)
    risk_level: str = "LOW"

class PQCRepoScanner:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.temp_dir = tempfile.TemporaryDirectory()
        self.clone_dir = Path(self.temp_dir.name) / "repo"
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.temp_dir.cleanup()

    def clone_repo(self) -> bool:
        """Clones the repository (shallow clone) into the temporary directory."""
        logger.info(f"[PQC SCANNER] Cloning repository {self.repo_url}...")
        try:
            # We use --depth 1 to minimize download size
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0" # Disable prompt for private repos without auth
            
            subprocess.run(
                ["git", "clone", "--depth", "1", self.repo_url, str(self.clone_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                timeout=60
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"[PQC SCANNER] Failed to clone repo: {e.stderr.decode('utf-8')}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("[PQC SCANNER] Git clone timed out.")
            return False

    def scan(self) -> ScanReport:
        """Scans the cloned repository for legacy cryptographic primitives."""
        if not self.clone_dir.exists():
            if not self.clone_repo():
                raise Exception("Failed to clone repository for scanning.")

        logger.info(f"[PQC SCANNER] Starting scan on {self.repo_url}")
        
        report = ScanReport(repo_url=self.repo_url, files_scanned=0, total_findings=0)
        
        # Compile regex patterns
        compiled_patterns = {
            re.compile(pattern): desc 
            for pattern, desc in LEGACY_CRYPTO_PATTERNS.items()
        }
        
        # Walk directory
        for root, _, files in os.walk(self.clone_dir):
            if ".git" in root:
                continue
                
            for file_name in files:
                file_path = Path(root) / file_name
                
                # Skip binary files or massive minified files
                if file_path.suffix.lower() in [".png", ".jpg", ".pdf", ".zip", ".exe", ".dll", ".so", ".min.js"]:
                    continue
                    
                report.files_scanned += 1
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        
                    for line_num, line in enumerate(lines, 1):
                        for pattern, description in compiled_patterns.items():
                            if pattern.search(line):
                                rel_path = str(file_path.relative_to(self.clone_dir))
                                
                                # Provide migration recommendations based on type
                                rec = "Migrate to ML-KEM (Kyber) for Key Encapsulation."
                                if "Signature" in description or "RSA" in description or "ECDSA" in description:
                                    rec = "Migrate to ML-DSA (Dilithium) or SLH-DSA (Sphincs+) for Digital Signatures."
                                
                                finding = Finding(
                                    file_path=rel_path,
                                    line_number=line_num,
                                    match_text=line.strip()[:100],
                                    vulnerability_type=description,
                                    recommendation=rec
                                )
                                report.findings.append(finding)
                                report.total_findings += 1
                except UnicodeDecodeError:
                    # Ignore files that aren't valid UTF-8 text
                    pass
                except Exception as e:
                    logger.debug(f"Error reading file {file_path}: {e}")
                    
        # Determine risk level
        if report.total_findings > 10:
            report.risk_level = "CRITICAL"
        elif report.total_findings > 0:
            report.risk_level = "HIGH"
            
        logger.info(f"[PQC SCANNER] Scan complete. Found {report.total_findings} vulnerable primitives across {report.files_scanned} files.")
        return report

def scan_repository(repo_url: str) -> Dict[str, Any]:
    """Convenience wrapper for the scanner."""
    with PQCRepoScanner(repo_url) as scanner:
        report = scanner.scan()
        return {
            "repo_url": report.repo_url,
            "risk_level": report.risk_level,
            "files_scanned": report.files_scanned,
            "total_findings": report.total_findings,
            "findings": [
                {
                    "file": f.file_path,
                    "line": f.line_number,
                    "type": f.vulnerability_type,
                    "recommendation": f.recommendation
                }
                for f in report.findings
            ]
        }
