from typing import List

from ocflib.org.meeting_hours import (
    read_current_meeting,
    read_meeting_list,
    read_next_meeting,
)

from fastapi import Response, status
from pydantic import BaseModel

from routes import router


class MeetingOutput(BaseModel):
    day: str
    time: str
    subject: str
    short: str
    irl: bool
    virtual: bool


class MeetingsListOutput(BaseModel):
    meetings: List[MeetingOutput]


@router.get("/meetings/list", tags=["meetings"], response_model=MeetingsListOutput)
def get_meetings_list():
    return {"meetings": [item._asdict() for item in read_meeting_list()]}


@router.get("/meetings/next", tags=["meetings"], response_model=MeetingOutput)
def get_next_meeting():
    next_meeting = read_next_meeting()
    if next_meeting is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return next_meeting._asdict()


@router.get("/meetings/current", tags=["meetings"], response_model=MeetingOutput)
def get_current_meeting():
    current_meeting = read_current_meeting()
    if current_meeting is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return current_meeting._asdict()
