import pexpect

import ocflib.account.validators as validators

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from routes import router


class RenewPasswordInput(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=16,
    )
    old_password: str = Field(
        min_length=5,
        max_length=256,
    )
    new_password: str = Field(
        min_length=12,
        max_length=256,
    )


class RenewPasswordOutput(BaseModel):
    output: str


@router.post(
    "/account/renew-password", tags=["account"], response_model=RenewPasswordOutput
)
def renew_password(data: RenewPasswordInput):
    try:
        validators.validate_username(data.username)
        validators.validate_password(
            data.username, data.old_password, strength_check=False
        )
        validators.validate_password(
            data.username, data.new_password, strength_check=True
        )
    except ValueError as ex:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(ex))
    cmd = "kinit --no-forwardable -l0 {}@OCF.BERKELEY.EDU".format(data.username)
    child = pexpect.spawn(cmd, timeout=10)
    child.expect("{}@OCF.BERKELEY.EDU's Password:".format(data.username))
    child.sendline(data.old_password)
    try:
        result = child.expect(["incorrect", "unknown", pexpect.EOF, "expired"])
        if result == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
            )
        elif result == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown user"
            )
        elif result == 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Password not expired"
            )
        else:
            child.sendline(data.new_password)
            child.expect("\r\nRepeat new password:")
            child.sendline(data.new_password)
            child.expect("\r\nSuccess: Password changed\r\n")
            output = "Password successfully updated!"
    except pexpect.exceptions.TIMEOUT:
        raise HTTPException(
            status_code=400, detail="Please double check your credentials"
        )

    return {"output": output}
