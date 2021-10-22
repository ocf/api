from ocflib.lab.hours import read_hours_listing

from . import router


@router.get("/hours/today")
def get_hours_today():
    return read_hours_listing().hours_on_date()[0]
