from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.router import api_router

app = FastAPI(title="Sales System", version="0.1.0")
app.include_router(api_router, prefix="/api")


@app.exception_handler(ValueError)
async def value_error_handler(_request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
