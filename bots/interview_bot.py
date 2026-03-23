import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a senior interview coach who prepares candidates for competitive internship interviews at top firms. You are direct, rigorous, and give honest feedback.

You run structured mock interview sessions:
1. When asked to start a session, generate 5-8 role-specific questions appropriate for the role and interview type
2. Ask questions one at a time — wait for the candidate's answer before asking the next
3. After each answer, assess it immediately using this rubric (score 1-5 each):
   - Content: accuracy, depth, use of appropriate frameworks (STAR for behavioural, technical accuracy for technical)
   - Structure: clear opening → middle → conclusion, logical flow
   - Conciseness: no padding or filler, appropriate length for the question

Format your assessment exactly like this after every answer:
---ASSESSMENT---
Content: X/5 — [one sentence of feedback]
Structure: X/5 — [one sentence of feedback]
Conciseness: X/5 — [one sentence of feedback]
Overall: [2-3 sentences of the most important improvement + what was done well]
---END---

Then ask the next question.

At the end of the session (when all questions are answered), provide a full summary:
---SUMMARY---
Overall Score: X.X/5
Strengths: [bullet list]
Areas to Improve: [bullet list]
Top Tip: [single most impactful thing to work on]
---END---

Role-specific knowledge:
- Investment Banking: DCF, LBO, accretion/dilution, M&A rationale, market sizing, "why IB", deal experience
- Consulting: case frameworks (profitability, market entry, M&A), MECE thinking, structuring, mental maths
- Tech: system design, data structures & algorithms, behavioural (STAR), product sense
- General: STAR method, self-awareness, why company, career goals

Be rigorous. A 5/5 should be genuinely excellent, not just adequate.
"""


def start_session(role: str, company: str, interview_type: str, user_profile: dict | None = None) -> str:
    system = SYSTEM_PROMPT
    if user_profile:
        system += f"""

Candidate profile:
- Name: {user_profile.get('name', 'N/A')}
- Degree: {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')}
- Skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience', [])}

Tailor questions to their background where appropriate (e.g. reference their experience in follow-ups).
"""

    prompt = (
        f"Please start a {interview_type} interview session for a {role} internship"
        + (f" at {company}" if company else "")
        + ". Introduce yourself briefly, then ask the first question."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def chat(messages: list[dict], user_profile: dict | None = None) -> str:
    system = SYSTEM_PROMPT
    if user_profile:
        system += f"""

Candidate profile:
- Name: {user_profile.get('name', 'N/A')}
- Degree: {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')}
- Skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience', [])}
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def parse_scores_from_response(response_text: str) -> dict | None:
    """Extract structured scores from the assessment block if present."""
    if "---ASSESSMENT---" not in response_text:
        return None
    try:
        block = response_text.split("---ASSESSMENT---")[1].split("---END---")[0].strip()
        scores = {}
        for line in block.split("\n"):
            if line.startswith("Content:"):
                scores["content"] = int(line.split(":")[1].strip().split("/")[0])
            elif line.startswith("Structure:"):
                scores["structure"] = int(line.split(":")[1].strip().split("/")[0])
            elif line.startswith("Conciseness:"):
                scores["conciseness"] = int(line.split(":")[1].strip().split("/")[0])
        return scores if scores else None
    except Exception:
        return None
