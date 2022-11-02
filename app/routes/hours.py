from datetime import date as date_type
from typing import Optional

from ocflib.lab.hours import HoursListing, read_hours_listing

from fastapi import HTTPException
from pydantic import BaseModel

from routes import router
from utils.cache import periodic


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
