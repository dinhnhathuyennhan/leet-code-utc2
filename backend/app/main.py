import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

from app.api import testcase

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.core.exception_handlers import register_exception_handlers  # noqa: E402

from app.api.router import api_router  # noqa: E402
from app.seed.seed_data import seed_data  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_data()
    yield


app = FastAPI(lifespan=lifespan)

configured_frontend_url = os.getenv("FRONTEND_URL", "")
frontend_origins = {
    origin.strip()
    for origin in configured_frontend_url.split(",")
    if origin.strip()
}
frontend_origins.update(
    {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

register_exception_handlers(app)


@app.get("/")
def health_check():
    return {"status": "ok"}
