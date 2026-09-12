import tempfile
import os
import json as json_lib
import logging
from collections import Counter
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


from app.db.database import init_db
from app.db.jobs import create_job, get_job, list_jobs, update_job, delete_job
from app.db.candidates import (
    create_candidate, get_candidate, list_candidates,
    update_candidate_cv, delete_candidate,
)
from app.db.screenings import (
    list_screenings_for_job, list_screenings_for_candidate,
    list_all_screenings_for_user, delete_screenings_for_candidate,
    list_communication_queue, get_screening_with_details, update_screening_decision,
)
from app.graph.orchestrator import screen_candidates_for_job, run_and_save_screening
from app.agents.scheduling_agent import propose_interview_slots, build_confirmation_message
from app.db.interviews import create_interview, list_interviews_for_hr, list_interviews_today
from app.db.users import UsernameAlreadyExistsError, create_user, verify_user, get_user_profile
from app.agents.communication_agent import generate_candidate_email
from app.email_service import send_email
from app.auth import create_access_token, get_current_user, validate_password_strength
from app.rag.job_store import index_jobs
from app.agents.matching_agent import match_candidate_to_jobs
from app.agents.prescreening_agent import generate_prescreening_questions, analyze_prescreening_answers
from app.pdf_utils import extract_text_from_pdf, extract_text_and_links_from_pdf, extract_contact_info
from app.agents.onboarding_agent import generate_onboarding_checklist
from app.db.candidates import mark_candidate_hired, list_hired_candidates, update_onboarding_checklist, update_mentor_name
from app.calendar_service import create_calendar_event

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.pdf_utils import validate_pdf_upload

RESUMES_DIR = "data/resumes"
os.makedirs(RESUMES_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="HR AI Agent API", lifespan=lifespan)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
def root():
    return {"status": "running"}


# --- Auth ---

@app.post("/register")
def api_register(username: str = Form(...), password: str = Form(...), company_name: str = Form(...), email: str = Form("")):
    normalized = username.strip().lower()
    password_error = validate_password_strength(password)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)
    try:
        create_user(username, password, company_name, email)
    except UsernameAlreadyExistsError:
        raise HTTPException(status_code=409, detail="This username is already taken.")
    token = create_access_token(normalized)  # auto-login: no separate login step needed
    return {"access_token": token, "token_type": "bearer", "username": normalized}

