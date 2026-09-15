from fastapi import FastAPI

from app.routers import auth, student
from app.handlers.exception_handlers import register_exception_handlers
app = FastAPI(title="Leet Code UTC2")

app.include_router(student.router)
app.include_router(auth.router)

register_exception_handlers(app)

@app.get("/")
def health_check():
    return {"status": "ok"}
