from fastapi import FastAPI

from app.routers import admin, progress, public

app = FastAPI(title="Finedu API")
app.include_router(public.router)
app.include_router(progress.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
