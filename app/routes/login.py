from fastapi import Response, Cookie
from fastapi.responses import RedirectResponse
from ocflib.ucb.cas import CAS_URL, verify_ticket
from utils.calnet import SERVICE_URL, create_calnet_jwt
import urllib.parse
from typing import Optional

from . import router


@router.get("/login/calnet")
async def calnet_login(
    next: str,
    ticket: str,
    response: Response,
    calnet_redirect_url: Optional[str] = Cookie(None),
):
    if next:
        response.set_cookie("calnet_redirect_url", next)
        return RedirectResponse(
            CAS_URL + f"login?service={urllib.parse.quote(SERVICE_URL)}"
        )  # TODO: get the current host from the raw request to redirect back to
    if ticket:
        uid = verify_ticket(ticket, SERVICE_URL)
        jwt = create_calnet_jwt(uid)
        if calnet_redirect_url:
            return RedirectResponse(calnet_redirect_url, headers={"calnet_jwt": jwt})
        else:
            return {"calnet_jwt": jwt}
