import sqlite3
import json
from pathlib import Path
from datetime import date, datetime

DB_PATH = Path(__file__).parent / "career_assistant.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            degree TEXT,
            university TEXT,
            graduation_year TEXT,
            year_of_study TEXT,
            target_sector TEXT,
            career_stage TEXT DEFAULT 'exploring',
            personality_notes TEXT,
            skills TEXT,
            experience TEXT,
            target_roles TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Role profiles (AI-generated content cache) ─────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS role_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            sector TEXT,
            description TEXT,
            typical_hours TEXT,
            avg_salary TEXT,
            exit_opportunities TEXT,
            work_life_balance TEXT,
            skills_required TEXT,
            day_in_life TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Professional testimonials ──────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS testimonials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            submitter_name TEXT,
            submitter_company TEXT,
            submitter_years_exp TEXT,
            content TEXT,
            approved INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Skills gap analyses ────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS skills_gaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            target_role TEXT,
            gap_analysis TEXT,
            roadmap TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Outreach contacts ──────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS outreach_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            role TEXT,
            company TEXT,
            linkedin_url TEXT,
            date_contacted TEXT,
            reply_status TEXT DEFAULT 'no_reply',
            follow_up_date TEXT,
            lead_warmth TEXT DEFAULT 'cold',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Applications (extended) ────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_title TEXT,
            company TEXT,
            url TEXT,
            platform TEXT,
            status TEXT DEFAULT 'applied',
            stage TEXT DEFAULT 'applied',
            deadline TEXT,
            feedback TEXT,
            follow_up_date TEXT,
            date_applied TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Coffee chats / networking tracker ─────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS coffee_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            contact_name TEXT,
            contact_role TEXT,
            contact_company TEXT,
            contact_info TEXT,
            scheduled_date TEXT,
            outcome TEXT,
            thank_you_sent INTEGER DEFAULT 0,
            follow_up_date TEXT,
            follow_up_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Interview sessions ─────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            company TEXT,
            interview_type TEXT,
            questions TEXT,
            answers TEXT,
            scores TEXT,
            overall_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Milestone badges ───────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            badge_slug TEXT,
            badge_name TEXT,
            badge_description TEXT,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Weekly goals ───────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS weekly_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            week_start TEXT,
            goals TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Streaks ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_active_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ── User helpers ─────────────────────────────────────────────────────────────

def upsert_user(data: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (name, email, degree, university, graduation_year, year_of_study,
                           target_sector, career_stage, personality_notes,
                           skills, experience, target_roles, location)
        VALUES (:name, :email, :degree, :university, :graduation_year, :year_of_study,
                :target_sector, :career_stage, :personality_notes,
                :skills, :experience, :target_roles, :location)
        ON CONFLICT(email) DO UPDATE SET
            name=excluded.name,
            degree=excluded.degree,
            university=excluded.university,
            graduation_year=excluded.graduation_year,
            year_of_study=excluded.year_of_study,
            target_sector=excluded.target_sector,
            career_stage=excluded.career_stage,
            personality_notes=excluded.personality_notes,
            skills=excluded.skills,
            experience=excluded.experience,
            target_roles=excluded.target_roles,
            location=excluded.location
    """, {
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "degree": data.get("degree", ""),
        "university": data.get("university", ""),
        "graduation_year": data.get("graduation_year", ""),
        "year_of_study": data.get("year_of_study", ""),
        "target_sector": data.get("target_sector", ""),
        "career_stage": data.get("career_stage", "exploring"),
        "personality_notes": data.get("personality_notes", ""),
        "skills": json.dumps(data.get("skills", [])),
        "experience": json.dumps(data.get("experience", [])),
        "target_roles": json.dumps(data.get("target_roles", [])),
        "location": data.get("location", ""),
    })
    conn.commit()
    user_id = c.lastrowid or get_user_by_email(data["email"])["id"]
    conn.close()
    return user_id


def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not row:
        return None
    return _parse_user(dict(row))


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return _parse_user(dict(row))


def _parse_user(user: dict) -> dict:
    for field in ("skills", "experience", "target_roles"):
        try:
            user[field] = json.loads(user[field]) if user[field] else []
        except Exception:
            user[field] = []
    return user


# ── Role profile helpers ──────────────────────────────────────────────────────

def get_role_profile(title: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM role_profiles WHERE title = ?", (title,)).fetchone()
    conn.close()
    return dict(row) if row else None


def save_role_profile(data: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO role_profiles (title, sector, description, typical_hours, avg_salary,
                                   exit_opportunities, work_life_balance, skills_required, day_in_life)
        VALUES (:title, :sector, :description, :typical_hours, :avg_salary,
                :exit_opportunities, :work_life_balance, :skills_required, :day_in_life)
        ON CONFLICT(title) DO UPDATE SET
            sector=excluded.sector, description=excluded.description,
            typical_hours=excluded.typical_hours, avg_salary=excluded.avg_salary,
            exit_opportunities=excluded.exit_opportunities,
            work_life_balance=excluded.work_life_balance,
            skills_required=excluded.skills_required, day_in_life=excluded.day_in_life
    """, data)
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id


