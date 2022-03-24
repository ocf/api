from fastapi import Depends
from fastapi.responses import JSONResponse
from . import router
from pydantic import BaseModel

from utils.user import get_current_user


class UserResponse(BaseModel):
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


@router.get("/user", tags=["account"], response_model=UserResponse)
async def get_user(current_user: dict = Depends(get_current_user)):
    return JSONResponse(content=current_user)  # will bypass output field limiting
