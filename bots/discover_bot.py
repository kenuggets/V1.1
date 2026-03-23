import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


def generate_role_profile(title: str, sector: str) -> dict:
    """Generate a full role profile for a given career title."""
    prompt = f"""Generate a detailed, realistic career profile for: {title} (Sector: {sector})

Reply with ONLY valid JSON in this exact format:
{{
  "title": "{title}",
  "sector": "{sector}",
  "description": "2-3 sentence overview of the role",
  "typical_hours": "e.g. 70-80 hrs/week at peak, 50-60 standard",
  "avg_salary": "e.g. £45,000-£60,000 base (London, entry level)",
  "exit_opportunities": "bullet list as a single string, separated by |",
  "work_life_balance": "honest 2-3 sentence assessment",
  "skills_required": "bullet list as a single string, separated by |",
  "day_in_life": "a vivid 4-5 sentence description of a typical day"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()
    try:
        return json.loads(text)
    except Exception:
        return {"title": title, "sector": sector, "description": text,
                "typical_hours": "", "avg_salary": "", "exit_opportunities": "",
                "work_life_balance": "", "skills_required": "", "day_in_life": ""}


def compare_roles(roles: list[str], user_profile: dict | None = None) -> str:
    """Generate a side-by-side comparison of 2-4 roles."""
    profile_ctx = ""
    if user_profile:
        profile_ctx = f"\nThe student has a {user_profile.get('degree', 'unknown')} degree from {user_profile.get('university', 'unknown')}."

    prompt = f"""Compare these careers for a university student choosing their first internship target: {', '.join(roles)}.{profile_ctx}

Cover for each role:
- What you actually do day-to-day
- Hours & work-life balance (be honest)
- Starting salary range (UK, London-based)
- Key skills needed
- Exit opportunities after 2-3 years
- What kind of person thrives here (personality fit)

Format as a clear comparison. Use a table where helpful. Be specific and honest — students need real information, not marketing."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def simulate_job_chat(messages: list[dict], role: str, company: str = "") -> str:
    """Run an interactive AI job simulation where Claude plays a senior colleague."""
    system = f"""You are running an immersive job simulation for a university student exploring a career as a {role}{f' at {company}' if company else ''}.

Play the role of their senior colleague/manager. Put them in realistic scenarios:
- Assign them tasks that are typical for this role
- Respond to their actions realistically
- Introduce time pressure, client demands, or team dynamics as appropriate
- After each exchange, give a brief [COACH NOTE] in italics explaining what this scenario teaches about the role

Start by setting the scene: what day it is, what project they're on, and what their first task is.
Make it vivid, honest, and educational. Don't sugarcoat the difficult parts of the job."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def analyse_skills_gap(target_role: str, user_profile: dict) -> dict:
    """Analyse the gap between a student's current profile and their target role."""
    prompt = f"""Perform a skills gap analysis for this student targeting: {target_role}

Student profile:
- Degree: {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')}
- Year of study: {user_profile.get('year_of_study', 'N/A')}
- Current skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience', [])}
- Location: {user_profile.get('location', 'N/A')}

Reply with ONLY valid JSON:
{{
  "role_requires": ["skill1", "skill2", ...],
  "student_has": ["skill1", ...],
  "gaps": [
    {{"skill": "skill name", "priority": "high|medium|low", "how_to_close": "specific action"}}
  ],
  "strengths": ["what they already have going for them"],
  "summary": "2-3 sentence honest assessment"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()
    try:
        return json.loads(text)
    except Exception:
        return {"summary": text, "gaps": [], "strengths": [], "role_requires": [], "student_has": []}


def generate_roadmap(target_role: str, user_profile: dict) -> str:
    """Generate a personalised year-by-year career roadmap."""
    prompt = f"""Create a personalised career roadmap for this student targeting {target_role}.

Student:
- Degree: {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')}
- Current year: {user_profile.get('year_of_study', 'N/A')} (graduation: {user_profile.get('graduation_year', 'N/A')})
- Skills: {', '.join(user_profile.get('skills', []))}
- Experience so far: {user_profile.get('experience', [])}

Create a semester-by-semester or year-by-year roadmap. For each period include:
- 2-3 specific actions (e.g. "Join the Finance Society", not "get involved in finance")
- What to prioritise and why
- Any deadlines that matter (application cycles, competition deadlines, etc.)

Make it realistic for their stage. If they're in Year 1, don't tell them to apply for internships yet.
Be specific, actionable, and honest about what matters most for THIS role."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
