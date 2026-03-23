from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import database
from bots import build_bot

router = APIRouter(prefix="/api/build", tags=["build"])


# ── CV / Cover Letter ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    messages: List[dict]
    user_id: Optional[int] = None


@router.post("/cv-chat")
async def cv_chat(req: ChatRequest):
    user_profile = database.get_user_by_id(req.user_id) if req.user_id else None
    if req.user_id:
        database.update_streak(req.user_id)
        database.award_milestone(req.user_id, "cv_started",
                                 "CV Builder", "Started working on your CV")
    reply = build_bot.cv_chat(req.messages, user_profile)
    return {"reply": reply}


# ── Outreach ──────────────────────────────────────────────────────────────────

class OutreachChatRequest(BaseModel):
    messages: List[dict]
    user_id: Optional[int] = None


class OutreachTemplateRequest(BaseModel):
    user_id: int
    scenario: str
    context: dict = {}


@router.post("/outreach-chat")
async def outreach_chat(req: OutreachChatRequest):
    user_profile = database.get_user_by_id(req.user_id) if req.user_id else None
    if req.user_id:
        database.update_streak(req.user_id)
    reply = build_bot.outreach_chat(req.messages, user_profile)
    return {"reply": reply}


@router.post("/outreach-template")
async def outreach_template(req: OutreachTemplateRequest):
    user = database.get_user_by_id(req.user_id)
    if not user:
        return {"error": "User not found"}
    result = build_bot.get_outreach_template(req.scenario, user, req.context)
    database.update_streak(req.user_id)
    return {"template": result}


# ── Contact Tracker ───────────────────────────────────────────────────────────

class ContactIn(BaseModel):
    name: str
    role: str = ""
    company: str = ""
    linkedin_url: str = ""
    date_contacted: str = ""
    reply_status: str = "no_reply"
    follow_up_date: str = ""
    lead_warmth: str = "cold"
    notes: str = ""


class ContactUpdate(BaseModel):
    reply_status: Optional[str] = None
    follow_up_date: Optional[str] = None
    lead_warmth: Optional[str] = None
    notes: Optional[str] = None


@router.post("/contacts/{user_id}")
async def add_contact(user_id: int, contact: ContactIn):
    contact_id = database.add_outreach_contact(user_id, contact.model_dump())
    database.update_streak(user_id)
    return {"contact_id": contact_id}


@router.get("/contacts/{user_id}")
async def get_contacts(user_id: int):
    contacts = database.get_outreach_contacts(user_id)
    return {"contacts": contacts}


@router.patch("/contacts/update/{contact_id}")
async def update_contact(contact_id: int, data: ContactUpdate):
    database.update_outreach_contact(contact_id, data.model_dump(exclude_none=True))
    return {"status": "updated"}


# ── Application Tracker ───────────────────────────────────────────────────────

class ApplicationIn(BaseModel):
    job_title: str
    company: str
    url: str = ""
    platform: str = "manual"
    deadline: str = ""
    follow_up_date: str = ""


class ApplicationUpdate(BaseModel):
    stage: Optional[str] = None
    status: Optional[str] = None
    feedback: Optional[str] = None
    follow_up_date: Optional[str] = None


@router.post("/applications/{user_id}")
async def add_application(user_id: int, app: ApplicationIn):
    app_id = database.log_application(
        user_id, app.job_title, app.company, app.url, app.platform,
        deadline=app.deadline, follow_up_date=app.follow_up_date
    )
    database.update_streak(user_id)
    return {"application_id": app_id}


@router.get("/applications/{user_id}")
async def get_applications(user_id: int):
    apps = database.get_applications(user_id)
    return {"applications": apps}


@router.patch("/applications/update/{app_id}")
async def update_application(app_id: int, data: ApplicationUpdate):
    database.update_application(app_id, data.model_dump(exclude_none=True))
    return {"status": "updated"}


# ── Extra-curricular Guide ────────────────────────────────────────────────────

class ExtraCurricularRequest(BaseModel):
    user_id: int
    target_role: str


@router.post("/extracurricular")
async def extracurricular(req: ExtraCurricularRequest):
    user = database.get_user_by_id(req.user_id)
    if not user:
        return {"error": "User not found"}
    guide = build_bot.get_extracurricular_guide(req.target_role, user)
    database.update_streak(req.user_id)
    return {"guide": guide}


# ── Weekly Goals ──────────────────────────────────────────────────────────────

class WeeklyGoalsRequest(BaseModel):
    user_id: int
    week_start: str


class GoalToggleRequest(BaseModel):
    user_id: int
    week_start: str
    goal_index: int
    completed: bool


@router.post("/weekly-goals/generate")
async def generate_goals(req: WeeklyGoalsRequest):
    user = database.get_user_by_id(req.user_id)
    if not user:
        return {"error": "User not found"}
    apps = database.get_applications(req.user_id)
    contacts = database.get_outreach_contacts(req.user_id)
    chats = database.get_coffee_chats(req.user_id)
    activity = {
        "applications": len(apps),
        "contacts": len(contacts),
        "coffee_chats": len(chats),
    }
    goals = build_bot.generate_weekly_goals(user, activity)
    goals_with_status = [{"task": g["task"], "category": g.get("category", "build"),
                          "estimated_mins": g.get("estimated_mins", 30), "completed": False}
                         for g in goals]
    database.save_weekly_goals(req.user_id, req.week_start, goals_with_status)
    return {"goals": goals_with_status}


@router.get("/weekly-goals/{user_id}/{week_start}")
async def get_goals(user_id: int, week_start: str):
    goals = database.get_weekly_goals(user_id, week_start)
    return {"goals": goals}


@router.patch("/weekly-goals/toggle")
async def toggle_goal(req: GoalToggleRequest):
    goals = database.get_weekly_goals(req.user_id, req.week_start)
    if req.goal_index < len(goals):
        goals[req.goal_index]["completed"] = req.completed
        database.save_weekly_goals(req.user_id, req.week_start, goals)
        if req.completed:
            database.update_streak(req.user_id)
    return {"goals": goals}
