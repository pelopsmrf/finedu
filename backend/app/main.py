from fastapi import FastAPI

from app.routers import public

app = FastAPI(title="Finedu API")
app.include_router(public.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
