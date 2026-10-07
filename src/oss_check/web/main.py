from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from oss_check.web.routers.pages import router as pages_router


app = FastAPI(
    title="OSS Dependency License Checker"
)

BASE_DIR = Path(__file__).resolve().parent


app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)


app.include_router(pages_router)