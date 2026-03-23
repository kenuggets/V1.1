from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import database
from bots import discover_bot

router = APIRouter(prefix="/api/discover", tags=["discover"])


class RoleRequest(BaseModel):
    title: str
    sector: str


class CompareRequest(BaseModel):
    roles: List[str]
    user_id: Optional[int] = None


class SimulateRequest(BaseModel):
    messages: List[dict]
    role: str
    company: str = ""


class SkillsGapRequest(BaseModel):
    user_id: int
    target_role: str


class RoadmapRequest(BaseModel):
    user_id: int
    target_role: str


@router.get("/roles")
async def list_roles(sector: Optional[str] = None):
    roles = database.list_roles_by_sector(sector)
    return {"roles": roles}


@router.post("/role-profile")
async def get_or_generate_role(req: RoleRequest):
    existing = database.get_role_profile(req.title)
    if existing:
        return {"profile": existing, "source": "cached"}
    profile = discover_bot.generate_role_profile(req.title, req.sector)
    database.save_role_profile(profile)
    return {"profile": profile, "source": "generated"}


@router.post("/compare")
async def compare_roles(req: CompareRequest):
    user_profile = None
    if req.user_id:
        user_profile = database.get_user_by_id(req.user_id)
    comparison = discover_bot.compare_roles(req.roles, user_profile)
    return {"comparison": comparison}


@router.post("/simulate")
async def simulate_job(req: SimulateRequest):
    reply = discover_bot.simulate_job_chat(req.messages, req.role, req.company)
    return {"reply": reply}


@router.post("/skills-gap")
async def skills_gap(req: SkillsGapRequest):
    user = database.get_user_by_id(req.user_id)
    if not user:
        return {"error": "User not found"}
    result = discover_bot.analyse_skills_gap(req.target_role, user)
    roadmap = discover_bot.generate_roadmap(req.target_role, user)
    database.save_skills_gap(req.user_id, req.target_role, str(result), roadmap)
    database.award_milestone(req.user_id, "skills_gap_done",
                             "Self-Aware", "Completed your first skills gap analysis")
    database.update_streak(req.user_id)
    return {"gap_analysis": result, "roadmap": roadmap}


@router.post("/roadmap")
async def roadmap(req: RoadmapRequest):
    user = database.get_user_by_id(req.user_id)
    if not user:
        return {"error": "User not found"}
    result = discover_bot.generate_roadmap(req.target_role, user)
    database.update_streak(req.user_id)
    return {"roadmap": result}
