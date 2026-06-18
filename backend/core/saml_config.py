import os

SAML_ENABLED = os.getenv("SAML_ENABLED", "true").lower() == "true"
SAML_SP_ENTITY_ID = os.getenv("SAML_SP_ENTITY_ID", "https://api.quantcai.in/metadata")
SAML_SP_ACS_URL = os.getenv("SAML_SP_ACS_URL", "https://api.quantcai.in/api/v1/auth/saml/acs")

# Corporate Identity Provider (IdP) metadata defaults for standard federation
SAML_IDP_ENTITY_ID = os.getenv("SAML_IDP_ENTITY_ID", "https://idp.okta.com/exk123456789")
SAML_IDP_SSO_URL = os.getenv("SAML_IDP_SSO_URL", "https://idp.okta.com/exk123456789/sso/saml")
SAML_IDP_PUBLIC_CERT = os.getenv("SAML_IDP_PUBLIC_CERT", "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...")