@app.post("/login")
def api_login(username: str = Form(...), password: str = Form(...)):
    if not verify_user(username, password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    normalized = username.strip().lower()
    token = create_access_token(normalized)  # token always uses normalized identity
    return {"access_token": token, "token_type": "bearer"}


# --- Jobs ---

def _get_owned_job_or_404(job_id: int, user: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["created_by"] != user:
        raise HTTPException(status_code=403, detail="You do not have access to this job")
    return job


def _get_owned_candidate_or_404(candidate_id: int, user: str):
    candidate = get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.get("created_by") != user:
        raise HTTPException(status_code=403, detail="You do not have access to this candidate")
    return candidate


def _rescore_job_candidates(job_id: int):
    screenings = list_screenings_for_job(job_id)
    candidate_ids = list({s["candidate_id"] for s in screenings})
    if candidate_ids:
        screen_candidates_for_job(candidate_ids, job_id)


@app.get("/jobs")
def api_list_jobs(user: str = Depends(get_current_user)):
    return list_jobs(created_by=user)


@app.get("/jobs/{job_id}")
def api_get_job(job_id: int, user: str = Depends(get_current_user)):
    return _get_owned_job_or_404(job_id, user)


@app.post("/jobs")
def api_create_job(
    title: str = Form(...), description: str = Form(...), requirements: str = Form(""),
    location: str = Form(""), remote_policy: str = Form(""), experience_level: str = Form(""),
    user: str = Depends(get_current_user),
):
    job_id = create_job(title, description, requirements, user, location, remote_policy, experience_level)
    job = get_job(job_id)
    index_jobs([{
        "id": str(job_id), "title": title, "description": description, "created_by": user,
        "location": location, "remote_policy": remote_policy, "experience_level": experience_level,
    }])
    return job


@app.put("/jobs/{job_id}")
def api_update_job(
    job_id: int, title: str = Form(None), description: str = Form(None), requirements: str = Form(None),
    location: str = Form(None), remote_policy: str = Form(None), experience_level: str = Form(None),
    user: str = Depends(get_current_user),
):
    _get_owned_job_or_404(job_id, user)
    update_job(
        job_id, title=title, description=description, requirements=requirements,
        location=location, remote_policy=remote_policy, experience_level=experience_level,
    )
    job = get_job(job_id)
    index_jobs([{
        "id": str(job_id), "title": job["title"], "description": job["description"], "created_by": user,
        "location": job["location"], "remote_policy": job["remote_policy"], "experience_level": job["experience_level"],
    }])
    if description is not None or requirements is not None:
        _rescore_job_candidates(job_id)  # content changed -> re-evaluate everyone screened against it
    return get_job(job_id)


@app.delete("/jobs/{job_id}")
def api_delete_job(job_id: int, user: str = Depends(get_current_user)):
    _get_owned_job_or_404(job_id, user)
    return {"deleted": delete_job(job_id)}


# --- Candidates ---
@app.post("/candidates")
async def api_create_candidate(name: str = Form(...), file: UploadFile = File(...), user: str = Depends(get_current_user)):
    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        cv_text, pdf_links = extract_text_and_links_from_pdf(tmp_path)
    finally:
        os.remove(tmp_path)

    contact = extract_contact_info(cv_text, pdf_links)
    candidate_id = create_candidate(name, cv_text, user, **contact)

    with open(f"{RESUMES_DIR}/{candidate_id}.pdf", "wb") as f:
        f.write(contents)

    return {"id": candidate_id, "name": name, "cv_length": len(cv_text)}

@app.get("/candidates")
def api_list_candidates(user: str = Depends(get_current_user)):
    return list_candidates(created_by=user)

@app.put("/candidates/{candidate_id}")
async def api_update_candidate(candidate_id: int, name: str = Form(...), file: UploadFile = File(...), user: str = Depends(get_current_user)):
    _get_owned_candidate_or_404(candidate_id, user)

    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        cv_text = extract_text_from_pdf(tmp_path)
    finally:
        os.remove(tmp_path)

    update_candidate_cv(candidate_id, name, cv_text)
    with open(f"{RESUMES_DIR}/{candidate_id}.pdf", "wb") as f:
        f.write(contents)

    prior_screenings = list_screenings_for_candidate(candidate_id)
    for s in prior_screenings:
        job = get_job(s["job_id"])
        if job:
            run_and_save_screening(candidate_id, s["job_id"], cv_text, job["description"])

    return {"id": candidate_id, "name": name, "cv_length": len(cv_text), "rescored_jobs": len(prior_screenings)}

@app.delete("/candidates/{candidate_id}")
def api_delete_candidate(candidate_id: int, user: str = Depends(get_current_user)):
    _get_owned_candidate_or_404(candidate_id, user)
    delete_screenings_for_candidate(candidate_id)
    return {"deleted": delete_candidate(candidate_id)}


@app.get("/candidates/{candidate_id}/matches")
def api_candidate_matches(
    candidate_id: int,
    location: str = Query(None),
    remote_policy: str = Query(None),
    experience_level: str = Query(None),
    user: str = Depends(get_current_user),
):
    candidate = _get_owned_candidate_or_404(candidate_id, user)

    return match_candidate_to_jobs(
        candidate["cv_text"],
        created_by=user,
        top_k=3,
        location=location,
        remote_policy=remote_policy,
        experience_level=experience_level,
    )


# --- Screening ---

@app.post("/jobs/{job_id}/screen")
def api_screen_candidates(job_id: int, candidate_ids: str = Form(...), user: str = Depends(get_current_user)):
    _get_owned_job_or_404(job_id, user)
    ids = [int(x.strip()) for x in candidate_ids.split(",")]
    return screen_candidates_for_job(ids, job_id)


@app.get("/jobs/{job_id}/screenings")
def api_get_screenings(job_id: int, user: str = Depends(get_current_user)):
    _get_owned_job_or_404(job_id, user)
    return list_screenings_for_job(job_id)


# --- Scheduling ---

@app.post("/screenings/propose-times")
def api_propose_times(candidate_name: str = Form(...), job_title: str = Form(...), user: str = Depends(get_current_user)):
    return propose_interview_slots(candidate_name, job_title)

@app.post("/interviews")
def api_create_interview(
    candidate_id: int = Form(...),
    job_id: int = Form(...),
    confirmed_time: str = Form(...),  # ISO format , e.g. "2026-07-28T10:00:00"
    user: str = Depends(get_current_user),
):
    job = _get_owned_job_or_404(job_id, user)
    candidate = _get_owned_candidate_or_404(candidate_id, user)

    interview_id = create_interview(candidate_id, job_id, confirmed_time, user)

    calendar_result = None
    try:
        calendar_result = create_calendar_event(
            candidate_name=candidate["name"],
            candidate_email=candidate.get("email") or "",
            job_title=job["title"],
            start_iso=confirmed_time,
        )
    except Exception as e:
        logger.warning("Calendar event creation failed: %s", e)

    message = build_confirmation_message(candidate["name"], job["title"], confirmed_time)

    return {
        "id": interview_id,
        "confirmed_time": confirmed_time,
        "confirmation_message": message,
        "calendar_link": calendar_result["html_link"] if calendar_result else None,
    }


@app.get("/interviews")
def api_list_interviews(user: str = Depends(get_current_user)):
    return list_interviews_for_hr(user)


@app.get("/interviews/today")
def api_interviews_today(user: str = Depends(get_current_user)):
    return list_interviews_today(user)


# --- Dashboard ---

@app.get("/dashboard/summary")
def api_dashboard_summary(user: str = Depends(get_current_user)):
    profile = get_user_profile(user)
    screenings = list_all_screenings_for_user(user)
    jobs = list_jobs(created_by=user)

    scores = [s["score"] for s in screenings if s["score"] is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    verdict_counts = Counter(s["category"] for s in screenings if s["category"])
    years = [s["years_experience"] for s in screenings if s["years_experience"] is not None]
    avg_years = round(sum(years) / len(years), 1) if years else None

    suitable_skills = []
    for s in screenings:
        if s["category"] == "suitable" and s["skills"]:
            suitable_skills.extend(json_lib.loads(s["skills"]))
    top_skills = Counter(suitable_skills).most_common(8)

    per_job = []
    for job in jobs:
        js = [s for s in screenings if s["job_id"] == job["id"]]
        jscores = [s["score"] for s in js if s["score"] is not None]
        jverdicts = Counter(s["category"] for s in js if s["category"])
        per_job.append({
            "job_title": job["title"],
            "total": len(js),
            "suitable": jverdicts.get("suitable", 0),
            "borderline": jverdicts.get("borderline", 0),
            "not_suitable": jverdicts.get("not_suitable", 0),
            "avg_score": round(sum(jscores) / len(jscores), 1) if jscores else None,
        })

    return {
        "profile": profile,
        "totals": {
            "jobs": len(jobs),
            "screenings": len(screenings),
        },
        "avg_score": avg_score,
        "avg_years_experience": avg_years,
        "verdict_breakdown": {
            "suitable": verdict_counts.get("suitable", 0),
            "borderline": verdict_counts.get("borderline", 0),
            "not_suitable": verdict_counts.get("not_suitable", 0),
        },
        "top_skills": [{"skill": s, "count": c} for s, c in top_skills],
        "per_job": per_job,
    }


# --- Static frontend ---

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/app")
def serve_frontend():
    return FileResponse("frontend/index.html")

# --- job posting  ---
@app.get("/public/jobs/{job_id}")
@limiter.limit("20/minute")
def api_public_job_view(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job["id"], "title": job["title"], "description": job["description"], "requirements": job["requirements"]}

@app.get("/jobs/{job_id}/pending-candidates")
def api_pending_candidates(job_id: int, user: str = Depends(get_current_user)):
    _get_owned_job_or_404(job_id, user)

    all_candidates = list_candidates(created_by=user)
    already_screened_ids = {s["candidate_id"] for s in list_screenings_for_job(job_id)}
    return [
        c for c in all_candidates
        if c.get("applied_job_id") == job_id and c["id"] not in already_screened_ids
    ]
# --- pre-screening ---

@app.get("/public/jobs/{job_id}/prescreening-questions")
@limiter.limit("10/minute")
def api_prescreening_questions(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    questions = generate_prescreening_questions(job["description"], job.get("experience_level"))
    return {"questions": questions}

@app.post("/public/jobs/{job_id}/apply")
@limiter.limit("5/minute")
async def api_public_apply(
    request: Request,
    job_id: int,
    name: str = Form(...),
    file: UploadFile = File(...),
    prescreening_answers: str = Form(""),
    phone: str = Form(""),
    github_url: str = Form(""),
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    contents = await file.read()

    validation_error = validate_pdf_upload(contents)
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        cv_text, pdf_links = extract_text_and_links_from_pdf(tmp_path)
    finally:
        os.remove(tmp_path)

    contact = extract_contact_info(cv_text, pdf_links)
    if phone:
        contact["phone"] = phone  
    if github_url:
        contact["github_url"] = github_url

    prescreening_flags = None
    if prescreening_answers:
        try:
            answers_dict = json_lib.loads(prescreening_answers)
        except (json_lib.JSONDecodeError, TypeError):
            answers_dict = None
        if answers_dict:
            prescreening_flags = json_lib.dumps(analyze_prescreening_answers(answers_dict))

    candidate_id = create_candidate(
        name, cv_text, job["created_by"],
        applied_job_id=job_id, prescreening_answers=prescreening_answers or None,
        prescreening_flags=prescreening_flags,
        **contact,
    )

    with open(f"{RESUMES_DIR}/{candidate_id}.pdf", "wb") as f:
        f.write(contents)

    return {"candidate_id": candidate_id, "job_id": job_id, "message": "Application received."}

# --- candidate details ---
@app.get("/candidates/{candidate_id}/detail")
def api_candidate_detail(candidate_id: int, user: str = Depends(get_current_user)):
    candidate = _get_owned_candidate_or_404(candidate_id, user)

    answers = {}
    if candidate.get("prescreening_answers"):
        try:
            answers = json_lib.loads(candidate["prescreening_answers"])
        except (json_lib.JSONDecodeError, TypeError):
            pass

    flags = {"has_concerns": False, "concerns": []}
    if candidate.get("prescreening_flags"):
        try:
            flags = json_lib.loads(candidate["prescreening_flags"])
        except (json_lib.JSONDecodeError, TypeError):
            pass

    return {
        "id": candidate["id"],
        "name": candidate["name"],
        "cv_text": candidate["cv_text"],
        "email": candidate.get("email"),
        "phone": candidate.get("phone"),
        "linkedin_url": candidate.get("linkedin_url"),
        "github_url": candidate.get("github_url"),
        "prescreening_answers": answers,
        "prescreening_flags": flags,
        "has_resume": os.path.exists(f"{RESUMES_DIR}/{candidate_id}.pdf"),
    }


@app.get("/candidates/{candidate_id}/resume")
def api_candidate_resume(candidate_id: int, user: str = Depends(get_current_user)):
    candidate = _get_owned_candidate_or_404(candidate_id, user)

    path = f"{RESUMES_DIR}/{candidate_id}.pdf"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Resume file not found")

    return FileResponse(path, media_type="application/pdf", filename=f"{candidate['name']}_CV.pdf")

DECISION_BY_ACTION = {
    "preselection_refuse": "preselection_refused",
    "preselection_accept": "preselection_accepted",
    "total_refuse": "rejected",
    "total_accept": "hired",
}


@app.get("/communication/candidates")
def api_communication_candidates(user: str = Depends(get_current_user)):
    return list_communication_queue(user)


@app.post("/communication/screenings/{screening_id}/decide")
def api_communication_decide(screening_id: int, action: str = Form(...), user: str = Depends(get_current_user)):
    screening = get_screening_with_details(screening_id)
    if not screening or screening["job_owner"] != user:
        raise HTTPException(status_code=404, detail="Screening not found")
    if action not in DECISION_BY_ACTION:
        raise HTTPException(status_code=400, detail="Invalid action")

    hr_profile = get_user_profile(user)
    company_name = hr_profile.get("company_name") if hr_profile else ""

    email_content = generate_candidate_email(
        action, screening["candidate_name"], screening["job_title"], company_name
    )

    email_sent = False
    if screening.get("candidate_email"):
        try:
            send_email(screening["candidate_email"], email_content["subject"], email_content["body"])
            email_sent = True
        except Exception as e:
            logger.warning("Failed to send communication email for screening %s: %s", screening_id, e)

    decision = DECISION_BY_ACTION[action]
    update_screening_decision(screening_id, decision)

    if action == "total_accept":
        skills = json_lib.loads(screening["skills"]) if screening.get("skills") else []
        checklist = generate_onboarding_checklist(
            screening["job_title"], screening["job_description"], skills, screening.get("justification", "")
        )
        mark_candidate_hired(screening["candidate_id"], screening["job_id"], json_lib.dumps(checklist))

    return {"ok": True, "decision": decision, "email_sent": email_sent}


# --- onboarding ---

@app.post("/candidates/{candidate_id}/hire")
def api_mark_hired(candidate_id: int, job_id: int = Form(...), user: str = Depends(get_current_user)):
    candidate = _get_owned_candidate_or_404(candidate_id, user)
    job = _get_owned_job_or_404(job_id, user)

    screenings = list_screenings_for_job(job_id)
    this_screening = next((s for s in screenings if s["candidate_id"] == candidate_id), None)
    skills = json_lib.loads(this_screening["skills"]) if this_screening and this_screening.get("skills") else []
    justification = this_screening["justification"] if this_screening else ""

    checklist = generate_onboarding_checklist(job["title"], job["description"], skills, justification)
    mark_candidate_hired(candidate_id, job_id, json_lib.dumps(checklist))

    return {"candidate_id": candidate_id, "checklist": checklist}


@app.get("/onboarding")
def api_list_onboarding(user: str = Depends(get_current_user)):
    hired = list_hired_candidates(user)
    result = []
    for c in hired:
        job = get_job(c["hired_for_job_id"]) if c.get("hired_for_job_id") else None
        checklist = json_lib.loads(c["onboarding_checklist"]) if c.get("onboarding_checklist") else {}
        result.append({
            "candidate_id": c["id"],
            "candidate_name": c["name"],
            "job_title": job["title"] if job else "Unknown",
            "welcome_message": checklist.get("welcome_message", ""),
            "first_day_agenda": checklist.get("first_day_agenda", []),
            "access_checklist": checklist.get("access_checklist", []),
            "checklist": checklist.get("checklist", []),
            "mentor_name": c.get("mentor_name") or "",
        })
    return result


@app.post("/candidates/{candidate_id}/onboarding/toggle-item")
def api_toggle_onboarding_item(
    candidate_id: int, list_name: str = Form(...), index: int = Form(...),
    user: str = Depends(get_current_user),
):
    candidate = _get_owned_candidate_or_404(candidate_id, user)
    if list_name not in ("access_checklist", "checklist"):
        raise HTTPException(status_code=400, detail="Invalid list_name")

    checklist = json_lib.loads(candidate["onboarding_checklist"]) if candidate.get("onboarding_checklist") else {}
    items = checklist.get(list_name, [])
    if index < 0 or index >= len(items):
        raise HTTPException(status_code=400, detail="Invalid item index")

    items[index]["done"] = not items[index].get("done", False)
    checklist[list_name] = items
    update_onboarding_checklist(candidate_id, json_lib.dumps(checklist))

    return checklist


@app.put("/candidates/{candidate_id}/mentor")
def api_update_mentor(candidate_id: int, mentor_name: str = Form(""), user: str = Depends(get_current_user)):
    _get_owned_candidate_or_404(candidate_id, user)
    update_mentor_name(candidate_id, mentor_name)
    return {"ok": True, "mentor_name": mentor_name}