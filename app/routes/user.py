from fastapi import Depends
from fastapi.responses import JSONResponse

from routes import router
from utils.auth import RawUserToken, UserToken
from utils.user import get_current_user


@router.get("/user", tags=["account"], response_model=RawUserToken)
async def get_user(current_user: UserToken = Depends(get_current_user)):
    return JSONResponse(content=current_user.raw)  # will bypass output field limiting
