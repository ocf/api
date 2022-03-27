# Keycloak setup
from keycloak import KeycloakOpenID
from typing_extensions import TypedDict

from fastapi.security import OAuth2AuthorizationCodeBearer

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
    scheme_name="keycloak_auth",
    description="""Regular authentication through Keycloak
                which gives access to user-specific endpoints.""",
)


class UserToken(TypedDict):
    exp: int
    iat: int
    auth_time: int
    jti: str
    iss: str
    aud: str
    sub: str
    typ: str
    azp: str
    session_state: str
    acr: str
    scope: str
    sid: str
    email_verified: bool
    name: str
    preferred_username: str
    given_name: str
    email: str


def decode_token(token: str) -> UserToken:
    return keycloak_openid.decode_token(
        token,
        key=KEYCLOAK_PUBLIC_KEY,
        options={"verify_signature": True, "verify_aud": False, "exp": True},
    )
