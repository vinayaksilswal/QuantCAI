from setuptools import setup, find_packages

setup(
    name="quantcai-scanner",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "cryptography>=42.0.0",
    ],
    entry_points={
        "console_scripts": [
            "quantcai=quantcai_scanner.main:cli",
        ],
    },
    author="QuantCAI",
    author_email="support@quantcai.in",
    description="Open-Source Post-Quantum Cryptography (PQC) Vulnerability TLS Scanner CLI",
    long_description=open("README.md").read() if open("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/quantcai/quantcai-scanner",
    license="Apache-2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
