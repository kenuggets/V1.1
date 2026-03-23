import asyncio
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import database
from database import get_user_by_id, log_application, get_applications
from bots.application_bot import score_job_fit

router = APIRouter(prefix="/api/application", tags=["application"])

# In-memory store for active session listings awaiting confirmation
# In production this would be a proper queue/cache
_pending_listings: dict[str, list] = {}
_session_results: dict[str, list] = {}


class SearchRequest(BaseModel):
    user_id: int
    job_titles: list[str]
    location: str


class ConfirmRequest(BaseModel):
    user_id: int
    session_id: str
    listing_index: int
    confirmed: bool


class StatusRequest(BaseModel):
    user_id: int


@router.post("/search")
async def search_jobs(req: SearchRequest):
    """Score and return job listings for user review before applying."""
    user_profile = get_user_by_id(req.user_id)
    if not user_profile:
        return {"error": "User not found"}

    # Return mock listings with scores for UI confirmation flow
    # Real scraping happens via /apply after confirmation
    mock_listings = [
        {"title": t, "company": "Various companies", "url": "", "platform": "search"}
        for t in req.job_titles
    ]

    scored = []
    for listing in mock_listings:
        fit = score_job_fit(listing, user_profile)
        scored.append({**listing, "fit_score": fit.get("score", 0), "fit_reason": fit.get("reason", "")})

    import uuid
    session_id = str(uuid.uuid4())
    _pending_listings[session_id] = scored

    return {"session_id": session_id, "listings": scored}


@router.post("/confirm")
async def confirm_application(req: ConfirmRequest):
    """Mark a listing as confirmed or declined by the user."""
    listings = _pending_listings.get(req.session_id, [])
    if req.listing_index >= len(listings):
        return {"error": "Invalid listing index"}

    listing = listings[req.listing_index]
    if req.confirmed:
        log_application(
            req.user_id,
            listing.get("title", ""),
            listing.get("company", ""),
            listing.get("url", ""),
            listing.get("platform", ""),
            status="applied",
        )
        return {"status": "applied", "listing": listing}
    return {"status": "skipped", "listing": listing}


@router.get("/history/{user_id}")
async def get_history(user_id: int):
    """Return all logged applications for a user."""
    apps = get_applications(user_id)
    return {"applications": apps}
