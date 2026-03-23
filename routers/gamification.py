from fastapi import APIRouter
import database

router = APIRouter(prefix="/api/gamification", tags=["gamification"])


@router.get("/dashboard/{user_id}")
async def dashboard(user_id: int):
    """Return all gamification data for the dashboard."""
    streak = database.get_streak(user_id)
    milestones = database.get_milestones(user_id)
    apps = database.get_applications(user_id)
    contacts = database.get_outreach_contacts(user_id)
    chats = database.get_coffee_chats(user_id)
    interviews = database.get_interview_sessions(user_id)

    # Calculate career progress stage
    stage = _compute_stage(apps, contacts, chats, milestones)
    database.update_streak(user_id)

    return {
        "streak": streak,
        "milestones": milestones,
        "stats": {
            "applications": len(apps),
            "contacts_reached": len(contacts),
            "coffee_chats": len(chats),
            "interviews_practiced": len(interviews),
        },
        "career_stage": stage,
    }


@router.get("/streak/{user_id}")
async def get_streak(user_id: int):
    streak = database.update_streak(user_id)
    return streak


@router.get("/milestones/{user_id}")
async def get_milestones(user_id: int):
    milestones = database.get_milestones(user_id)
    return {"milestones": milestones}


def _compute_stage(apps, contacts, chats, milestones) -> dict:
    """Compute the user's career progress stage (0-4)."""
    badge_slugs = {m["badge_slug"] for m in milestones}

    if "offer_received" in badge_slugs:
        return {"level": 4, "label": "Offer Stage", "next": None}
    if len(chats) >= 1 or "first_interview_prep" in badge_slugs:
        return {"level": 3, "label": "Preparing", "next": "Land an offer"}
    if len(apps) >= 1 or len(contacts) >= 1:
        return {"level": 2, "label": "Applying", "next": "Book a coffee chat or interview"}
    if "skills_gap_done" in badge_slugs:
        return {"level": 1, "label": "Building", "next": "Send your first application or cold message"}
    return {"level": 0, "label": "Exploring", "next": "Complete your skills gap analysis"}
