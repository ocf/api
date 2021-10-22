from ocflib.misc.shorturls import get_connection
from ocflib.misc.shorturls import get_shorturl

from fastapi import Response, status
from fastapi.responses import RedirectResponse
from . import router


@router.get("/shorturl/{slug}", status_code=status.HTTP_301_MOVED_PERMANENTLY)
def bounce_shorturl(slug: str, response: Response):
    if slug:
        with get_connection() as ctx:
            target = get_shorturl(ctx, slug)

        if target:
            return RedirectResponse(target)

    response.status_code = status.HTTP_404_NOT_FOUND
