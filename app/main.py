from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router
from utils.config import get_settings

settings = get_settings()

app = FastAPI(
    title="OCF API",
    description="[https://github.com/ocf/api](https://github.com/ocf/api)",
    version=settings.version,
    license_info={
        "name": "GNU GPLv3 and Apache 2.0",
        "url": "https://github.com/ocf/api/blob/master/LICENSE",
    },
    openapi_tags=[
        {"name": "lab_stats"},
        {"name": "lab_hours"},
        {"name": "account"},
        {"name": "misc"},
    ],
)

origins = ["http://localhost:8000", "http://ocf", "https://new.ocf.berkeley.edu"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["misc"])
async def root():
    return {"message": "Welcome to the OCF API!"}


app.include_router(router)

# Some great reference reading: https://github.com/tiangolo/fastapi/issues/12
