import csv
import io
import re
from contextlib import contextmanager
from typing import Any, Collection, Dict, Generator, List, Optional, Tuple

from typing_extensions import Literal

from ocflib.account.validators import validate_password
from ocflib.vhost.mail import (
    MailForwardingAddress,
    crypt_password,
    get_connection,
    vhosts_for_user,
)

from fastapi import Depends, File, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from routes import router
from utils.auth import UserToken
from utils.config import get_settings
from utils.user import get_current_group_user


class REMOVE_PASSWORD:
    """Singleton to represent a password should be removed."""


class InvalidEmailError(ValueError):
    pass


class MailVHost(BaseModel):
    domain: str
    addresses: List[str]
    has_wildcard: bool


class VHostMailOutput(BaseModel):
    vhosts: List[MailVHost]


@router.get("/account/vhost/mail", tags=["account"], response_model=VHostMailOutput)
def vhost_mail(user_token: UserToken = Depends(get_current_group_user)):
    user = user_token["preferred_username"]
    vhosts = []

    with _txn() as c:
        for vhost in sorted(vhosts_for_user(user)):
            addresses = sorted(vhost.get_forwarding_addresses(c))
            vhosts.append(
                {
                    "domain": vhost.domain,
                    "addresses": addresses,
                    "has_wildcard": any(address.is_wildcard for address in addresses),
                }
            )

    return {"vhosts": vhosts}


class VHostMailUpdateInput(BaseModel):
    action: Literal["add", "update", "delete"]
    addr: str
    forward_to: Optional[str]
    password: Optional[str]
    new_addr: Optional[str]


@router.post(
    "/account/vhost/mail", status_code=status.HTTP_204_NO_CONTENT, tags=["account"]
)
def vhost_mail_update(
    data: VHostMailUpdateInput, user_token: UserToken = Depends(get_current_group_user)
):
    user = user_token["preferred_username"]

    # _get_addr may return None, but never with this particular call
    addr_info = _get_addr(data.addr, user, required=True)
    assert addr_info is not None
    addr_name, addr_domain, addr_vhost = addr_info
    addr = (addr_name or "") + "@" + addr_domain

    # These fields are optional; some might be None
    forward_to = _get_forward_to(data.forward_to)

    new_addr = _get_addr(data.new_addr, user, required=False)
    new_addr_name = None
    if new_addr is not None:
        new_addr_name, new_addr_domain, new_addr_vhost = new_addr
        new_addr = (new_addr_name or "") + "@" + new_addr_domain

        # Sanity check: can't move addresses across vhosts
        if new_addr_vhost != addr_vhost:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                'You cannot change an address from "{}" to "{}"!'.format(
                    addr_domain,
                    new_addr_domain,
                ),
            )

    password_hash = _get_password(data.password, new_addr_name or addr_name)

    # Perform the add/update
    with _txn() as c:
        existing = _find_addr(c, addr_vhost, addr)
        new = None

        if data.action == "add":
            if existing is not None:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f'The address "{addr}" already exists!'
                )

            new = MailForwardingAddress(
                address=addr,
                crypt_password=None,
                forward_to=None,
                last_updated=None,
            )
        else:
            if existing is None:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f'The address "{addr}" does not exist!'
                )
            addr_vhost.remove_forwarding_address(c, existing.address)

        if data.action != "delete":
            new = new or existing
            if forward_to:
                new = new._replace(forward_to=forward_to)
            if password_hash is REMOVE_PASSWORD:
                new = new._replace(crypt_password=None)
            elif password_hash:
                new = new._replace(crypt_password=password_hash)
            if new_addr:
                new = new._replace(address=new_addr)

        if new is not None:
            addr_vhost.add_forwarding_address(c, new)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


class VHostMailExportInput(BaseModel):
    domain: str


@router.get("/account/vhost/mail/export", tags=["account"])
def vhost_mail_csv_export(
    data: VHostMailExportInput, user_token: UserToken = Depends(get_current_group_user)
):
    user = user_token["preferred_username"]
    domain = data.domain
    vhost = _get_vhost(user, domain)
    if not vhost:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, f'You cannot use the domain: "{domain}"'
        )

    with _txn() as c:
        addresses = (
            addr
            for addr in sorted(vhost.get_forwarding_addresses(c))
            if not addr.is_wildcard
        )

    return StreamingResponse(_write_csv(addresses), media_type="text/csv")
    # TODO: may need to add this header if the browser doesn't treat response as a file
    # response["Content-disposition"] = f'attachment; filename="{domain}.csv"'


class VHostMailImportInput(BaseModel):
    domain: str


