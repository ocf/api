from typing import List

from typing_extensions import Literal

from ocflib.account.search import user_is_group

from fastapi import Depends
from pydantic import BaseModel

from routes import router
from utils.auth import UserToken
from utils.user import get_current_user


class AccountInfoOutput(BaseModel):
    username: str
    email: str
    name: str
    type: Literal["personal", "group"]
    groups: List[str]


@router.get("/account/me", tags=["account"], response_model=AccountInfoOutput)
async def get_account_info(current_user: UserToken = Depends(get_current_user)):
    account_type = "group" if user_is_group(current_user.username) else "personal"
    return {
        "username": current_user.username,
        "email": current_user.email,
        "name": current_user.name,
        "type": account_type,
        "groups": current_user.groups,
    }
