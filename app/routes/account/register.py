from typing import List, Optional

from Crypto.PublicKey import RSA

import ocflib.ucb.directory as directory
from ocflib.account import search
from ocflib.account.creation import (
    CREATE_PUBLIC_KEY,
    NewAccountRequest,
    encrypt_password,
    valid_email,
    validate_password,
    validate_username,
)
from ocflib.account.search import user_attrs_ucb
from ocflib.account.submission import NewAccountResponse
from ocflib.ucb.groups import group_by_oid, groups_by_student_signat

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field

from routes import router
from utils.calnet import get_calnet_uid
from utils.celery import celery_app, validate_then_create_account
from utils.constants import TEST_GROUP_ACCOUNTS, TESTER_CALNET_UIDS


class RegisterAccountInput(BaseModel):
    account_association: int = Field(
        description="CalNet UID/CalLink OID of entity to create account for"
    )
    username: str
    password: str
    contact_email: str


class RegisterAccountOutput(BaseModel):
    status: str
    task_id: str


@router.post(
    "/account/register", tags=["account"], response_model=RegisterAccountOutput
)
async def register_account(
    data: RegisterAccountInput,
    calnet_uid=Depends(get_calnet_uid),
):
    existing_accounts = search.users_by_calnet_uid(calnet_uid)
    groups_for_user = groups_by_student_signat(calnet_uid)

    eligible_new_group_accounts, existing_group_accounts = {}, {}
    for group_oid in groups_for_user:
        if not group_by_oid(group_oid)["accounts"] or group_oid in [
            group[0] for group in TEST_GROUP_ACCOUNTS
        ]:
            eligible_new_group_accounts[group_oid] = groups_for_user[group_oid]
        else:
            existing_group_accounts[group_oid] = groups_for_user[group_oid]

    if (
        existing_accounts
        and not eligible_new_group_accounts
        and calnet_uid not in TESTER_CALNET_UIDS
    ):
        return {
            "state": "You already have an account",
            "account": ", ".join(existing_accounts),
            "calnet_uid": calnet_uid,
        }

    # ensure we can even find them in university LDAP
    # (alumni etc. might not be readable in LDAP but can still auth via CalNet)
    if not user_attrs_ucb(calnet_uid):
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Unable to read account information"
        )

    if not valid_email(data.contact_email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid email")

    if not validate_password(data.username, data.password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid password")

    real_name = directory.name_by_calnet_uid(calnet_uid)

    association_choices = []
    if not existing_accounts or calnet_uid in TESTER_CALNET_UIDS:
        association_choices.append((calnet_uid, real_name))
    for group_oid, group in eligible_new_group_accounts.items():
        association_choices.append((group_oid, group["name"]))

    is_group_account = data.account_association != calnet_uid
    if is_group_account:
        if not validate_username(
            data.username,
            eligible_new_group_accounts[data.account_association]["name"],
        ):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid username")
        req = NewAccountRequest(
            user_name=data.username,
            real_name=eligible_new_group_accounts[data.account_association]["name"],
            is_group=True,
            calnet_uid=None,
            callink_oid=data.account_association,
            email=data.contact_email,
            encrypted_password=encrypt_password(
                data.password,
                RSA.importKey(CREATE_PUBLIC_KEY),
            ),
            handle_warnings=NewAccountRequest.WARNINGS_WARN,
        )
    else:
        if not validate_username(data.username, real_name):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid username")
        req = NewAccountRequest(
            user_name=data.username,
            real_name=real_name,
            is_group=False,
            calnet_uid=calnet_uid,
            callink_oid=None,
            email=data.contact_email,
            encrypted_password=encrypt_password(
                data.password,
                RSA.importKey(CREATE_PUBLIC_KEY),
            ),
            handle_warnings=NewAccountRequest.WARNINGS_WARN,
        )

    task = validate_then_create_account.delay(req)
    task.wait(timeout=5)

    if isinstance(task.result, NewAccountResponse):
        if task.result.status == NewAccountResponse.REJECTED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, task.result.errors)
        elif task.result.status == NewAccountResponse.FLAGGED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, task.result.errors)
        elif task.result.status == NewAccountResponse.PENDING:
            return {"status": "pending", "task_id": task.result}
        else:
            raise AssertionError("Unexpected state reached")
    else:
        # validation was successful, the account is being created now
        return {"status": "success", "task_id": task.result}


class RegisterAccountStatusOutput(BaseModel):
    state: str
    status: Optional[List[str]]
    message: Optional[str]


@router.get(
    "/account/register/status",
    tags=["account"],
    response_model=RegisterAccountStatusOutput,
)
def register_account_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    if not task.ready():
        meta = task.info
        status_steps = ["Starting creation"]
        if isinstance(meta, dict) and "status" in meta:
            status_steps.extend(meta["status"])
        return {"state": "pending", "status": status_steps}
    elif isinstance(task.result, NewAccountResponse):
        if task.result.status == NewAccountResponse.CREATED:
            return {"state": "success"}
        elif task.result.status == NewAccountResponse.PENDING:
            return {"state": "pending", "message": "requires staff approval"}
        elif task.result.status == NewAccountResponse.FLAGGED:
            return {
                "state": "flagged",
                "message": "there were some warnings when creating your account",
            }
        elif task.result.status == NewAccountResponse.REJECTED:
            return {
                "state": "rejected",
                "message": "account not created due to fatal error",
            }
    elif isinstance(task.result, Exception):
        return {"state": "unknown", "message": task.result}

    raise HTTPException(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Account was unable to be created for unknown reasons",
    )
