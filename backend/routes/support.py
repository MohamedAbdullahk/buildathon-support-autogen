from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.support_service import SupportResult, run_support_query
from backend.utils.logger import logger

router = APIRouter()


class SupportRequest(BaseModel):
    query: str = Field(
        ...,
        description="The customer's question or task",
        examples=["How do I reset my password?"],
    )


@router.post("", response_model=SupportResult)
async def support_endpoint(request: SupportRequest):
    """Run the 3-agent support team (Assistant -> Web Search -> Entry Agent)."""
    try:
        return await run_support_query(request.query)
    except Exception as e:
        logger.error(f"/api/v1/support failed | error={e}")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while processing your query. Please try again.",
        )