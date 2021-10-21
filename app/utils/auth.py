from fastapi.security import OAuth2AuthorizationCodeBearer

# Keycloak setup
from keycloak import KeycloakOpenID

keycloak_url = "https://auth.ocf.berkeley.edu/auth/"
realm_name = "ocf"

keycloak_openid = KeycloakOpenID(
    server_url=keycloak_url,
    client_id="ocfapi",
    realm_name=realm_name,
)

KEYCLOAK_PUBLIC_KEY = (
    "-----BEGIN PUBLIC KEY-----\n"
    + keycloak_openid.public_key()
    + "\n-----END PUBLIC KEY-----"
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{keycloak_url}realms/{realm_name}/protocol/openid-connect/auth",
    tokenUrl=f"{keycloak_url}realms/{realm_name}/protocol/openid-connect/token",
)


def decode_token(token: str):
    return keycloak_openid.decode_token(
        token,
        key=KEYCLOAK_PUBLIC_KEY,
        options={"verify_signature": True, "verify_aud": False, "exp": True},
    )
