import re
from math import floor
from time import time
from typing import Dict, Union
from urllib.parse import urljoin

from jose import JWTError, jwt

from fastapi import Depends, HTTPException, status
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from utils.config import get_settings
from utils.constants import API_HOST

settings = get_settings()

JWT_AUDIENCE = "ocfapi_calnet"

calnet_jwt_auth_scheme = HTTPBearer(
    scheme_name="calnet_jwt",
    description="""JWT that authorizes a user to take
                actions on behalf of a CalNet UID.""",
)


def get_calnet_uid(
    calnet_jwt: HTTPAuthorizationCredentials = Depends(calnet_jwt_auth_scheme),
) -> int:
    try:
        payload = decode_calnet_jwt(calnet_jwt.credentials)
        if not verify_calnet_jwt(payload):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "malformed jwt")
    except JWTError as e:
        print(e)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "malformed jwt")
    else:
        return int(payload["sub"])


def create_calnet_jwt(uid: Union[int, str]) -> str:
    current_time = floor(time())
    return jwt.encode(
        {
            "aud": JWT_AUDIENCE,
            "sub": str(uid),
            "iat": current_time,
            "exp": current_time + 60 * 30,  # 60 sec * 30 min
        },
        settings.calnet_jwt_secret,
        algorithm="HS256",
    )


def verify_calnet_jwt(payload: Dict[str, Union[str, int]]) -> bool:
    try:
        if str(payload["aud"]) != JWT_AUDIENCE:
            return False
        if float(payload["iat"]) > time():
            return False
        if float(payload["exp"]) < time():
            return False
        if not int(payload["sub"]):
            return False
    except Exception:
        # will catch fields not existing, or not in correct type
        return False
    return True


def decode_calnet_jwt(calnet_jwt: str) -> Dict[str, Union[str, int]]:
    # the verification through python-jose is
    # not as good as what we can do ourselves
    return jwt.decode(
        calnet_jwt,
        settings.calnet_jwt_secret,
        algorithms="HS256",
        options={
            "verify_signature": True,
            "verify_aud": False,
            "verify_iat": False,
            "verify_exp": False,
            "verify_nbf": False,
            "verify_iss": False,
            "verify_sub": False,
            "verify_jti": False,
            "verify_at_hash": True,
            "require_aud": False,
            "require_iat": False,
            "require_exp": False,
            "require_nbf": False,
            "require_iss": False,
            "require_sub": False,
            "require_jti": False,
            "require_at_hash": False,
            "leeway": 0,
        },
    )


def get_calnet_service_url(host: str = API_HOST) -> str:
    if not re.match("^https?://", host):
        if settings.debug:
            host = "http://" + host
        else:
            host = "https://" + host
    url = urljoin(host, "/auth/calnet/callback")
    return url
