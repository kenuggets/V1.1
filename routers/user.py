from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import database

router = APIRouter(prefix="/api/user", tags=["user"])


class UserProfile(BaseModel):
    name: str
    email: str
    degree: str = ""
    university: str = ""
    graduation_year: str = ""
    year_of_study: str = ""
    target_sector: str = ""
    career_stage: str = "exploring"
    personality_notes: str = ""
    skills: List[str] = []
    experience: List = []
    target_roles: List[str] = []
    location: str = ""


@router.post("/save")
async def save_user(profile: UserProfile):
    user_id = database.upsert_user(profile.model_dump())
    database.update_streak(user_id)
    return {"user_id": user_id}


@router.get("/by-email/{email}")
async def get_by_email(email: str):
    user = database.get_user_by_email(email)
    if not user:
        return {"error": "User not found"}
    return {"user": user}


@router.get("/{user_id}")
async def get_by_id(user_id: int):
    user = database.get_user_by_id(user_id)
    if not user:
        return {"error": "User not found"}
    streak = database.get_streak(user_id)
    milestones = database.get_milestones(user_id)
    return {"user": user, "streak": streak, "milestones": milestones}
