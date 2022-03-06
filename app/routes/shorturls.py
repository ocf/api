from ocflib.misc.shorturls import get_connection
from ocflib.misc.shorturls import get_shorturl

from fastapi import status
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from . import router


@router.get("/shorturl/{slug}", status_code=status.HTTP_301_MOVED_PERMANENTLY)
async def bounce_shorturl(slug: str):
    if slug:
        with get_connection() as ctx:
            target = get_shorturl(ctx, slug)

        if target:
            return RedirectResponse(
                target, status_code=status.HTTP_301_MOVED_PERMANENTLY
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
