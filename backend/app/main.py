from fastapi import FastAPI

app = FastAPI(title="Finedu API")


@app.get("/api/health")
def health():
    return {"status": "ok"}
