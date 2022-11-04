from typing import Optional
from urllib.parse import quote_plus, urljoin

from ocflib.ucb.cas import CAS_URL, verify_ticket

from fastapi import Cookie, Header, HTTPException, status
from fastapi.responses import RedirectResponse

from routes import router
from utils.calnet import create_calnet_jwt, get_calnet_service_url


@router.get("/auth/calnet", tags=["auth"])
async def calnet_login(
    next: Optional[str] = None,
    host: str = Header(None),
):
    response = RedirectResponse(
        urljoin(CAS_URL, f"login?service={quote_plus(get_calnet_service_url(host))}")
    )
    if next:
        response.set_cookie("calnet_redirect_url", next)
    return response


@router.get("/auth/calnet/callback", tags=["auth"])
async def calnet_login_callback(
    ticket: str,
    calnet_redirect_url: Optional[str] = Cookie(None),
    host: str = Header(None),
):
    uid = verify_ticket(ticket, get_calnet_service_url(host))
    if not uid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "got bad ticket")
    jwt = create_calnet_jwt(uid)
    if calnet_redirect_url:
        response = RedirectResponse(calnet_redirect_url)
        response.delete_cookie("calnet_redirect_url")
        response.set_cookie(
            "ocfapi_calnet_token",
            jwt,
            30 * 60,
            secure=True,
            samesite="Strict",
        )
        return response
    else:
        return {"calnet_token": jwt}
