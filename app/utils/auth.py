# Keycloak setup
import logging
from typing import List

import requests
from jose import jwt
from typing_extensions import TypedDict

from fastapi.security import OAuth2AuthorizationCodeBearer

keycloak_url = "https://auth.ocf.berkeley.edu/auth/"
realm_name = "ocf"
client_id = "ocfapi"

realm_metadata_request = requests.get(f"{keycloak_url}realms/{realm_name}")
if realm_metadata_request.status_code >= 400:
    logging.fatal(realm_metadata_request.text)
    raise Exception("Unable to fetch Keycloak realm metadata")

realm_metadata = realm_metadata_request.json()

KEYCLOAK_PUBLIC_KEY = (
    "-----BEGIN PUBLIC KEY-----\n"
    + realm_metadata["public_key"]
    + "\n-----END PUBLIC KEY-----"
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{keycloak_url}realms/{realm_name}/protocol/openid-connect/auth",
    tokenUrl=f"{keycloak_url}realms/{realm_name}/protocol/openid-connect/token",
    scheme_name="keycloak_auth",
    description="""Regular authentication through Keycloak
                which gives access to user-specific endpoints.""",
)


class RealmAccess(TypedDict):
    roles: List[str]


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
    realm_access: RealmAccess


def decode_token(token: str) -> UserToken:
    return jwt.decode(
        token,
        key=KEYCLOAK_PUBLIC_KEY,
        audience=client_id,
        options={"verify_signature": True, "verify_aud": False, "exp": True},
    )
