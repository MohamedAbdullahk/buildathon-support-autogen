from fastapi import FastAPI

from backend.routes import health, support
from backend.utils.logger import logger

app = FastAPI(
    title="Multi-Agent Customer Support API",
    description="AutoGen team: Assistant -> Web Search Assistant -> Entry Agent",
    version="2.0.0",
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(support.router, prefix="/api/v1/support", tags=["Support"])

logger.info("FastAPI app initialised")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)