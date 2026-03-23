from fastapi import APIRouter
from pydantic import BaseModel
from database import upsert_user, get_user_by_email, get_user_by_id

router = APIRouter(prefix="/api/user", tags=["user"])


class UserProfile(BaseModel):
    name: str
    email: str
    degree: str = ""
    university: str = ""
    graduation_year: str = ""
    skills: list[str] = []
    experience: list[dict] = []
    target_roles: list[str] = []
    location: str = ""


@router.post("/save")
async def save_user(profile: UserProfile):
    user_id = upsert_user(profile.model_dump())
    return {"user_id": user_id}


@router.get("/by-email/{email}")
async def get_by_email(email: str):
    user = get_user_by_email(email)
    if not user:
        return {"error": "User not found"}
    return {"user": user}


@router.get("/{user_id}")
async def get_by_id(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        return {"error": "User not found"}
    return {"user": user}
