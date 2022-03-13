import logging
from fastapi import Depends, HTTPException, status
from . import router

from ocflib.printing.quota import get_connection, get_quota
from ..utils.user import get_current_user


@router.get("/quotas/paper")
async def paper_quota(current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as c:
            quota = get_quota(c, current_user["preferred_username"])
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