def list_roles_by_sector(sector: str = None) -> list[dict]:
    conn = get_connection()
    if sector:
        rows = conn.execute("SELECT * FROM role_profiles WHERE sector = ? ORDER BY title", (sector,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM role_profiles ORDER BY sector, title").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Testimonial helpers ───────────────────────────────────────────────────────

def submit_testimonial(role: str, name: str, company: str, years_exp: str, content: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO testimonials (role, submitter_name, submitter_company, submitter_years_exp, content)
        VALUES (?, ?, ?, ?, ?)
    """, (role, name, company, years_exp, content))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id


def get_testimonials(role: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM testimonials WHERE role = ? AND approved = 1 ORDER BY created_at DESC", (role,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Skills gap helpers ────────────────────────────────────────────────────────

def save_skills_gap(user_id: int, target_role: str, gap_analysis: str, roadmap: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO skills_gaps (user_id, target_role, gap_analysis, roadmap)
        VALUES (?, ?, ?, ?)
    """, (user_id, target_role, gap_analysis, roadmap))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id


def get_latest_skills_gap(user_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM skills_gaps WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Outreach contact helpers ──────────────────────────────────────────────────

def add_outreach_contact(user_id: int, data: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO outreach_contacts (user_id, name, role, company, linkedin_url,
                                       date_contacted, reply_status, follow_up_date, lead_warmth, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, data.get("name", ""), data.get("role", ""), data.get("company", ""),
          data.get("linkedin_url", ""), data.get("date_contacted", ""),
          data.get("reply_status", "no_reply"), data.get("follow_up_date", ""),
          data.get("lead_warmth", "cold"), data.get("notes", "")))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    award_milestone(user_id, "first_outreach", "First Outreach", "Sent your first cold message")
    return row_id


def update_outreach_contact(contact_id: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE outreach_contacts
        SET reply_status=?, follow_up_date=?, lead_warmth=?, notes=?
        WHERE id=?
    """, (data.get("reply_status"), data.get("follow_up_date"),
          data.get("lead_warmth"), data.get("notes"), contact_id))
    conn.commit()
    conn.close()


def get_outreach_contacts(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM outreach_contacts WHERE user_id = ? ORDER BY date_contacted DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Application helpers ───────────────────────────────────────────────────────

def log_application(user_id: int, job_title: str, company: str, url: str, platform: str,
                    status: str = "applied", deadline: str = "", follow_up_date: str = "") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO applications (user_id, job_title, company, url, platform, status, stage, deadline, follow_up_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, job_title, company, url, platform, status, "applied", deadline, follow_up_date))
    conn.commit()
    app_id = c.lastrowid
    conn.close()
    award_milestone(user_id, "first_application", "First Application", "Submitted your first job application")
    return app_id


def update_application(app_id: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE applications SET stage=?, status=?, feedback=?, follow_up_date=? WHERE id=?
    """, (data.get("stage"), data.get("status"), data.get("feedback"),
          data.get("follow_up_date"), app_id))
    conn.commit()
    conn.close()


def get_applications(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM applications WHERE user_id = ? ORDER BY date_applied DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Coffee chat helpers ───────────────────────────────────────────────────────

def add_coffee_chat(user_id: int, data: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO coffee_chats (user_id, contact_name, contact_role, contact_company,
                                  contact_info, scheduled_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, data.get("contact_name", ""), data.get("contact_role", ""),
          data.get("contact_company", ""), data.get("contact_info", ""),
          data.get("scheduled_date", "")))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    award_milestone(user_id, "first_coffee_chat", "First Coffee Chat", "Booked your first coffee chat")
    return row_id


def update_coffee_chat(chat_id: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE coffee_chats
        SET outcome=?, thank_you_sent=?, follow_up_date=?, follow_up_notes=?
        WHERE id=?
    """, (data.get("outcome"), data.get("thank_you_sent", 0),
          data.get("follow_up_date"), data.get("follow_up_notes"), chat_id))
    conn.commit()
    conn.close()


def get_coffee_chats(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM coffee_chats WHERE user_id = ? ORDER BY scheduled_date DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Interview session helpers ─────────────────────────────────────────────────

def save_interview_session(user_id: int, role: str, company: str, interview_type: str,
                            questions: list, answers: list, scores: list, overall_score: float) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO interview_sessions (user_id, role, company, interview_type, questions, answers, scores, overall_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, role, company, interview_type,
          json.dumps(questions), json.dumps(answers), json.dumps(scores), overall_score))
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return session_id


def get_interview_sessions(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM interview_sessions WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    sessions = []
    for row in rows:
        s = dict(row)
        for field in ("questions", "answers", "scores"):
            try:
                s[field] = json.loads(s[field]) if s[field] else []
            except Exception:
                s[field] = []
        sessions.append(s)
    return sessions


# ── Milestone helpers ─────────────────────────────────────────────────────────

def award_milestone(user_id: int, badge_slug: str, badge_name: str, badge_description: str):
    conn = get_connection()
    exists = conn.execute(
        "SELECT id FROM milestones WHERE user_id=? AND badge_slug=?", (user_id, badge_slug)
    ).fetchone()
    if not exists:
        conn.execute("""
            INSERT INTO milestones (user_id, badge_slug, badge_name, badge_description)
            VALUES (?, ?, ?, ?)
        """, (user_id, badge_slug, badge_name, badge_description))
        conn.commit()
    conn.close()


def get_milestones(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM milestones WHERE user_id = ? ORDER BY earned_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Weekly goals helpers ──────────────────────────────────────────────────────

def save_weekly_goals(user_id: int, week_start: str, goals: list) -> int:
    conn = get_connection()
    c = conn.cursor()
    existing = conn.execute(
        "SELECT id FROM weekly_goals WHERE user_id=? AND week_start=?", (user_id, week_start)
    ).fetchone()
    if existing:
        conn.execute("UPDATE weekly_goals SET goals=? WHERE id=?",
                     (json.dumps(goals), existing["id"]))
        conn.commit()
        row_id = existing["id"]
    else:
        c.execute("INSERT INTO weekly_goals (user_id, week_start, goals) VALUES (?, ?, ?)",
                  (user_id, week_start, json.dumps(goals)))
        conn.commit()
        row_id = c.lastrowid
    conn.close()
    return row_id


def get_weekly_goals(user_id: int, week_start: str) -> list:
    conn = get_connection()
    row = conn.execute(
        "SELECT goals FROM weekly_goals WHERE user_id=? AND week_start=?", (user_id, week_start)
    ).fetchone()
    conn.close()
    if not row:
        return []
    try:
        return json.loads(row["goals"])
    except Exception:
        return []


# ── Streak helpers ────────────────────────────────────────────────────────────

def update_streak(user_id: int) -> dict:
    today = date.today().isoformat()
    conn = get_connection()
    row = conn.execute("SELECT * FROM streaks WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        conn.execute("""
            INSERT INTO streaks (user_id, current_streak, longest_streak, last_active_date)
            VALUES (?, 1, 1, ?)
        """, (user_id, today))
        conn.commit()
        conn.close()
        return {"current_streak": 1, "longest_streak": 1}

    row = dict(row)
    last = row["last_active_date"]
    current = row["current_streak"]
    longest = row["longest_streak"]

    if last == today:
        conn.close()
        return {"current_streak": current, "longest_streak": longest}

    from datetime import timedelta
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if last == yesterday:
        current += 1
    else:
        current = 1

    longest = max(longest, current)
    conn.execute("""
        UPDATE streaks SET current_streak=?, longest_streak=?, last_active_date=? WHERE user_id=?
    """, (current, longest, today, user_id))
    conn.commit()
    conn.close()
    return {"current_streak": current, "longest_streak": longest}


def get_streak(user_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM streaks WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return {"current_streak": 0, "longest_streak": 0}
    return {"current_streak": row["current_streak"], "longest_streak": row["longest_streak"]}
