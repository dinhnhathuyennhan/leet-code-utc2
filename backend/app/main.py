from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402

from app.handlers.exception_handlers import register_exception_handlers  # noqa: E402
from app.routers import auth, user  # noqa: E402

app = FastAPI()

app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(auth.router)

register_exception_handlers(app)


@app.get("/")
def health_check():
    return {"status": "ok"}
