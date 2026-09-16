from fastapi import FastAPI

from app.routers import user

app = FastAPI(title="Leet Code UTC2")

app.include_router(user.router, prefix="/users", tags=["users"])


@app.get("/")
def health_check():
    return {"status":"ok"}
