from fastapi import FastAPI

app = FastAPI(title="Chấm Code API")

@app.get("/")
def health_check():
    return {"status":"ok"}
