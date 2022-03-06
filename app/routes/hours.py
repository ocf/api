from datetime import date as date_type
from ocflib.lab.hours import read_hours_listing
from ocflib.lab.staff_hours import get_staff_hours as real_get_staff_hours
from fastapi import HTTPException

from . import router


@router.get("/hours/staff")
def get_staff_hours():
    return real_get_staff_hours()


@router.get("/hours/today")
def get_hours_today():
    return read_hours_listing().hours_on_date()[0]


@router.get("/hours/{date}")
def get_hours_date(date: str):
    try:
        # date formatted as ISO 8601 (e.g. 2022-02-22)
        parsed_date = date_type.fromisoformat(date)
        return read_hours_listing().hours_on_date(parsed_date)[0]
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid date format (expected ISO 8601)"
        )
