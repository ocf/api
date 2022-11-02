from typing import List

from ocflib.lab.staff_hours import get_staff_hours as real_get_staff_hours

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


@router.get("/staff_hours", tags=["misc"], response_model=StaffHoursOutput)
async def get_staff_hours():
    return {"staff_hours": _get_staff_hours()}
