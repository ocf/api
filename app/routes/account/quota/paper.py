import logging
from datetime import datetime
from functools import partial

from ocflib.printing.quota import Refund, add_refund, get_connection, get_quota

from fastapi import Depends, HTTPException, Response, status
from pydantic import BaseModel

from routes import router
from utils.auth import UserToken
from utils.config import get_settings
from utils.constants import OCFSTAFF_GROUP
from utils.user import depends_get_current_user_with_group, get_current_user

settings = get_settings()

get_connection = partial(
    get_connection,
    user=settings.ocfprinting_user,
    password=settings.ocfprinting_password,
    db=settings.ocfprinting_db,
)


class PaperQuotaOutput(BaseModel):
    user: str
    daily: int
    semesterly: int


@router.get("/account/quota/paper", tags=["account"], response_model=PaperQuotaOutput)
async def get_paper_quota(current_user: UserToken = Depends(get_current_user)):
    try:
        with get_connection().cursor() as c:
            quota = get_quota(c, current_user.username)
            return {
                "user": quota.user,
                "daily": quota.daily,
                "semesterly": quota.semesterly,
            }

    except (KeyError, ValueError) as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unknown error occured",
            headers={"WWW-Authenticate": "Bearer"},
        )


class PaperRefundInput(BaseModel):
    username: str
    pages: int
    reason: str


@router.post(
    "/account/quota/paper",
    tags=["account"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_paper_refund(
    refund: PaperRefundInput,
    current_user: UserToken = Depends(
        depends_get_current_user_with_group(OCFSTAFF_GROUP)
    ),
):
    try:
        with get_connection().cursor() as c:
            add_refund(
                c,
                Refund(
                    user=refund.username,
                    time=datetime.now(),
                    pages=refund.pages,
                    staffer=current_user.username,
                    reason=refund.reason,
                ),
            )
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    except (KeyError, ValueError) as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unknown error occured",
            headers={"WWW-Authenticate": "Bearer"},
        )
