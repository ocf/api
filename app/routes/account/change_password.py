from typing import Any, Iterator, List
from ocflib.account.search import users_by_calnet_uid
from ocflib.ucb.groups import groups_by_student_signat
from ocflib.ucb.directory import name_by_calnet_uid
from requests.exceptions import ReadTimeout

from fastapi import Depends, HTTPException, status, Response
from pydantic import BaseModel

from utils.calnet import get_calnet_uid
from utils.constants import TESTER_CALNET_UIDS, TEST_OCF_ACCOUNTS
from utils.celery import (
    change_password as change_password_task,
)

from routes import router

CALLINK_ERROR_MSG = (
    "Couldn't connect to CalLink API. Resetting group "
    "account passwords online is unavailable."
)


class ChangePasswordInput(BaseModel):
    account: str
    new_password: str


@router.post(
    "/account/change-password",
    tags=["account"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {},
        status.HTTP_403_FORBIDDEN: {},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {},
    },
)
async def change_password(
    data: ChangePasswordInput, calnet_uid=Depends(get_calnet_uid)
):
    accounts = get_accounts_for(calnet_uid)
    try:
        accounts += get_accounts_signatory_for(calnet_uid)
    except (ConnectionError, ReadTimeout):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, CALLINK_ERROR_MSG)

    if not accounts:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"No accounts found for CalNet UID {calnet_uid}",
        )

    if data.account not in accounts:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"CalNet UID {calnet_uid} is not authorized for account {data.account}",
        )

    try:
        calnet_name = name_by_calnet_uid(calnet_uid)
        task = change_password_task.delay(
            data.account,
            data.new_password,
            comment=f"Your password was reset online by {calnet_name}.",
        )
        result = task.wait(timeout=10)
        if isinstance(result, Exception):
            raise result
    except ValueError as ex:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(ex))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def get_accounts_signatory_for(calnet_uid: str) -> List[str]:
    def flatten(lst: Iterator[Any]) -> List[Any]:
        return [item for sublist in lst for item in sublist]

    group_accounts = flatten(
        map(
            lambda group: group["accounts"],
            groups_by_student_signat(calnet_uid).values(),
        ),
    )

    # sanity check since we don't trust CalLink API that much:
    # if >= 10 groups, can't change online, sorry
    assert len(group_accounts) < 10, "should be less than 10 group accounts"

    return group_accounts


def get_accounts_for(calnet_uid: str) -> List[str]:
    accounts = users_by_calnet_uid(calnet_uid)

    if calnet_uid in TESTER_CALNET_UIDS:
        # these test accounts don't have to exist in in LDAP
        accounts.extend(TEST_OCF_ACCOUNTS)

    return accounts
