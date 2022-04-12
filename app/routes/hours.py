from datetime import date as date_type
from typing import List, Optional

from ocflib.lab.hours import HoursListing, read_hours_listing
from ocflib.lab.staff_hours import get_staff_hours as real_get_staff_hours

from fastapi import HTTPException
from pydantic import BaseModel

from routes import router
from utils.cache import periodic


class StaffHourStaff(BaseModel):
    user_name: str
    real_name: str
    position: str


class StaffHour(BaseModel):
    day: str
    time: str
    staff: List[StaffHourStaff]
    cancelled: bool


class StaffHoursOutput(BaseModel):
    staff_hours: List[StaffHour]


@periodic(60)
def _get_staff_hours() -> List[StaffHour]:
    staff_hours: List[StaffHour] = []
    for h in real_get_staff_hours():
        staff_hour = h._asdict()
        staff_hour["staff"] = [s._asdict() for s in h.staff]
        staff_hours.append(staff_hour)
    return staff_hours


@router.get("/hours/staff", tags=["lab_hours"], response_model=StaffHoursOutput)
async def get_staff_hours():
    return {"staff_hours": _get_staff_hours()}


@periodic(60)
def get_hours_listing() -> HoursListing:
    return read_hours_listing()


class HoursOutput(BaseModel):
    open: Optional[str]
    close: Optional[str]


@router.get("/hours/today", tags=["lab_hours"], response_model=HoursOutput)
async def get_hours_today():
    return _get_hours_date()


@router.get("/hours/{date}", tags=["lab_hours"], response_model=HoursOutput)
async def get_hours_date(date: str):
    try:
        # date formatted as ISO 8601 (e.g. 2022-02-22)
        parsed_date = date_type.fromisoformat(date)
        return _get_hours_date(parsed_date)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid date format (expected ISO 8601)"
        )


def _get_hours_date(date: Optional[date_type] = None):
    hours_listing = get_hours_listing().hours_on_date(date)
    if len(hours_listing) == 0:
        return {}
    hours = hours_listing[0]
    return {"open": str(hours.open), "close": str(hours.close)}
