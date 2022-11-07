import logging

from typing_extensions import Literal

from ocflib.account.search import user_is_group

from fastapi import Depends, HTTPException, status

from utils.auth import UserToken, decode_token, oauth2_scheme


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
    group: Literal["ocfstaff", "ocfofficers", "ocfroot", "opstaff"],
):
    async def get_current_user_with_group(
        user_token: UserToken = Depends(get_current_user),
    ):
        if group not in user_token.groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid permissions to access resource",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_token

    return get_current_user_with_group


async def get_current_group_user(
    user_token: UserToken = Depends(get_current_user),
) -> UserToken:
    if not user_is_group(user_token.username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not a group",
        )

    return user_token
