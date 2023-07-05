from datetime import datetime

from pytz import timezone
from sqlalchemy.orm import Session

from db.models import CoffeeHouseBranch, Worktime, DaysOfWeek
from menu.schemas import CoffeeHouseBranchWorktime


def coffee_house_branch_worktime_today(
        branch: CoffeeHouseBranch,
        db: Session
) -> CoffeeHouseBranchWorktime:
    """
    Calculates the working time of the coffee house branch and returns it
    :param branch: instance of CoffeeHouseBranch
    :param db: sqlalchemy session
    :return: pydantic class with open_time, close_time
    """
    weekday = datetime.now(tz=timezone('Asia/Vladivostok')).weekday()
    worktime: Worktime = db.query(Worktime).filter(
        Worktime.coffee_house_branch_id == branch.id,
        Worktime.day_of_week == DaysOfWeek(weekday)
    ).one_or_none()

    if worktime is None or (not branch.is_active):
        return CoffeeHouseBranchWorktime(open_time=None, close_time=None)
    else:
        return CoffeeHouseBranchWorktime(
            open_time=worktime.open_time,
            close_time=worktime.close_time
        )
