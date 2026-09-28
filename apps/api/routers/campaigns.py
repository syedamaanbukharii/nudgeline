"""Campaigns API router."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, UUID4

router = APIRouter(prefix="/v1/campaigns", tags=["campaigns"])


class CampaignCreateSchema(BaseModel):
    name: str
    mode: str
    voice_config: dict = {}
    calling_window: dict = {}


@router.post("")
async def create_campaign(req: Request, data: CampaignCreateSchema):
    """Create a new outbound campaign."""
    tenant_id = getattr(req.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # In a real implementation, we would use SQLAlchemy session and create the campaign
    return {"id": "123e4567-e89b-12d3-a456-426614174000", "name": data.name, "status": "draft"}


@router.get("")
async def list_campaigns(req: Request):
    """List campaigns for the tenant."""
    return {"data": []}


@router.post("/{campaign_id}/start")
async def start_campaign(campaign_id: UUID4, req: Request):
    """Transition campaign to active."""
    return {"status": "active"}