@router.post(
    "/account/vhost/mail/import",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["account"],
)
def vhost_mail_csv_import(
    data: VHostMailImportInput,
    csv_file: bytes = File(None, media_type="text/csv"),
    user_token: UserToken = Depends(get_current_group_user),
):
    user = user_token["preferred_username"]
    domain = data.domain
    vhost = _get_vhost(user, domain)
    if not vhost:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, f'You cannot use the domain: "{domain}"'
        )

    addresses = _parse_csv(csv_file, domain)

    # Add new addresses and update existing if the recipients changed
    with _txn() as c:
        existing_addrs = {
            addr.address: addr for addr in vhost.get_forwarding_addresses(c)
        }

        for from_addr, to_addrs in addresses.items():
            if from_addr in existing_addrs:
                existing_addr = existing_addrs[from_addr]
                if to_addrs != existing_addr.forward_to:
                    new = MailForwardingAddress(
                        address=from_addr,
                        crypt_password=existing_addr.crypt_password,
                        forward_to=to_addrs,
                        last_updated=None,
                    )
                    vhost.remove_forwarding_address(c, from_addr)
                else:
                    new = None
            else:
                new = MailForwardingAddress(
                    address=from_addr,
                    crypt_password=None,
                    forward_to=to_addrs,
                    last_updated=None,
                )

            if new is not None:
                vhost.add_forwarding_address(c, new)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _write_csv(addresses: Generator[Any, None, None]) -> Any:
    """Turn a collection of vhost forwarding addresses into a CSV
    string for user download."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for addr in addresses:
        writer.writerow(
            (
                addr.address.split("@")[0],
                " ".join(sorted(addr.forward_to)),
            )
        )

    return buf.getvalue()


def _parse_csv(csv_file: Optional[bytes], domain: str) -> Dict[str, Any]:
    """Parse, validate, and return addresses from the file uploaded
    with the CSV upload button/form."""
    if not csv_file:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing CSV file!")

    addresses: Dict[str, Collection[Any]] = {}
    try:
        with io.TextIOWrapper(io.BytesIO(csv_file), encoding="utf-8") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                try:
                    if len(row) != 2:
                        raise ValueError("Must have exactly 2 columns")

                    from_addr = row[0] + "@" + domain
                    if _parse_addr(from_addr) is None:
                        raise ValueError(f'Invalid forwarding address: "{from_addr}"')

                    try:
                        to_addrs = _parse_csv_forward_addrs(row[1])
                    except InvalidEmailError as e:
                        raise ValueError(f'Invalid address: "{e}"')

                    addresses[from_addr] = to_addrs
                except ValueError as e:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"Error parsing CSV: row {i + 1}: {e}",
                    )
    except UnicodeDecodeError as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f'Uploaded file is not valid UTF-8 encoded: "{e}"',
        )

    return addresses


def _parse_csv_forward_addrs(string: str) -> Collection[Any]:
    """Parse and validate emails from a commas-and-whitespace separated
    list string."""
    # Allow any combination of whitespace and , as separators
    to_addrs = re.split(r"(?:\s|,)+", string)
    if to_addrs[-1] == "":
        # Allow trailing comma
        to_addrs = to_addrs[:-1]
    if not to_addrs:
        raise ValueError("Missing forward-to address")
    for to_addr in to_addrs:
        if _parse_addr(to_addr) is None:
            raise InvalidEmailError(to_addr)

    return frozenset(to_addrs)


def _parse_addr(addr: str, allow_wildcard: bool = False) -> Optional[Tuple[str, str]]:
    """Safely parse an email, returning first component and domain."""
    m = re.match(
        (
            r"([a-zA-Z0-9\-_\+\.]+)"
            + ("?" if allow_wildcard else "")
            + r"@([a-zA-Z0-9\-_\+\.]+)$"
        ),
        addr,
    )
    if not m:
        return None
    name, domain = m.group(1), m.group(2)
    if "." in domain:
        return name, domain

    return None


def _get_addr(
    original: Optional[str], user: Any, required: bool = True
) -> Optional[Tuple[Any, Any, Any]]:
    if original is not None:
        addr = original.strip()
        parsed = _parse_addr(addr, allow_wildcard=True)
        if not parsed:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, f'Invalid address: "{original}"'
            )
        else:
            name, domain = parsed

            # Make sure that user can use this domain
            vhost = _get_vhost(user, domain)
            if vhost is not None:
                return name, domain, vhost
            else:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, f'You cannot use the domain: "{domain}"'
                )
    elif required:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You must provide an address!")

    return None


def _get_forward_to(forward_to: Optional[str]) -> Optional[Collection[Any]]:
    if forward_to is None:
        return None

    # Validate each email in the list
    parsed_addrs = set()
    for forward_addr in forward_to.split(","):
        # Strip whitespace and ignore empty, because people suck at forms.
        forward_addr = forward_addr.strip()
        if forward_addr != "":
            if _parse_addr(forward_addr) is not None:
                parsed_addrs.add(forward_addr)
            else:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f'Invalid forwarding address: "{forward_addr}"',
                )

    if len(parsed_addrs) < 1:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "You must provide at least one address to forward to!",
        )

    return frozenset(parsed_addrs)


def _get_password(password: Optional[str], addr_name: Optional[str]) -> Any:
    # If addr_name is None, then this is a wildcard address, and those can't
    # have passwords.
    if addr_name is None:
        return REMOVE_PASSWORD

    if password is not None:
        password = password.strip()
        if not password:
            return REMOVE_PASSWORD
        try:
            validate_password(addr_name, password, strength_check=True)
        except ValueError as ex:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                ex.args[0],
            )
        else:
            return crypt_password(password)


def _get_vhost(user: str, domain: str) -> Any:
    vhosts = vhosts_for_user(user)
    for vhost in vhosts:
        if vhost.domain == domain:
            return vhost


def _find_addr(c: Any, vhost: Any, addr: str) -> Any:
    for addr_obj in vhost.get_forwarding_addresses(c):
        if addr_obj.address == addr:
            return addr_obj


settings = get_settings()


@contextmanager
def _txn(**kwargs: Any) -> Generator[Any, None, None]:
    with get_connection(
        user=settings.OCFMAIL_USER,
        password=settings.OCFMAIL_PASSWORD,
        db=settings.OCFMAIL_DB,
        autocommit=False,
        **kwargs,
    ) as c:
        try:
            yield c
        except Exception:
            c.connection.rollback()
            raise
        else:
            c.connection.commit()
