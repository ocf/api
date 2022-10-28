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


class RealmMetadata(TypedDict):
    realm: str
    public_key: str


realm_metadata_request = requests.get(f"{keycloak_url}realms/{realm_name}")
if not realm_metadata_request.ok:
    logging.fatal(realm_metadata_request.text)
    raise Exception("Unable to fetch Keycloak realm metadata")

realm_metadata: RealmMetadata = realm_metadata_request.json()
raw_public_key = realm_metadata.get("public_key")
if not raw_public_key:
    raise Exception("`public_key` not present in realm metadata")

KEYCLOAK_PUBLIC_KEY = (
    "-----BEGIN PUBLIC KEY-----\n" + raw_public_key + "\n-----END PUBLIC KEY-----"
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{keycloak_url}realms/{realm_name}/protocol/openid-connect/auth",
    tokenUrl=f"{keycloak_url}realms/{realm_name}/protocol/openid-connect/token",
    scheme_name="keycloak_auth",
    description="""Regular authentication through Keycloak
                which gives access to user-specific endpoints.""",
)


class RawUserToken(TypedDict):
    exp: int
    iat: int
    auth_time: int
    jti: str
    iss: str
    aud: List[str]
    sub: str
    typ: str
    azp: str
    nonce: str
    session_state: str
    allowed_origins: List[str]
    scope: str
    sid: str
    email_verified: bool
    name: str
    groups: List[str]
    preferred_username: str
    given_name: str
    email: str


class UserToken:
    username: str
    email: str
    name: str
    scope: str
    groups: List[str]
    raw: RawUserToken

    def __init__(self, raw_token: RawUserToken) -> None:
        _username = raw_token.get("preferred_username")
        if _username is None:
            raise Exception("username is None")
        self.username = _username

        _email = raw_token.get("email")
        if _email is None:
            raise Exception("email is None")
        self.email = _email

        _name = raw_token.get("name")
        if _name is None:
            raise Exception("name is None")
        self.name = _name

        _scope = raw_token.get("scope")
        if _scope is None:
            raise Exception("scope is None")
        self.scope = _scope

        _groups = raw_token.get("groups")
        if _groups is None:
            raise Exception("groups is None")
        self.groups = _groups

        self.raw = raw_token


def decode_token(token: str) -> UserToken:
    raw_user_token: RawUserToken = jwt.decode(
        token,
        key=KEYCLOAK_PUBLIC_KEY,
        audience=client_id,
        algorithms="RS256",
        options={"verify_aud": False, "require_exp": True},
    )

    return UserToken(raw_user_token)
