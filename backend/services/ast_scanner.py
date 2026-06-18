import ast
import re
import os
import zipfile
import io
import logging
from typing import Any, Dict, List, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("quantcai.ast_scanner")

# Initialize LLM for AI refactoring
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
llm = None
if api_key:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0
        )
    except Exception as e:
        logger.warning(f"Could not initialize ChatGoogleGenerativeAI in ast_scanner: {e}")


# ---------------------------------------------------------------------------
# Vulnerability Signatures & Rules
# ---------------------------------------------------------------------------

SEVERITY_WEIGHTS = {
    "CRITICAL": 35.0,
    "HIGH": 25.0,
    "MEDIUM": 15.0,
    "LOW": 5.0
}

# Regex Matchers for Java, Go, and C++
JAVA_SIGNATURES = [
    (re.compile(r'KeyPairGenerator\.getInstance\(\s*"(RSA|DSA|EC)"\s*(,\s*"\w+")?\s*\)', re.IGNORECASE), {
        "severity": "CRITICAL",
        "title": "Quantum-Vulnerable Key Generator Instance (Java)",
        "description": "Instantiation of a legacy public key algorithm (RSA/DSA/EC) KeyPairGenerator detected. These algorithms are broken by Shor's algorithm.",
        "remediation": "Migrate to post-quantum digital signatures (ML-DSA / FIPS 204) and KEMs (ML-KEM / FIPS 203) when compatible."
    }),
    (re.compile(r'Cipher\.getInstance\(\s*"(RSA|DSA|DES|RC4|Blowfish)[^"]*"\s*\)', re.IGNORECASE), {
        "severity": "HIGH",
        "title": "Quantum-Vulnerable Cipher Suite (Java)",
        "description": "Use of vulnerable asymmetric cipher or outdated symmetric block cipher detected.",
        "remediation": "Ensure encryption uses quantum-resistant symmetric cryptography (AES-256) and lattice-based key agreement."
    }),
    (re.compile(r'import\s+java\.security\.(interfaces\.RSAPrivateKey|interfaces\.RSAPublicKey|interfaces\.DSAPrivateKey|spec\.RSAPublicKeySpec);'), {
        "severity": "HIGH",
        "title": "Vulnerable RSA/DSA Cryptographic Imports (Java)",
        "description": "Imports referencing legacy asymmetric keys (RSA/DSA) which are quantum-vulnerable.",
        "remediation": "Prioritize crypto agility abstraction layers to ease future migration to ML-DSA/ML-KEM."
    })
]

GO_SIGNATURES = [
    (re.compile(r'rsa\.GenerateKey\s*\('), {
        "severity": "HIGH",
        "title": "Quantum-Vulnerable RSA Key Generation (Go)",
        "description": "Generation of RSA asymmetric keypair detected. Shor's algorithm renders RSA vulnerable regardless of key bit-length.",
        "remediation": "Migrate to ML-DSA (FIPS 204) or post-quantum hybrid wrappers."
    }),
    (re.compile(r'elliptic\.P256\s*\(\)'), {
        "severity": "CRITICAL",
        "title": "Quantum-Vulnerable Elliptic Curve P-256 (Go)",
        "description": "Use of NIST P-256 elliptic curve group detected. ECC is highly vulnerable to Shor's algorithm.",
        "remediation": "Transition key exchanges to post-quantum hybrid algorithms (e.g. X25519MLKEM768)."
    }),
    (re.compile(r'import\s+\(\s*[^)]*"(crypto/rsa"|crypto/dsa"|crypto/elliptic")[^)]*\)'), {
        "severity": "HIGH",
        "title": "Vulnerable Key Exchange/Signature Imports (Go)",
        "description": "Go package imports for rsa, dsa, or elliptic curves detected.",
        "remediation": "Prepare codebases for transition to post-quantum crypto APIs."
    })
]

CPP_SIGNATURES = [
    (re.compile(r'(RSA_generate_key_ex|DSA_generate_parameters_ex|EC_KEY_new_by_curve_name)'), {
        "severity": "CRITICAL",
        "title": "Quantum-Vulnerable Key Generation (OpenSSL C/C++)",
        "description": "Use of OpenSSL legacy key generation APIs (RSA, DSA, EC) detected.",
        "remediation": "Integrate OpenSSL 3.5+ provider framework to load OQS (Open Quantum Safe) post-quantum providers."
    }),
    (re.compile(r'#(include)\s+<openssl/(rsa|dsa|dh|ec)\.h>'), {
        "severity": "HIGH",
        "title": "Quantum-Vulnerable OpenSSL Headers (C/C++)",
        "description": "Includes referencing OpenSSL legacy asymmetric key headers.",
        "remediation": "Audit structures to support cryptographic agility using EVP interfaces."
    })
]


