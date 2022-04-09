from enum import Enum
from functools import partial
from ipaddress import ip_address
from typing import Any, Dict, Optional

from ocflib.infra.hosts import hosts_by_filter
from ocflib.infra.net import ipv4_to_ipv6, is_ocf_ip
from ocflib.lab.stats import get_connection

from fastapi import HTTPException, Request, Response, status
from pydantic import BaseModel

from routes import router
from utils.cache import cache
from utils.config import get_settings

settings = get_settings()

get_connection = partial(
    get_connection,
    user=settings.ocfstats_user,
    password=settings.ocfstats_password,
    db=settings.ocfstats_db,
)


class SessionState(str, Enum):
    active = "active"
    cleanup = "cleanup"


class LogSessionInput(BaseModel):
    state: SessionState
    user: Optional[str] = None


@router.post("/session/log", status_code=status.HTTP_204_NO_CONTENT, tags=["misc"])
def log_session(session: LogSessionInput, request: Request):
    """Primary API endpoint for session tracking.

    Desktops have a cronjob that calls this endpoint: https://git.io/vpIKX
    """

    remote_ip = ip_address(request.client.host)

    if not is_ocf_ip(remote_ip):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        host = _get_desktops().get(remote_ip)

        if not host:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IP {remote_ip} does not belong to a desktop",
            )

        state = session.state
        user = session.user

        if state is SessionState.cleanup or not user:
            # sessions also get periodically cleaned up: https://git.io/vpwg8
            _close_sessions(host)
        elif state is SessionState.active and _session_exists(host, user):
            _refresh_session(host, user)
        else:
            _new_session(host, user)

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)


def _new_session(host: str, user: str) -> None:
    """Register new session in when a user logs into a desktop."""

    _close_sessions(host)

    with get_connection() as c:
        c.execute(
            "INSERT INTO `session` (`host`, `user`, `start`, `last_update`) "
            "VALUES (%s, %s, NOW(), NOW())",
            (host, user),
        )


def _session_exists(host: str, user: str) -> bool:
    """Returns whether an open session already exists for a given host and user."""

    with get_connection() as c:
        c.execute(
            "SELECT COUNT(*) AS `count` FROM `session` "
            "WHERE `host` = %s AND `user` = %s AND `end` IS NULL",
            (host, user),
        )

        return c.fetchone()["count"] > 0


def _refresh_session(host: str, user: str) -> None:
    """Keep a session around if the user is still logged in."""

    with get_connection() as c:
        c.execute(
            "UPDATE `session` SET `last_update` = NOW() "
            "WHERE `host` = %s AND `user` = %s AND `end` IS NULL",
            (host, user),
        )


def _close_sessions(host: str) -> None:
    """Close all sessions for a particular host."""

    with get_connection() as c:
        c.execute(
            "UPDATE `session` SET `end` = NOW(), `last_update` = NOW() "
            "WHERE `host` = %s AND `end` IS NULL",
            (host,),
        )


@cache(600)
def _get_desktops() -> Dict[Any, Any]:
    """Return IPv4 and 6 address to fqdn mapping for OCF desktops from LDAP."""

    desktops = {}
    for e in hosts_by_filter("(type=desktop)"):
        host = e["cn"][0] + ".ocf.berkeley.edu"
        v4 = ip_address(e["ipHostNumber"][0])
        v6 = ipv4_to_ipv6(v4)
        desktops[v4] = host
        desktops[v6] = host
    return desktops
