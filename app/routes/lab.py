from typing import Any
from typing import List
from typing import Set

from ocflib.infra.hosts import hostname_from_domain
from ocflib.lab.stats import get_connection
from ocflib.lab.stats import list_desktops

from . import router


def _list_public_desktops() -> List[Any]:
    return list_desktops(public_only=True)


def _get_desktops_in_use() -> Set[Any]:
    """List which desktops are currently in use."""

    # https://github.com/ocf/ocflib/blob/90f9268a89ac9d53c089ab819c1aa95bdc38823d/ocflib/lab/ocfstats.sql#L70
    # we don't use users_in_lab_count_public because we're looking for
    # desktops in use, and the view does COUNT(DISTINCT users)
    with get_connection() as c:
        c.execute(
            "SELECT * FROM `desktops_in_use_public`;",
        )

    return {hostname_from_domain(session["host"]) for session in c}


@router.get("/lab/desktops")
def desktop_usage():
    public_desktops = _list_public_desktops()

    desktops_in_use = _get_desktops_in_use()
    public_desktops_in_use = desktops_in_use.intersection(public_desktops)

    return {
        "public_desktops_in_use": list(public_desktops_in_use),
        "public_desktops_num": len(public_desktops),
    }
