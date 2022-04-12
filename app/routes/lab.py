from datetime import datetime
from typing import List, Optional, Set

from ocflib.infra.hosts import hostname_from_domain
from ocflib.lab.stats import get_connection, list_desktops
from ocflib.lab.stats import staff_in_lab as real_staff_in_lab
from ocflib.lab.stats import users_in_lab_count as real_users_in_lab_count

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
    with get_connection() as c:
        c.execute(
            "SELECT * FROM `desktops_in_use_public`;",
        )

    return {hostname_from_domain(session["host"]) for session in c}


class DesktopUsageOutput(BaseModel):
    desktops_in_use: List[str]
    desktops_num: int


@router.get("/lab/desktops", tags=["lab_stats"], response_model=DesktopUsageOutput)
async def desktop_usage():
    desktops_in_use = _get_desktops_in_use()
    all_desktops = _list_desktops()

    return {
        "desktops_in_use": list(desktops_in_use),
        "desktops_num": len(all_desktops),
    }


class NumUsersOutput(BaseModel):
    num_users: int


@router.get("/lab/num_users", tags=["lab_stats"], response_model=NumUsersOutput)
async def get_num_users_in_lab():
    return {"num_users": real_users_in_lab_count()}


class StaffSession(BaseModel):
    user: str
    host: str
    start: datetime
    end: Optional[datetime]


class StaffInLabOutput(BaseModel):
    staff_in_lab: List[StaffSession]


@router.get("/lab/staff", tags=["lab_stats"], response_model=StaffInLabOutput)
async def get_staff_in_lab():
    return {"staff_in_lab": [s._asdict() for s in real_staff_in_lab()]}
