from fastapi import FastAPI

from app.routers import student

app = FastAPI(title="Leet Code UTC2")

app.include_router(student.router)

@app.get("/")
def health_check():
    return {"status":"ok"}
