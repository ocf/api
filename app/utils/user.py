import logging

from ocflib.account.search import user_is_group

from fastapi import Depends, HTTPException, status

from utils.auth import UserToken, decode_token, oauth2_scheme


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserToken:
    try:
        return decode_token(token)
    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_group_user(
    user_token: UserToken = Depends(get_current_user),
) -> UserToken:
    if not user_is_group(user_token["preferred_username"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not a group",
        )

    return user_token
