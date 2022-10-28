import logging
from typing import Callable, Union

from ocflib.account.search import user_is_group

from fastapi import Depends, HTTPException, status

from utils.auth import UserToken, decode_token, oauth2_scheme
from utils.constants import (
    OCFOFFICERS_GROUP,
    OCFROOT_GROUP,
    OCFSTAFF_GROUP,
    OPSTAFF_GROUP,
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserToken:
    try:
        return decode_token(token)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def depends_get_current_user_with_group(
    group: Union[OCFSTAFF_GROUP, OCFOFFICERS_GROUP, OCFROOT_GROUP, OPSTAFF_GROUP],
) -> Callable[[str], UserToken]:
    async def get_current_user_with_group(token: str = Depends(oauth2_scheme)):
        try:
            user_token = decode_token(token)
            if group not in user_token.get("realm_access").get("roles"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid permissions to access resource",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user_token
        except HTTPException:
            raise
        except Exception as e:
            logging.error(e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return get_current_user_with_group


async def get_current_group_user(
    user_token: UserToken = Depends(get_current_user),
) -> UserToken:
    if not user_is_group(user_token["preferred_username"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not a group",
        )

    return user_token
