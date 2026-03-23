import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "career_assistant.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            degree TEXT,
            university TEXT,
            graduation_year TEXT,
            skills TEXT,
            experience TEXT,
            target_roles TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_title TEXT,
            company TEXT,
            url TEXT,
            platform TEXT,
            status TEXT DEFAULT 'pending',
            date_applied TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

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

    conn.commit()
    conn.close()


# --- User helpers ---

def upsert_user(data: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (name, email, degree, university, graduation_year, skills, experience, target_roles, location)
        VALUES (:name, :email, :degree, :university, :graduation_year, :skills, :experience, :target_roles, :location)
        ON CONFLICT(email) DO UPDATE SET
            name=excluded.name,
            degree=excluded.degree,
            university=excluded.university,
            graduation_year=excluded.graduation_year,
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
    user = dict(row)
    for field in ("skills", "experience", "target_roles"):
        try:
            user[field] = json.loads(user[field]) if user[field] else []
        except Exception:
            user[field] = []
    return user


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return None
    user = dict(row)
    for field in ("skills", "experience", "target_roles"):
        try:
            user[field] = json.loads(user[field]) if user[field] else []
        except Exception:
            user[field] = []
    return user


# --- Application helpers ---

def log_application(user_id: int, job_title: str, company: str, url: str, platform: str, status: str = "applied") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO applications (user_id, job_title, company, url, platform, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, job_title, company, url, platform, status))
    conn.commit()
    app_id = c.lastrowid
    conn.close()
    return app_id


def update_application_status(app_id: int, status: str):
    conn = get_connection()
    conn.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
    conn.commit()
    conn.close()


def get_applications(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM applications WHERE user_id = ? ORDER BY date_applied DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Interview session helpers ---

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
