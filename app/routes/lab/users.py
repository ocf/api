from datetime import datetime
from typing import List, Optional

from ocflib.lab.stats import staff_in_lab as real_staff_in_lab
from ocflib.lab.stats import users_in_lab_count as real_users_in_lab_count

from pydantic import BaseModel

from routes import router


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
