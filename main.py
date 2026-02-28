from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
import random
import re
import os
import smtplib
from email.message import EmailMessage

from services.ai_service import (
    analyze_resume,
    analyze_job,
    calculate_match,
    detect_skill_gap,
    generate_improvement_suggestions,
    generate_explanation,
    generate_career_roadmap,
    generate_interview_questions,
    evaluate_answer,
    get_matched_skills,
    generate_resume_reference,
    format_resume_reference,
    build_resume_intelligence,
    extract_profile_links,
)

from utils.parser import extract_text_from_pdf

app = FastAPI()
OTP_STORE = {}
OTP_TTL_MINUTES = 10
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER).strip()
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "").strip()


def _allowed_origins():
    defaults = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://internpilot-kappa.vercel.app",
    ]
    if not CORS_ORIGINS_ENV:
        return defaults

    extra = [o.strip() for o in CORS_ORIGINS_ENV.split(",") if o.strip()]
    merged = []
    for origin in defaults + extra:
        if origin not in merged:
            merged.append(origin)
    return merged


def _smtp_configured():
    return bool(SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASS and SMTP_FROM)


def _missing_smtp_fields():
    missing = []
    if not SMTP_HOST:
        missing.append("SMTP_HOST")
    if not SMTP_PORT:
        missing.append("SMTP_PORT")
    if not SMTP_USER:
        missing.append("SMTP_USER")
    if not SMTP_PASS:
        missing.append("SMTP_PASS")
    if not SMTP_FROM:
        missing.append("SMTP_FROM")
    return missing


def _send_otp_email(recipient_email: str, otp_code: str):
    msg = EmailMessage()
    msg["Subject"] = "Your InternPilot OTP Code"
    msg["From"] = SMTP_FROM
    msg["To"] = recipient_email
    msg.set_content(
        f"Your InternPilot verification code is: {otp_code}\n\n"
        f"This code expires in {OTP_TTL_MINUTES} minutes.\n"
        "If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return {"message": "InternPilot FINAL API 🚀"}

@app.post("/upload-and-analyze")
async def upload_and_analyze(
    file: UploadFile = File(...),
    job: str = Query(...)
):
    file_bytes = await file.read()
    resume_text = extract_text_from_pdf(file_bytes)
    if not resume_text or not resume_text.strip():
        return {
            "match_score": 0,
            "match_explanation": "Could not extract text from the uploaded resume PDF. If this is a scanned/image PDF, upload a text-based PDF.",
            "confidence": 0,
            "matched_skills": [],
            "missing_skills": [],
            "improvement_suggestions": ["Upload a selectable-text PDF resume for accurate analysis."],
            "career_roadmap": ["Re-upload resume in text-based PDF format and try again."],
            "hireability_status": "NEEDS IMPROVEMENT",
            "recruiter_decision": "Resume parsing failed",
            "interview_questions": ["Tell me about yourself."],
        }

    resume_data = await analyze_resume(resume_text)
    job_data = await analyze_job(job)
    role_title = job_data.get("role_title", "Target Role")
    role_family = job_data.get("role_family", "general")

    match_score = calculate_match(resume_data, job_data)
    explanation_data = await generate_explanation(match_score)

    missing_skills = detect_skill_gap(resume_data, job_data)
    suggestions = generate_improvement_suggestions(missing_skills, role_title=role_title)
    roadmap = generate_career_roadmap(missing_skills, role_title=role_title)

    matched_skills = get_matched_skills(resume_data, job_data)

    # ⭐ Interview Questions Generated
    question_seed = matched_skills if matched_skills else job_data.get("required_skills", [])
    questions = generate_interview_questions(question_seed, role_title=role_title, role_family=role_family)

    if match_score >= 85:
        hireability = "🔥 TOP CANDIDATE"
        recruiter_decision = "Highly Recommended for Interview"
    elif match_score >= 65:
        hireability = "⭐ STRONG POTENTIAL"
        recruiter_decision = "Consider After Skill Improvement"
    else:
        hireability = "⚠️ NEEDS IMPROVEMENT"
        recruiter_decision = "Needs Training Before Hiring"

    return {
        "role_title": role_title,
        "role_family": role_family,
        "match_score": match_score,
        "match_explanation": explanation_data["match_explanation"],
        "confidence": explanation_data["confidence"],
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "improvement_suggestions": suggestions,
        "career_roadmap": roadmap,
        "hireability_status": hireability,
        "recruiter_decision": recruiter_decision,
        "interview_questions": questions
    }


# ⭐ NEW — Interview Evaluation API
@app.post("/evaluate-answer")
async def evaluate(answer: str = Query(...)):
    feedback = evaluate_answer(answer)
    return feedback


@app.post("/auth/request-otp")
async def request_otp(email: str = Query(...)):
    cleaned_email = (email or "").strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned_email):
        return {"ok": False, "message": "Please provide a valid email address."}

    code = f"{random.randint(0, 999999):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)
    OTP_STORE[cleaned_email] = {"code": code, "expires_at": expires_at}

    if _smtp_configured():
        try:
            _send_otp_email(cleaned_email, code)
            return {
                "ok": True,
                "message": f"OTP sent to {cleaned_email}. It expires in {OTP_TTL_MINUTES} minutes.",
                "expires_in_minutes": OTP_TTL_MINUTES,
            }
        except Exception:
            return {
                "ok": False,
                "message": "Failed to send OTP email. Check SMTP settings and try again.",
            }

    # Fallback development mode when SMTP is not configured.
    return {
        "ok": True,
        "message": f"SMTP not configured. OTP generated in demo mode (expires in {OTP_TTL_MINUTES} minutes).",
        "demo_code": code,
        "expires_in_minutes": OTP_TTL_MINUTES,
    }


@app.post("/auth/verify-otp")
async def verify_otp(email: str = Query(...), code: str = Query(...)):
    cleaned_email = (email or "").strip().lower()
    cleaned_code = (code or "").strip()

    entry = OTP_STORE.get(cleaned_email)
    if not entry:
        return {"ok": False, "message": "No OTP found for this email. Request a new code."}

    if datetime.now(timezone.utc) > entry["expires_at"]:
        OTP_STORE.pop(cleaned_email, None)
        return {"ok": False, "message": "OTP expired. Please request a new code."}

    if entry["code"] != cleaned_code:
        return {"ok": False, "message": "Invalid OTP code."}

    OTP_STORE.pop(cleaned_email, None)
    return {"ok": True, "message": "Login successful.", "user": {"email": cleaned_email, "name": cleaned_email.split("@")[0]}}


@app.get("/auth/smtp-status")
async def smtp_status():
    missing = _missing_smtp_fields()
    return {
        "configured": len(missing) == 0,
        "missing_fields": missing,
    }


@app.post("/extract-resume-links")
async def extract_resume_links(file: UploadFile = File(...)):
    file_bytes = await file.read()
    resume_text = extract_text_from_pdf(file_bytes)
    links = extract_profile_links(resume_text)
    return links


@app.post("/generate-resume-reference")
async def generate_resume(
    job: str = Query(...),
    profile: str = Query(""),
    portfolio: str = Query(""),
    interview_story: str = Query(""),
    linkedin: str = Query(""),
    github: str = Query(""),
    portfolio_url: str = Query(""),
):
    intelligence = await build_resume_intelligence(
        job_text=job,
        profile_text=profile,
        portfolio_text=portfolio,
        interview_story=interview_story,
        linkedin=linkedin,
        github=github,
        portfolio=portfolio_url,
    )
    return intelligence
