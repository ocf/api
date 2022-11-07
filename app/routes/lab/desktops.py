from typing import List, Set

from ocflib.infra.hosts import hostname_from_domain
from ocflib.lab.stats import get_connection, list_desktops

from pydantic import BaseModel

from routes import router
from utils.cache import cache, periodic


@cache()
def _list_public_desktops() -> List[str]:
    return list_desktops(public_only=True)


@cache()
def _list_desktops() -> List[str]:
    return list_desktops()


@periodic(5)
def _get_desktops_in_use() -> Set[str]:
    """List which desktops are currently in use."""

    # https://github.com/ocf/ocflib/blob/90f9268a89ac9d53c089ab819c1aa95bdc38823d/ocflib/lab/ocfstats.sql#L70
    # we don't use users_in_lab_count_public because we're looking for
    # desktops in use, and the view does COUNT(DISTINCT users)
    with get_connection().cursor() as c:
        c.execute(
            "SELECT * FROM `desktops_in_use_public`;",
        )

    return {hostname_from_domain(session["host"]) for session in c}  # type: ignore


class DesktopUsageOutput(BaseModel):
    all_desktops_in_use: List[str]
    all_desktops_num: int
    public_desktops_in_use: List[str]
    public_desktops_num: int


@router.get("/lab/desktops", tags=["lab_stats"], response_model=DesktopUsageOutput)
async def desktop_usage():
    desktops_in_use = _get_desktops_in_use()
    all_desktops = _list_desktops()
    public_desktops = _list_public_desktops()
    public_desktops_in_use = desktops_in_use.intersection(public_desktops)

    return {
        "all_desktops_in_use": list(desktops_in_use),
        "all_desktops_num": len(all_desktops),
        "public_desktops_in_use": list(public_desktops_in_use),
        "public_desktops_num": len(public_desktops),
    }