class PythonASTAuditor(ast.NodeVisitor):
    """AST Visitor that parses Python source code trees for quantum vulnerability signatures."""
    def __init__(self, filename: str):
        self.filename = filename
        self.findings = []

    def visit_Import(self, node: ast.Import):
        for name in node.names:
            if name.name in ("cryptography.hazmat.primitives.asymmetric.rsa", "rsa"):
                self._add_finding(node, "HIGH", "Legacy RSA Import", 
                                  "Python code imports the legacy RSA module which is vulnerable to Shor's algorithm.", 
                                  "Migrate to post-quantum digital signatures.")
            elif name.name in ("cryptography.hazmat.primitives.asymmetric.dsa", "dsa"):
                self._add_finding(node, "CRITICAL", "Legacy DSA Import", 
                                  "Python code imports the deprecated DSA module.", 
                                  "Replace with ML-DSA (FIPS 204).")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            if "asymmetric.rsa" in node.module:
                self._add_finding(node, "HIGH", "Legacy RSA Import Module", 
                                  "Imports from RSA asymmetric module detected.", 
                                  "Migrate to post-quantum lattice alternatives.")
            elif "asymmetric.dsa" in node.module:
                self._add_finding(node, "CRITICAL", "Legacy DSA Import Module", 
                                  "Imports from DSA asymmetric module detected.", 
                                  "Replace with ML-DSA.")
            elif "asymmetric.ec" in node.module:
                self._add_finding(node, "HIGH", "Legacy Elliptic Curve Import Module", 
                                  "Imports from EC asymmetric module detected.", 
                                  "Prepare for transition to ML-KEM or SLH-DSA.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id

        if func_name == "generate_private_key":
            self._add_finding(node, "HIGH", "Asymmetric Private Key Generation", 
                              "Generation of asymmetric private keys detected. If this is RSA or ECC, it is vulnerable to CRQCs.", 
                              "Ensure keys are migrated to post-quantum digital signature standards.")
        elif func_name in ("generate_parameters", "generate_key"):
            self._add_finding(node, "HIGH", "Asymmetric Parameter/Key Setup", 
                              "APIs that configure parameters or keys for DH or DSA groups.", 
                              "Ensure all key arrangements use ML-KEM (FIPS 203).")
        self.generic_visit(node)

    def _add_finding(self, node: ast.AST, severity: str, title: str, description: str, remediation: str):
        self.findings.append({
            "file": self.filename,
            "line": node.lineno,
            "severity": severity,
            "title": title,
            "description": description,
            "remediation": remediation
        })


# ---------------------------------------------------------------------------
# Core Scanner Logic
# ---------------------------------------------------------------------------

class ASTScanner:
    """Scans code contents and directory zip files for quantum vulnerabilities."""

    @staticmethod
    def scan_code(filename: str, content: str, language: str) -> List[Dict[str, Any]]:
        """Scans a single file's string content based on its detected language."""
        findings = []
        lines = content.splitlines()

        if language == "python":
            try:
                tree = ast.parse(content, filename=filename)
                auditor = PythonASTAuditor(filename)
                auditor.visit(tree)
                findings.extend(auditor.findings)
            except Exception as e:
                # If AST parsing fails, fallback to regex-based heuristics for Python imports
                logger.warning(f"AST parse failed for {filename}: {e}. Falling back to regex.")
                for line_idx, line in enumerate(lines, 1):
                    if "import rsa" in line or "asymmetric.rsa" in line:
                        findings.append({
                            "file": filename,
                            "line": line_idx,
                            "severity": "HIGH",
                            "title": "Legacy RSA Import (Regex Fallback)",
                            "description": "Imports referencing legacy RSA module.",
                            "remediation": "Migrate to post-quantum signature schemes."
                        })

        elif language == "java":
            for rule_regex, meta in JAVA_SIGNATURES:
                for match in rule_regex.finditer(content):
                    # Estimate line number
                    matched_offset = match.start()
                    line_no = content[:matched_offset].count('\n') + 1
                    findings.append({
                        "file": filename,
                        "line": line_no,
                        "severity": meta["severity"],
                        "title": meta["title"],
                        "description": meta["description"],
                        "remediation": meta["remediation"]
                    })

        elif language == "go":
            for rule_regex, meta in GO_SIGNATURES:
                for match in rule_regex.finditer(content):
                    matched_offset = match.start()
                    line_no = content[:matched_offset].count('\n') + 1
                    findings.append({
                        "file": filename,
                        "line": line_no,
                        "severity": meta["severity"],
                        "title": meta["title"],
                        "description": meta["description"],
                        "remediation": meta["remediation"]
                    })

        elif language in ("cpp", "c"):
            for rule_regex, meta in CPP_SIGNATURES:
                for match in rule_regex.finditer(content):
                    matched_offset = match.start()
                    line_no = content[:matched_offset].count('\n') + 1
                    findings.append({
                        "file": filename,
                        "line": line_no,
                        "severity": meta["severity"],
                        "title": meta["title"],
                        "description": meta["description"],
                        "remediation": meta["remediation"]
                    })

        for f in findings:
            f["content"] = content

        return findings


    @classmethod
    def scan_zip_bytes(cls, zip_data: bytes) -> Dict[str, Any]:
        """Unzips archive bytes and runs scanner over code file tree."""
        vulnerabilities = []
        files_scanned = 0
        total_size = len(zip_data)

        # File extensions supported
        ext_to_lang = {
            ".py": "python",
            ".java": "java",
            ".go": "go",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".h": "cpp",
            ".hpp": "cpp"
        }

        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                for info in z.infolist():
                    if info.is_dir():
                        continue
                    
                    # Security checks: prevent directory traversal & excessive extraction size
                    if ".." in info.filename or info.filename.startswith("/"):
                        continue
                    
                    _, ext = os.path.splitext(info.filename.lower())
                    if ext in ext_to_lang:
                        files_scanned += 1
                        try:
                            with z.open(info.filename) as f:
                                # Limit read size per file to 2MB to prevent zip-bomb memory exhaustion
                                content_bytes = f.read(2000000)
                                content = content_bytes.decode("utf-8", errors="ignore")
                                lang = ext_to_lang[ext]
                                file_findings = cls.scan_code(info.filename, content, lang)
                                vulnerabilities.extend(file_findings)
                        except Exception as e:
                            logger.error(f"Error scanning zip file member {info.filename}: {e}")
        except Exception as e:
            logger.error(f"Failed to process ZIP archive: {e}")
            raise ValueError(f"Failed to process ZIP archive: {e}")

        # Compute summary metrics
        total_findings = len(vulnerabilities)
        critical_count = sum(1 for v in vulnerabilities if v["severity"] == "CRITICAL")
        high_count = sum(1 for v in vulnerabilities if v["severity"] == "HIGH")
        medium_count = sum(1 for v in vulnerabilities if v["severity"] == "MEDIUM")
        low_count = sum(1 for v in vulnerabilities if v["severity"] == "LOW")

        # Basic scoring algorithm
        total_risk_score = 0.0
        for v in vulnerabilities:
            total_risk_score += SEVERITY_WEIGHTS.get(v["severity"], 5.0)

        clamped_score = min(100.0, total_risk_score)
        pqc_readiness = round(100.0 - clamped_score, 1)

        return {
            "files_scanned": files_scanned,
            "pqc_readiness_pct": pqc_readiness,
            "overall_risk_score": round(clamped_score, 1),
            "summary": {
                "total_findings": total_findings,
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            "vulnerabilities": vulnerabilities
        }

    @classmethod
    def generate_code_remediation(cls, filename: str, file_content: str, line_no: int, issue_title: str) -> str:
        """
        Uses Gemini to generate a unified git diff patching the vulnerability at line_no.
        """
        if not llm:
            raise ValueError("Gemini API key is not configured. Cannot perform AI refactoring.")
        
        prompt = (
            f"You are a post-quantum cryptography expert code assistant.\n"
            f"The file '{filename}' has a quantum-vulnerability: '{issue_title}' near line {line_no}.\n"
            f"Here is the complete source code of the file:\n"
            f"```\n{file_content}\n```\n\n"
            f"Generate a unified git diff patch that fixes the vulnerability at/near line {line_no} by migrating "
            f"legacy cryptographic operations to post-quantum safe alternatives (or clean agnostic wrappers). "
            f"For Python, replace legacy rsa/dsa imports or calls with post-quantum placeholders or secure algorithms.\n"
            f"Provide ONLY the unified git diff patch in your response, starting with `diff --git` or `---` and ending with the last line of the diff. Do not include markdown code block syntax (like ```diff or ```) or any additional explanation text. The diff MUST be valid and directly applicable to the original code."
        )
        try:
            response = llm.invoke(prompt)
            patch = response.content
            # Clean up potential markdown formatting if Gemini ignored instructions
            if "```diff" in patch:
                patch = patch.split("```diff")[1].split("```")[0].strip()
            elif "```" in patch:
                patch = patch.split("```")[1].split("```")[0].strip()
            return patch.strip()
        except Exception as e:
            logger.error(f"Error calling Gemini LLM for refactoring: {e}")
            raise RuntimeError(f"Gemini LLM refactoring failed: {str(e)}")

