import logging

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.middleware.cors import CORSMiddleware

import ocflib.lab.stats as labstats
import ocflib.printing.printers as printstats
import datetime

# Keycloak setup
from keycloak import KeycloakOpenID

keycloak_url = "https://auth.ocf.berkeley.edu/auth/"
realm_name = "ocf"

keycloak_openid = KeycloakOpenID(
    server_url=keycloak_url,
    client_id="ocfapi",
    realm_name=realm_name,
)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{keycloak_url}realms/{realm_name}/protocol/openid-connect/auth",
    tokenUrl=f"{keycloak_url}realms/{realm_name}/protocol/openid-connect/token",
)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        KEYCLOAK_PUBLIC_KEY = (
            "-----BEGIN PUBLIC KEY-----\n"
            + keycloak_openid.public_key()
            + "\n-----END PUBLIC KEY-----"
        )
        return keycloak_openid.decode_token(
            token,
            key=KEYCLOAK_PUBLIC_KEY,
            options={"verify_signature": True, "verify_aud": False, "exp": True},
        )
    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/user")
async def get_user(current_user: dict = Depends(get_current_user)):
    logging.info(current_user)
    return current_user


@app.get("/stats")
async def get_homepage_stats():
    # users = labstats.users_in_lab_count()
    return {
        "Pages Printed": sum(get_pages_today().values()),
        "Mirror Bandwidth": get_weekly_bandwidth(),
        "Hours Farmed": 888,
        "Accounts Created": 13,
    }


def get_weekly_bandwidth():
    """Return the bandwidth used by all mirrors in the previous 7-day period
    This should be in a human-readable format
    """
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    bandwidth = 0
    for tup in labstats.bandwidth_by_dist(week_ago):
        bandwidth += tup[1]
    return labstats.humanize_bytes(bandwidth)


def get_pages_today():
    """Return a dict with the number of pages printed today by each printer"""
    rn = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=-8)))
    with labstats.get_connection() as cursor:
        cursor.execute(
            """
            SELECT max(value) as value, cast(date as date) as date, printer
                FROM printer_pages_public
                GROUP BY cast(date as date), printer
                ORDER BY date ASC, printer ASC
        """
        )
        pages_today = {}
        last_seen = {printer: 0 for printer in printstats.PRINTERS}
        # If it's not today or yesterday, skip the row
        # If it's yesterday, add to last seen
        # If it's today, add to pages_today based on last_seen
        for row in cursor:
            date = row["date"]
            printer = row["printer"]
            if (not (printer in printstats.PRINTERS)) or rn.day - date.day > 1:
                continue
            elif rn.day - date.day == 1:
                last_seen[printer] = row["value"]
            elif rn.day == date.day:
                pages_today[printer] = row["value"] - last_seen[printer]
        return pages_today

        # Stuff from ocfweb, probably not using

        # ~ # Resolves the issue of possible missing dates.
        # ~ # defaultdict(lambda: defaultdict(int))
        # ~ doesn't work due to inability to pickle local objects like lambdas;
        # ~ # this effectively does the same thing as that.
        # ~ pages_printed: Dict[Any, Any] = defaultdict(partial(defaultdict, int))
        # ~ last_seen: Dict[Any, Any] = {}

        # ~ for row in cursor:
        # ~ if row['printer'] in last_seen:
        # ~ pages_printed.setdefault(row['date'], defaultdict(int))
        # ~ pages_printed[row['date']][row['printer']] = (
        # ~ row['value'] - last_seen[row['printer']]
        # ~ )
        # ~ last_seen[row['printer']] = row['value']


# Some great reference reading: https://github.com/tiangolo/fastapi/issues/12
