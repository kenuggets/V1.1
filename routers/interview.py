from fastapi import APIRouter
from pydantic import BaseModel
from bots import interview_bot
from database import get_user_by_id, save_interview_session

router = APIRouter(prefix="/api/interview", tags=["interview"])


class StartRequest(BaseModel):
    role: str
    company: str = ""
    interview_type: str = "mixed"
    user_id: int | None = None


class ChatRequest(BaseModel):
    messages: list[dict]
    user_id: int | None = None
    role: str = ""
    company: str = ""
    interview_type: str = "mixed"


class SaveSessionRequest(BaseModel):
    user_id: int
    role: str
    company: str
    interview_type: str
    questions: list[str]
    answers: list[str]
    scores: list[dict]
    overall_score: float


@router.post("/start")
async def start_session(req: StartRequest):
    user_profile = get_user_by_id(req.user_id) if req.user_id else None
    reply = interview_bot.start_session(req.role, req.company, req.interview_type, user_profile)
    return {"reply": reply}


@router.post("/chat")
async def chat(req: ChatRequest):
    user_profile = get_user_by_id(req.user_id) if req.user_id else None
    reply = interview_bot.chat(req.messages, user_profile)
    scores = interview_bot.parse_scores_from_response(reply)
    return {"reply": reply, "scores": scores}


@router.post("/save-session")
async def save_session(req: SaveSessionRequest):
    session_id = save_interview_session(
        req.user_id, req.role, req.company, req.interview_type,
        req.questions, req.answers, req.scores, req.overall_score
    )
    return {"session_id": session_id}
