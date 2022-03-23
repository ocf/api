from fastapi import Cookie, HTTPException, status
from fastapi.responses import RedirectResponse
from ocflib.ucb.cas import CAS_URL, verify_ticket
from utils.calnet import SERVICE_URL, create_calnet_jwt
import urllib.parse
from typing import Optional

from . import router


@router.get("/login/calnet")
async def calnet_login(
    next: Optional[str] = None,
    ticket: Optional[str] = None,
    calnet_redirect_url: Optional[str] = Cookie(None),
):
    if next:
        response = RedirectResponse(
            CAS_URL + f"login?service={urllib.parse.quote_plus(SERVICE_URL)}"
        )  # TODO: get the current host from the raw request to redirect back to
        response.set_cookie("calnet_redirect_url", next)
        return response
    if ticket:
        uid = verify_ticket(ticket, SERVICE_URL)
        if not uid:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "got bad ticket")
        jwt = create_calnet_jwt(uid)
        if calnet_redirect_url:
            return RedirectResponse(calnet_redirect_url, headers={"calnet_jwt": jwt})
        else:
            return {"calnet_jwt": jwt}
    raise HTTPException(
        status.HTTP_400_BAD_REQUEST, "no redirect url or ticket in request"
    )
