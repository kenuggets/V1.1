import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an expert career advisor and professional CV/cover letter writer with 15+ years of experience helping graduates and students land their first roles at top companies.

Your job is to:
1. Understand the user's background, skills, experiences, and target role/company
2. Give concrete, actionable advice on improving their CV structure and bullet points
3. Write a tailored, compelling cover letter specific to their target role and company
4. Refine your output based on their feedback

Guidelines:
- Use strong action verbs and quantify achievements wherever possible
- Tailor every cover letter to the specific company's culture and values
- Keep CV bullet points concise: impact + action + result
- Cover letters should be 3 paragraphs: hook, value prop, call to action
- Always ask for the target role and company before generating anything
- Be honest but constructive — don't sugarcoat weak areas, give actionable fixes
"""


def chat(messages: list[dict], user_profile: dict | None = None) -> str:
    system = SYSTEM_PROMPT
    if user_profile:
        system += f"""

User profile:
- Name: {user_profile.get('name', 'N/A')}
- Degree: {user_profile.get('degree', 'N/A')} at {user_profile.get('university', 'N/A')} ({user_profile.get('graduation_year', 'N/A')})
- Skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience', [])}
- Target roles: {', '.join(user_profile.get('target_roles', []))}
- Location: {user_profile.get('location', 'N/A')}

Use this profile as context. Always ask for the specific job description or company they are targeting before generating a cover letter.
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    return response.content[0].text
