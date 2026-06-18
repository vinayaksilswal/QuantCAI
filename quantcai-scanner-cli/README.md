# QuantCAI PQC CLI Scanner

An open-source, lightweight Post-Quantum Cryptography (PQC) scanner to identify quantum-vulnerable digital assets (TLS protocols and certificate key pairs) in your network infrastructure.

Evaluating cryptographic preparedness is essential for the transition to **Q-Day / Year to Quantum (Y2Q)** compliance, aligning with NIST FIPS 203/204/205 standards and the CNSA 2.0 migration timelines.

---

## Features

- **TLS Handshake Verification**: Inspect negotiated TLS versions and cipher suites.
- **Key Classification**: Detect legacy algorithms (RSA, ECC, DSA) and evaluate key sizes against quantum decryption safety.
- **PQC Hybrid Key Exchange Identification**: Check for modern post-quantum algorithms (e.g. ML-KEM).
- **Comprehensive Risk Scoring**: Multi-factor additive risk rating from `COMPLIANT` to `CRITICAL`.
- **Actionable Remediation Guidelines**: Step-by-step remediation plans based on current NIST recommendations.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Pip

### Standard Installation

Clone this repository and install from the source:

```bash
cd quantcai-scanner-cli
pip install .
```

This installs the command-line utility `quantcai` globally.

---

## Usage

### 1. Basic Scan

Scan a standard web domain (uses port 443 by default):

```bash
quantcai scan google.com
```

### 2. Override Port

Scan a target utilizing a non-standard port:

```bash
quantcai scan example.com --port 8443
```

### 3. Save Report as JSON

Output the complete raw analysis to a structured JSON file:

```bash
quantcai scan example.com --output report.json
```

---

## Enterprise Integrations (Upgrade Path)

The open-source CLI focuses on external network scans. For internal resources, source code parsing, CI/CD pipeline blocking, and CycloneDX 1.6 Cryptographic Bill of Materials (CBOM) exports:

- Visit: [https://quantcai.in](https://quantcai.in)
- Email: [support@quantcai.in](mailto:support@quantcai.in)

---

## License

This project is licensed under the Apache-2.0 License. See the LICENSE file for details.
