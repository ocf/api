from paramiko import AuthenticationException, SSHClient
from paramiko.hostkeys import HostKeyEntry

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field

from routes import router
from utils.user import get_current_user


class RunCommandInput(BaseModel):
    command: str
    username: str = Field(
        min_length=3,
        max_length=16,
    )
    password: str = Field(
        min_length=8,
        max_length=256,
    )


class RunCommandOutput(BaseModel):
    output: str
    error: str


@router.post("/account/command", tags=["account"], response_model=RunCommandOutput)
def run_command(data: RunCommandInput, _=Depends(get_current_user)):
    ssh = SSHClient()

    host_keys = ssh.get_host_keys()
    entry = HostKeyEntry.from_line(
        "ssh.ocf.berkeley.edu ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAqMkHVVoMl8md25iky7e2Xe3ARaC4H1PbIpv5Y+xT4KOT17gGvFSmfjGyW9P8ZTyqxq560iWdyELIn7efaGPbkUo9retcnT6WLmuh9nRIYwb6w7BGEEvlblBmH27Fkgt7JQ6+1sr5teuABfIMg22WTQAeDQe1jg0XsPu36OjbC7HjA3BXsiNBpxKDolYIXWzOD+r9FxZLP0lawh8dl//O5FW4ha1IbHklq2i9Mgl79wAH3jxf66kQJTvLmalKnQ0Dbp2+vYGGhIjVFXlGSzKsHAVhuVD6TBXZbxWOYoXanS7CC43MrEtBYYnc6zMn/k/rH0V+WeRhuzTnr/OZGJbBBw==",  # noqa
    )
    assert (
        entry is not None
    )  # should never be none as we are passing a static string above
    host_keys.add(
        "ssh.ocf.berkeley.edu",
        "ssh-rsa",
        entry.key,
    )

    try:
        ssh.connect(
            "ssh.ocf.berkeley.edu",
            username=data.username,
            password=data.password,
        )
    except AuthenticationException:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Authentication failed. Did you type the wrong username or password?",
        )

    _, ssh_stdout, ssh_stderr = ssh.exec_command(data.command, get_pty=True)
    output = ssh_stdout.read().decode()
    error = ssh_stderr.read().decode()

    return {"output": output, "error": error}
