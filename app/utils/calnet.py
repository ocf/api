from fastapi import Depends, HTTPException, status
from fastapi.security.http import HTTPBearer
from jose import jwt
from time import time
from math import floor
from typing import Dict, Union
import os
from utils.constants import API_HOST

SERVICE_URL = f"{API_HOST}/login/calnet"
__JWT_SECRET = os.getrandom(32).hex()
JWT_AUDIENCE = "ocfapi_calnet"


def get_calnet_uid(calnet_jwt: str = Depends(HTTPBearer())) -> int:
    payload = decode_calnet_jwt(calnet_jwt)
    if not verify_calnet_jwt(payload):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "malformed jwt")
    return int(payload["sub"])


def create_calnet_jwt(uid: Union[int, str]) -> str:
    current_time = floor(time())
    return jwt.encode(
        {
            "sub": str(uid),
            "iat": current_time,
            "exp": current_time + 60 * 30,  # 60 sec * 30 min
        },
        __JWT_SECRET,
    )


def verify_calnet_jwt(payload: Dict[str, str]) -> bool:
    if "aud" not in payload or payload["aud"] != JWT_AUDIENCE:
        return False
    if (
        "iat" not in payload
        or not payload["iat"].isdigit()
        or float(payload["iat"]) > time()
    ):
        return False
    if (
        "exp" not in payload
        or not payload["exp"].isdigit()
        or float(payload["exp"]) < time()
    ):
        return False
    if "sub" not in payload or not payload["sub"].isdigit():
        return False
    return True


def decode_calnet_jwt(calnet_jwt: str) -> Dict[str, str]:
    return jwt.decode(calnet_jwt, __JWT_SECRET)
