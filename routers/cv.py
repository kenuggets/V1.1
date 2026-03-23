from fastapi import APIRouter
from pydantic import BaseModel
from bots import cv_bot
from database import get_user_by_id

router = APIRouter(prefix="/api/cv", tags=["cv"])


class ChatRequest(BaseModel):
    messages: list[dict]
    user_id: int | None = None


@router.post("/chat")
async def chat(req: ChatRequest):
    user_profile = get_user_by_id(req.user_id) if req.user_id else None
    reply = cv_bot.chat(req.messages, user_profile)
    return {"reply": reply}
