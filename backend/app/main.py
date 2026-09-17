from fastapi import FastAPI

from app.handlers.exception_handlers import register_exception_handlers
from app.routers import auth, user

app = FastAPI(title="Leet Code UTC2")

app.include_router(user.router, tags=["users"])
app.include_router(auth.router)

register_exception_handlers(app)


@app.get("/")
def health_check():
    return {"status": "ok"}
