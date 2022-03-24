from fastapi import Cookie, HTTPException, status, Header
from fastapi.responses import RedirectResponse
from ocflib.ucb.cas import CAS_URL, verify_ticket
from utils.calnet import create_calnet_jwt, get_calnet_service_url
from urllib.parse import urljoin, quote_plus
from typing import Optional

from . import router


@router.get("/login/calnet", tags=["account"])
async def calnet_login(
    next: Optional[str] = None,
    ticket: Optional[str] = None,
    calnet_redirect_url: Optional[str] = Cookie(None),
    host: Optional[str] = Header(None),
):
    if next:
        response = RedirectResponse(
            urljoin(
                CAS_URL, f"login?service={quote_plus(get_calnet_service_url(host))}"
            )
        )
        response.set_cookie("calnet_redirect_url", next)
        return response
    if ticket:
        uid = verify_ticket(ticket, get_calnet_service_url(host))
        if not uid:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "got bad ticket")
        jwt = create_calnet_jwt(uid)
        if calnet_redirect_url:
            response = RedirectResponse(
                calnet_redirect_url, headers={"calnet_jwt": jwt}
            )
            response.delete_cookie("calnet_redirect_url")
            return response
        else:
            return {"calnet_jwt": jwt}
    raise HTTPException(
        status.HTTP_400_BAD_REQUEST, "no redirect url or ticket in request"
    )
