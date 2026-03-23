import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


# ── Coffee Chat Prep ─────────────────────────────────────────────────────────

def prep_coffee_chat(contact_info: str, user_profile: dict, target_role: str) -> str:
    """Generate tailored coffee chat preparation based on the interviewer's background."""
    prompt = f"""A student is preparing for a coffee chat. Generate personalised preparation advice.

Student:
- Name: {user_profile.get('name', 'N/A')}
- Degree: {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')}
- Target role: {target_role}
- Skills/experience: {', '.join(user_profile.get('skills', []))}

Person they're meeting:
{contact_info}

Provide:

## Questions to Ask
5-7 specific, thoughtful questions tailored to this person's background and role. Not generic questions — reference specifics from their profile.

## Topics to Avoid
What NOT to ask or bring up (e.g. salary, "can you get me a job", anything already on their public profile)

## How to Start Well
Opening 2-3 sentences that feel natural and set a positive tone

## How to Keep It Going
2-3 techniques to keep the conversation flowing if it stalls

## How to End & Ask for Next Steps
Exact phrasing to close without sounding transactional. How to ask for a referral or follow-on introduction naturally.

## Rapport Tips
Specific things from their background you can connect on authentically."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_followup_strategy(chat_details: dict, user_profile: dict) -> str:
    """Generate a personalised follow-up strategy after a coffee chat."""
    prompt = f"""A student just had a coffee chat. Help them follow up effectively.

Student: {user_profile.get('name', 'N/A')}, targeting {chat_details.get('target_role', 'N/A')}
They spoke with: {chat_details.get('contact_name', 'N/A')}, {chat_details.get('contact_role', 'N/A')} at {chat_details.get('contact_company', 'N/A')}
Outcome: {chat_details.get('outcome', 'N/A')}
Key topics discussed: {chat_details.get('topics_discussed', 'not specified')}

Generate:

## Thank-You Message
A personalised thank-you email/LinkedIn message (ready to send, under 100 words). Reference something specific from the conversation.

## Follow-Up Timeline
Specific dates/timing for follow-up touchpoints over the next 3 months.

## How to Stay on Their Radar
2-3 low-key ways to stay in touch without being annoying (e.g. engaging with their posts, sharing relevant articles)

## How to Ask for a Referral
When and how to ask — exact phrasing when the time is right."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ── Interview Prep ───────────────────────────────────────────────────────────

INTERVIEW_SYSTEM = """You are a senior interview coach preparing candidates for competitive internship interviews at top firms. You are direct, rigorous, and give honest feedback.

You run structured mock interview sessions:
1. When asked to start, generate 5-8 role-specific questions for the interview type
2. Ask questions one at a time — wait for the candidate's answer before asking the next
3. After each answer, assess it immediately using this rubric (score 1-5):
   - Content: accuracy, depth, use of appropriate frameworks (STAR for behavioural, technical accuracy for technical)
   - Structure: clear opening → middle → conclusion, logical flow
   - Conciseness: no padding or filler, appropriate length

Format your assessment exactly like this after every answer:
---ASSESSMENT---
Content: X/5 — [one sentence of feedback]
Structure: X/5 — [one sentence of feedback]
Conciseness: X/5 — [one sentence of feedback]
Overall: [2-3 sentences: most important improvement + what was done well]
---END---

At the end provide a full summary:
---SUMMARY---
Overall Score: X.X/5
Strengths: [bullet list]
Areas to Improve: [bullet list]
Top Tip: [single most impactful thing to work on]
---END---

Interview type knowledge:
- Behavioural: STAR method, self-awareness, "why company", career goals
- Technical (Finance): DCF, LBO, accretion/dilution, M&A rationale, mental maths
- Case (Consulting): profitability, market entry, M&A frameworks, MECE thinking, structuring
- Technical (Tech): system design, data structures, algorithms, product sense
- Group: contribution without dominating, structured thinking under pressure
- Assessment Centre: prioritisation exercises, in-tray tasks, presentation prep

Be rigorous. A 5/5 should be genuinely excellent."""


def start_interview_session(role: str, company: str, interview_type: str,
                             interviewer_info: str = "", user_profile: dict | None = None) -> str:
    system = INTERVIEW_SYSTEM
    if user_profile:
        system += f"""

Candidate:
- Name: {user_profile.get('name', 'N/A')}
- Degree: {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')}
- Skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience', [])}

Tailor questions to their background where relevant."""

    if interviewer_info:
        system += f"\n\nInterviewer background (use to personalise where appropriate):\n{interviewer_info}"

    prompt = (
        f"Start a {interview_type} interview for a {role} internship"
        + (f" at {company}" if company else "")
        + ". Introduce yourself briefly as the interviewer, then ask the first question."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def interview_chat(messages: list[dict], user_profile: dict | None = None) -> str:
    system = INTERVIEW_SYSTEM
    if user_profile:
        system += f"""

Candidate:
- Name: {user_profile.get('name', 'N/A')}
- Degree: {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')}
- Skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience', [])}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def analyse_audio_transcript(transcript: str, context: dict) -> str:
    """Analyse a speech transcript and give communication coaching feedback."""
    prompt = f"""Analyse this spoken answer transcript and give communication coaching feedback.

Context:
- Type: {context.get('type', 'interview answer')} (coffee chat / interview)
- Role: {context.get('role', 'N/A')}
- Question/topic: {context.get('question', 'N/A')}

Transcript:
\"\"\"{transcript}\"\"\"

Provide feedback on:

## Content Quality
Was the answer substantive? Did it address the question? Missing key points?

## Tone & Confidence
Did they sound confident? Any hedging language ("kind of", "I think maybe")? Too formal / too casual?

## Rapport & Curiosity Signals
Did they sound genuinely interested? Any moments that built rapport?

## Filler Words & Pacing
Identify filler words (um, uh, like, you know). Was the pace appropriate?

## Structure
Was it well-organised? Did it have a clear beginning, middle, end?

## Top 2 Improvements
The two most impactful changes they could make.

## What Was Strong
Acknowledge genuine strengths."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
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


# ── Internship Success Guide ─────────────────────────────────────────────────

def get_internship_guide(role: str, company: str, user_profile: dict) -> str:
    """Generate personalised advice for making the most of an internship."""
    prompt = f"""A student has just landed an internship as a {role}{f' at {company}' if company else ''}.

Student: {user_profile.get('degree', 'N/A')} student at {user_profile.get('university', 'N/A')}

Give them a comprehensive guide to making the most of their internship and securing a return offer:

## First Week: First Impressions
Specific actions in the first 5 days. What to do, what to avoid.

## Building Relationships
How to network internally — who to meet, how to approach them, what to ask.

## Delivering Great Work
What "excellent intern" looks like in this specific role/sector.

## Getting a Return Offer
The factors that most determine return offer decisions in this industry. What interns typically get wrong.

## Professionalism & Culture
Specific norms for this industry (e.g. IB has different norms than tech). What to observe in week 1.

Be specific to {role}. Not generic advice — real, actionable guidance for this industry."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
