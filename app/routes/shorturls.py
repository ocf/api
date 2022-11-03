from ocflib.misc.shorturls import get_connection, get_shorturl

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse

from routes import router


@router.get(
    "/shorturls/bounce/{slug}",
    status_code=status.HTTP_308_PERMANENT_REDIRECT,
    tags=["shorturls"],
)
async def bounce_shorturl(slug: str):
    if slug:
        with get_connection() as ctx:
            target = get_shorturl(ctx, slug)

        if target:
            return RedirectResponse(
                target, status_code=status.HTTP_308_PERMANENT_REDIRECT
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
