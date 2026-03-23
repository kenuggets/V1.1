import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


# ── CV & Cover Letter ────────────────────────────────────────────────────────

CV_SYSTEM = """You are an expert career advisor and CV writer specialising in helping university students land their first internships at top firms.

Your job:
1. Give concrete, actionable feedback on CV bullet points and structure
2. Write tailored, compelling cover letters specific to the target role and company
3. Provide LinkedIn profile optimisation advice (section by section)
4. Refine output based on user feedback

CV bullet point formula: Action verb + Task/Project + Quantified Result
Cover letter format: Hook (why this company) → Value prop (what you bring) → Call to action
LinkedIn: Headline, About, Experience, Skills, Featured sections matter most

Be honest and direct. Don't sugarcoat weak points — give fixes.
Always ask for the target role and company before generating a cover letter."""


def cv_chat(messages: list[dict], user_profile: dict | None = None) -> str:
    system = CV_SYSTEM
    if user_profile:
        system += f"""

Student profile:
- Name: {user_profile.get('name', 'N/A')}
- Degree: {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')} ({user_profile.get('graduation_year', 'N/A')})
- Year: {user_profile.get('year_of_study', 'N/A')}
- Skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience', [])}
- Target roles: {', '.join(user_profile.get('target_roles', []))}
- Target sector: {user_profile.get('target_sector', 'N/A')}
- Location: {user_profile.get('location', 'N/A')}

Use this profile as context. Always ask for the specific job description or company they are targeting before generating a cover letter."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    return response.content[0].text


# ── Outreach / Cold Email ────────────────────────────────────────────────────

OUTREACH_SYSTEM = """You are a cold outreach strategist who has helped hundreds of students land internships through targeted networking.

You write messages that get replies. Your approach:
- Keep messages under 150 words — busy people skim
- Open with a specific, personalised hook (never "I hope this email finds you well")
- Lead with genuine interest and a specific reason for reaching out
- End with a low-friction ask (15-minute call, not "let me know if there's an opening")
- Subject lines: specific, under 8 words

Scenarios you handle:
- cold_alumni: Reaching out to a uni alumnus at the target company
- cold_recruiter: Reaching out to a recruiter or hiring manager
- coffee_chat_followup: Following up after a coffee chat
- referral_ask: Asking someone to refer you for a role
- thank_you: Post-coffee-chat thank you note

When asked for a template: generate the message + subject line + a brief note on what makes it effective.
Give 2 variations (more formal / more conversational).
Provide real-time feedback when the user pastes a draft."""


def outreach_chat(messages: list[dict], user_profile: dict | None = None) -> str:
    system = OUTREACH_SYSTEM
    if user_profile:
        system += f"""

Student:
- Name: {user_profile.get('name', 'N/A')}
- Degree: {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')}
- Skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience', [])}
- Target roles: {', '.join(user_profile.get('target_roles', []))}
- Target sector: {user_profile.get('target_sector', 'N/A')}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=OUTREACH_SYSTEM,
        messages=messages,
    )
    return response.content[0].text


def get_outreach_template(scenario: str, user_profile: dict, context: dict) -> str:
    """Generate a specific outreach template for a given scenario."""
    scenario_labels = {
        "cold_alumni": "cold message to a university alumnus",
        "cold_recruiter": "cold message to a recruiter or hiring manager",
        "coffee_chat_followup": "follow-up after a coffee chat",
        "referral_ask": "referral request",
        "thank_you": "thank-you note after a coffee chat or interview",
    }
    label = scenario_labels.get(scenario, scenario)

    prompt = f"""Write a {label} template for this student.

Student: {user_profile.get('name', 'N/A')}, studying {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')}
Target role: {context.get('target_role', user_profile.get('target_roles', ['N/A'])[0] if user_profile.get('target_roles') else 'N/A')}
Target company: {context.get('company', 'N/A')}
Recipient: {context.get('recipient_name', 'N/A')} — {context.get('recipient_role', 'N/A')}
Additional context: {context.get('notes', 'none')}

Provide:
1. Subject line (if email)
2. Version A (professional/formal)
3. Version B (warm/conversational)
4. A brief note on what makes each effective

Keep each message under 150 words."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ── Extra-Curricular Guide ───────────────────────────────────────────────────

def get_extracurricular_guide(target_role: str, user_profile: dict) -> str:
    """Recommend role-specific extra-curricular activities and how to approach them."""
    prompt = f"""A student is targeting {target_role} internships. Give them a guide to the most valuable extra-curricular activities for this specific path.

Student profile:
- Degree: {user_profile.get('degree', 'N/A')}
- Year: {user_profile.get('year_of_study', 'N/A')}
- Current skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience', [])}

For each recommended activity:
1. What it is and why it matters for {target_role}
2. Specific examples (named competitions, certifications, platforms)
3. How to get started (concrete first step)
4. How to present it on a CV

Include 4-6 activities ranked by impact. Be specific — not "join a finance society" but "join your university's Investment Society and pitch for an analyst role in the portfolio team"."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ── Weekly micro-tasks ───────────────────────────────────────────────────────

def generate_weekly_goals(user_profile: dict, recent_activity: dict) -> list[dict]:
    """Generate 3-5 specific weekly micro-tasks based on the user's current stage."""
    prompt = f"""Generate 3-5 specific weekly micro-tasks for this student. Tasks must be concrete and completable in under 2 hours each.

Student:
- Target role: {', '.join(user_profile.get('target_roles', ['N/A']))}
- Year: {user_profile.get('year_of_study', 'N/A')}
- Career stage: {user_profile.get('career_stage', 'exploring')}

Recent activity:
- Applications sent: {recent_activity.get('applications', 0)}
- Contacts reached out to: {recent_activity.get('contacts', 0)}
- Coffee chats completed: {recent_activity.get('coffee_chats', 0)}
- CV last updated: {recent_activity.get('cv_updated', 'unknown')}

Reply with ONLY valid JSON array:
[
  {{"task": "specific task text", "category": "discover|build|prepare|networking", "estimated_mins": 30}},
  ...
]

Example good task: "Find 3 alumni from your university on LinkedIn who work at Goldman Sachs and send connection requests with personalised notes"
Example bad task: "Network more" or "Improve your CV" """

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()
    try:
        import json
        return json.loads(text)
    except Exception:
        return [{"task": "Update your CV with your most recent experience", "category": "build", "estimated_mins": 45}]
