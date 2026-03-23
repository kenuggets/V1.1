from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import database
from bots import prepare_bot

router = APIRouter(prefix="/api/prepare", tags=["prepare"])


# ── Coffee Chat Prep ──────────────────────────────────────────────────────────

class CoffeeChatPrepRequest(BaseModel):
    user_id: int
    contact_name: str
    contact_role: str
    contact_company: str
    contact_info: str
    target_role: str
    scheduled_date: str = ""


@router.post("/coffee-chat-prep")
async def coffee_chat_prep(req: CoffeeChatPrepRequest):
    user = database.get_user_by_id(req.user_id)
    if not user:
        return {"error": "User not found"}
    chat_id = database.add_coffee_chat(req.user_id, {
        "contact_name": req.contact_name,
        "contact_role": req.contact_role,
        "contact_company": req.contact_company,
        "contact_info": req.contact_info,
        "scheduled_date": req.scheduled_date,
    })
    prep = prepare_bot.prep_coffee_chat(req.contact_info, user, req.target_role)
    database.update_streak(req.user_id)
    return {"chat_id": chat_id, "prep": prep}


# ── Coffee Chat Tracker ───────────────────────────────────────────────────────

class CoffeeChatUpdate(BaseModel):
    outcome: Optional[str] = None
    thank_you_sent: Optional[bool] = None
    follow_up_date: Optional[str] = None
    follow_up_notes: Optional[str] = None
    topics_discussed: Optional[str] = None
    target_role: Optional[str] = None


@router.get("/coffee-chats/{user_id}")
async def get_coffee_chats(user_id: int):
    chats = database.get_coffee_chats(user_id)
    return {"chats": chats}


@router.patch("/coffee-chats/{chat_id}")
async def update_coffee_chat(chat_id: int, data: CoffeeChatUpdate):
    database.update_coffee_chat(chat_id, data.model_dump(exclude_none=True))
    return {"status": "updated"}


# ── Follow-Up Strategy ────────────────────────────────────────────────────────

class FollowUpRequest(BaseModel):
    user_id: int
    contact_name: str
    contact_role: str
    contact_company: str
    outcome: str
    topics_discussed: str = ""
    target_role: str = ""


@router.post("/followup-strategy")
async def followup_strategy(req: FollowUpRequest):
    user = database.get_user_by_id(req.user_id)
    if not user:
        return {"error": "User not found"}
    strategy = prepare_bot.generate_followup_strategy(req.model_dump(), user)
    database.update_streak(req.user_id)
    return {"strategy": strategy}


# ── Interview Prep ────────────────────────────────────────────────────────────

class InterviewStartRequest(BaseModel):
    user_id: Optional[int] = None
    role: str
    company: str = ""
    interview_type: str = "Behavioural"
    interviewer_info: str = ""


class InterviewChatRequest(BaseModel):
    messages: List[dict]
    user_id: Optional[int] = None


@router.post("/interview/start")
async def start_interview(req: InterviewStartRequest):
    user_profile = database.get_user_by_id(req.user_id) if req.user_id else None
    if req.user_id:
        database.update_streak(req.user_id)
        database.award_milestone(req.user_id, "first_interview_prep",
                                 "Interview Ready", "Started your first mock interview")
    reply = prepare_bot.start_interview_session(
        req.role, req.company, req.interview_type, req.interviewer_info, user_profile
    )
    return {"reply": reply}


@router.post("/interview/chat")
async def interview_chat(req: InterviewChatRequest):
    user_profile = database.get_user_by_id(req.user_id) if req.user_id else None
    if req.user_id:
        database.update_streak(req.user_id)
    reply = prepare_bot.interview_chat(req.messages, user_profile)
    scores = prepare_bot.parse_scores_from_response(reply)
    return {"reply": reply, "scores": scores}


# ── Audio / Speech Feedback ───────────────────────────────────────────────────

class AudioFeedbackRequest(BaseModel):
    transcript: str
    user_id: Optional[int] = None
    context_type: str = "interview"
    role: str = ""
    question: str = ""


@router.post("/audio-feedback")
async def audio_feedback(req: AudioFeedbackRequest):
    feedback = prepare_bot.analyse_audio_transcript(req.transcript, {
        "type": req.context_type,
        "role": req.role,
        "question": req.question,
    })
    if req.user_id:
        database.update_streak(req.user_id)
        database.award_milestone(req.user_id, "audio_practice",
                                 "Voice Coach", "Used audio feedback for the first time")
    return {"feedback": feedback}


# ── Internship Success Guide ──────────────────────────────────────────────────

class InternshipGuideRequest(BaseModel):
    user_id: int
    role: str
    company: str = ""


@router.post("/internship-guide")
async def internship_guide(req: InternshipGuideRequest):
    user = database.get_user_by_id(req.user_id)
    if not user:
        return {"error": "User not found"}
    guide = prepare_bot.get_internship_guide(req.role, req.company, user)
    database.award_milestone(req.user_id, "offer_received",
                             "Offer Received", "Landed an internship offer!")
    database.update_streak(req.user_id)
    return {"guide": guide}
