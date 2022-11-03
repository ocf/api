import datetime
import socket
from textwrap import dedent
from typing import Optional

from ocflib.account.search import user_attrs
from ocflib.misc.mail import send_mail
from ocflib.misc.validators import host_exists, valid_email
from ocflib.misc.whoami import current_user_formatted_email
from ocflib.vhost.web import eligible_for_vhost, has_vhost

from fastapi import Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from routes import router
from utils.auth import UserToken
from utils.config import get_settings
from utils.user import get_current_user


class VHostRequestInput(BaseModel):
    subdomain: str = Field(
        min_length=1, max_length=32, regex=r"^([a-zA-Z0-9]+\.)+[a-zA-Z0-9]{2,}$"
    )
    name: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=1, max_length=64)
    position: str = Field(min_length=1, max_length=64)
    comments: Optional[str] = Field(min_length=1, max_length=1024)


@router.post(
    "/account/hosting/vhost",
    tags=["account"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {},
        status.HTTP_403_FORBIDDEN: {},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {},
    },
)
def request_vhost(
    data: VHostRequestInput,
    request: Request,
    user_token: UserToken = Depends(get_current_user),
):
    user = user_token.username

    if has_vhost(user):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Account {user} already has virtual hosting",
        )

    if not eligible_for_vhost(user):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Account {user} is not eligible for virtual hosting",
        )

    if host_exists(data.subdomain):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Requested subdomain already exists"
        )

    if not valid_email(data.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid email")

    # send email to hostmaster@ocf and redirect to success page
    attrs = user_attrs(user)
    ip_addr = str(request.client)

    try:
        ip_reverse = socket.gethostbyaddr(str(request.client))[0]
    except (socket.herror, socket.gaierror):
        ip_reverse = "unknown"

    subject = "Virtual Hosting Request: {} ({})".format(
        data.subdomain,
        user,
    )
    message = dedent(
        """\
        Virtual Hosting Request:
            - OCF Account: {user}
            - OCF Account Title: {title}
            - Requested Subdomain: {requested_subdomain}
            - Current URL: https://www.ocf.berkeley.edu/~{user}/

        Comments/Special Requests:
        {comments}

        Requested by:
            - Name: {your_name}
            - Position: {your_position}
            - Email: {your_email}
            - IP Address: {ip_addr} ({ip_reverse})
            - User Agent: {user_agent}

        --------
        Request submitted to ocfapi ({hostname}) on {now}.
        {full_path}"""
    ).format(
        user=user,
        title=attrs["cn"][0],
        requested_subdomain=data.subdomain,
        comments=data.comments,
        your_name=data.name,
        your_position=data.position,
        your_email=data.email,
        ip_addr=ip_addr,
        ip_reverse=ip_reverse,
        user_agent=request.headers.get("User-agent"),
        now=datetime.datetime.now().strftime(
            "%A %B %e, %Y @ %I:%M:%S %p",
        ),
        hostname=socket.gethostname(),
        full_path=request.url,
    )

    try:
        settings = get_settings()
        send_mail(
            "hostmaster@ocf.berkeley.edu"
            if not settings.debug
            else current_user_formatted_email(),
            subject,
            message,
            sender=data.email,
        )
    except Exception as ex:
        # TODO: report via ocflib
        print(ex)
        print("Failed to send vhost request email!")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "We were unable to submit your virtual hosting "
            + "request. Please try again or email us at "
            + "hostmaster@ocf.berkeley.edu",
        )
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
