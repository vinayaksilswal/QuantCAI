from __future__ import annotations

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class AlgorithmProperties(BaseModel):
    primitive: Optional[str] = None
    parameterSetIdentifier: Optional[str] = None
    curve: Optional[str] = None
    padding: Optional[str] = None
    mode: Optional[str] = None
    keyLength: Optional[int] = None


class CertificateProperties(BaseModel):
    subjectName: Optional[str] = None
    issuerName: Optional[str] = None
    validFrom: Optional[str] = None
    validTo: Optional[str] = None
    signatureAlgorithm: Optional[str] = None
    subjectAlternativeNames: Optional[List[str]] = None


class CipherSuiteAlgorithm(BaseModel):
    name: str
    algorithms: List[str]


class ProtocolProperties(BaseModel):
    type: Optional[str] = None  # e.g., 'tls'
    version: Optional[str] = None  # e.g., '1.2' or '1.3'
    cipherSuites: Optional[List[CipherSuiteAlgorithm]] = None


class CryptoProperties(BaseModel):
    assetType: Literal["algorithm", "certificate", "protocol", "related-crypto-material"]
    algorithmProperties: Optional[AlgorithmProperties] = None
    certificateProperties: Optional[CertificateProperties] = None
    protocolProperties: Optional[ProtocolProperties] = None
    oid: Optional[str] = None


class Component(BaseModel):
    bom_ref: str = Field(..., alias="bom-ref")
    type: Literal["cryptographic-asset"] = "cryptographic-asset"
    name: str
    description: Optional[str] = None
    cryptoProperties: CryptoProperties

    class Config:
        populate_by_name = True


class Dependency(BaseModel):
    ref: str
    dependsOn: Optional[List[str]] = Field(default=None, alias="dependsOn")

    class Config:
        populate_by_name = True


class Tool(BaseModel):
    vendor: Optional[str] = "QuantCAI"
    name: str = "PQC Compliance Scanner"
    version: str = "1.6.0"


class Metadata(BaseModel):
    timestamp: str
    tools: Optional[List[Tool]] = Field(default_factory=lambda: [Tool()])


class CycloneDXCBOM(BaseModel):
    bomFormat: Literal["CycloneDX"] = "CycloneDX"
    specVersion: Literal["1.6"] = "1.6"
    serialNumber: str
    version: int = 1
    metadata: Metadata
    components: List[Component]
    dependencies: List[Dependency] = Field(default_factory=list)
