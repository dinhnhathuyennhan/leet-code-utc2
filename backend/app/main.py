import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from app.seed_data import seed_users

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from app.handlers.exception_handlers import register_exception_handlers  # noqa: E402
from app.routers import auth, student, course, user  # noqa: E402

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_users()
    yield
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(course.router)
app.include_router(student.router)

register_exception_handlers(app)


@app.get("/")
def health_check():
    return {"status": "ok"}
