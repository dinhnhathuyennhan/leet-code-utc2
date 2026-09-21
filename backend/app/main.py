from contextlib import asynccontextmanager

from dotenv import load_dotenv

from app.seed_data import seed_users

load_dotenv()

from fastapi import FastAPI  # noqa: E402

from app.handlers.exception_handlers import register_exception_handlers  # noqa: E402
from app.routers import auth, course, user  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_users()
    yield
app = FastAPI(lifespan=lifespan)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(course.router)

register_exception_handlers(app)


@app.get("/")
def health_check():
    return {"status": "ok"}
