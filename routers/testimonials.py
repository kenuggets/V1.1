from fastapi import APIRouter
from pydantic import BaseModel
import database

router = APIRouter(prefix="/api/testimonials", tags=["testimonials"])


class TestimonialIn(BaseModel):
    role: str
    submitter_name: str
    submitter_company: str
    submitter_years_exp: str = ""
    content: str


@router.post("/submit")
async def submit_testimonial(t: TestimonialIn):
    tid = database.submit_testimonial(
        t.role, t.submitter_name, t.submitter_company, t.submitter_years_exp, t.content
    )
    return {"testimonial_id": tid}


@router.get("/{role}")
async def get_testimonials(role: str):
    testimonials = database.get_testimonials(role)
    return {"testimonials": testimonials}
