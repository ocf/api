import logging
from fastapi import Depends, HTTPException, status

from .auth import oauth2_scheme, decode_token


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        return decode_token(token)
    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
