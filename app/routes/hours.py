from datetime import date as date_type
from typing import Optional

from ocflib.lab.hours import HoursListing, read_hours_listing
from ocflib.lab.staff_hours import get_staff_hours as real_get_staff_hours

from fastapi import HTTPException
from pydantic import BaseModel

from routes import router
from utils.cache import periodic


@periodic(60)
def _get_staff_hours():
    return real_get_staff_hours()


@router.get("/hours/staff", tags=["lab_hours"])
async def get_staff_hours():
    return _get_staff_hours()


@periodic(60)
def get_hours_listing() -> HoursListing:
    return read_hours_listing()


class HoursOutput(BaseModel):
    open: Optional[str]
    close: Optional[str]


@router.get("/hours/today", tags=["lab_hours"], response_model=HoursOutput)
async def get_hours_today():
    hours = get_hours_listing().hours_on_date()
    if len(hours) == 0:
        return {}
    return hours[0]


@router.get("/hours/{date}", tags=["lab_hours"], response_model=HoursOutput)
async def get_hours_date(date: str):
    try:
        # date formatted as ISO 8601 (e.g. 2022-02-22)
        parsed_date = date_type.fromisoformat(date)
        return get_hours_listing().hours_on_date(parsed_date)[0]
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid date format (expected ISO 8601)"
        )
