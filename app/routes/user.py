from fastapi import Depends
from . import router

from ..utils.user import get_current_user


@router.get("/user")
async def get_user(current_user: dict = Depends(get_current_user)):
    return current_user
