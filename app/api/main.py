import tempfile
import os
import json as json_lib
from collections import Counter

from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.db.jobs import create_job, get_job, list_jobs, update_job, delete_job
from app.db.candidates import (
    create_candidate, get_candidate, list_candidates,
    update_candidate_cv, delete_candidate,
)
from app.db.screenings import (
    list_screenings_for_job, list_screenings_for_candidate,
    list_all_screenings_for_user, delete_screenings_for_candidate,
)
from app.pdf_utils import extract_text_from_pdf
from app.graph.orchestrator import screen_candidates_for_job, run_and_save_screening
from app.agents.scheduling_agent import propose_interview_slots, build_confirmation_message
from app.db.interviews import create_interview, list_interviews_for_hr
from app.db.users import create_user, verify_user, get_user_profile
from app.auth import create_access_token, get_current_user
from app.rag.job_store import index_jobs, find_matching_jobs

app = FastAPI(title="HR AI Agent API")


@app.get("/")
def root():
    return {"status": "running"}


# --- Auth ---

@app.post("/register")
def api_register(username: str = Form(...), password: str = Form(...), company_name: str = Form(...), email: str = Form("")):
    normalized = username.strip().lower()
    create_user(username, password, company_name, email)
    token = create_access_token(normalized)  # auto-login: no separate login step needed
    return {"access_token": token, "token_type": "bearer", "username": normalized}


@app.post("/login")
def api_login(username: str = Form(...), password: str = Form(...)):
    if not verify_user(username, password):
        return {"error": "Invalid username or password"}
    normalized = username.strip().lower()
    token = create_access_token(normalized)  # token always uses normalized identity
    return {"access_token": token, "token_type": "bearer"}


# --- Jobs ---

def _get_owned_job_or_error(job_id: int, user: str):
    job = get_job(job_id)
    if not job or job["created_by"] != user:
        return None
    return job


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
    job = _get_owned_job_or_error(job_id, user)
    return job if job else {"error": "Job not found"}


@app.post("/jobs")
def api_create_job(title: str = Form(...), description: str = Form(...), requirements: str = Form(""), user: str = Depends(get_current_user)):
    job_id = create_job(title, description, requirements, user)
    job = get_job(job_id)
    index_jobs([{"id": str(job_id), "title": title, "description": description}])
    return job


@app.put("/jobs/{job_id}")
def api_update_job(job_id: int, title: str = Form(None), description: str = Form(None), requirements: str = Form(None), user: str = Depends(get_current_user)):
    if not _get_owned_job_or_error(job_id, user):
        return {"error": "Job not found"}
    update_job(job_id, title=title, description=description, requirements=requirements)
    job = get_job(job_id)
    index_jobs([{"id": str(job_id), "title": job["title"], "description": job["description"]}])
    if description is not None or requirements is not None:
        _rescore_job_candidates(job_id)  # content changed -> re-evaluate everyone screened against it
    return get_job(job_id)


@app.delete("/jobs/{job_id}")
def api_delete_job(job_id: int, user: str = Depends(get_current_user)):
    if not _get_owned_job_or_error(job_id, user):
        return {"error": "Job not found"}
    return {"deleted": delete_job(job_id)}


# --- Candidates ---

@app.post("/candidates")
async def api_create_candidate(name: str = Form(...), file: UploadFile = File(...), user: str = Depends(get_current_user)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        cv_text = extract_text_from_pdf(tmp_path)
    finally:
        os.remove(tmp_path)

    candidate_id = create_candidate(name, cv_text, user)
    return {"id": candidate_id, "name": name, "cv_length": len(cv_text)}


@app.get("/candidates")
def api_list_candidates(user: str = Depends(get_current_user)):
    return list_candidates(created_by=user)


@app.put("/candidates/{candidate_id}")
async def api_update_candidate(candidate_id: int, name: str = Form(...), file: UploadFile = File(...), user: str = Depends(get_current_user)):
    candidate = get_candidate(candidate_id)
    if not candidate or candidate.get("created_by") != user:
        return {"error": "Candidate not found"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        cv_text = extract_text_from_pdf(tmp_path)
    finally:
        os.remove(tmp_path)

    update_candidate_cv(candidate_id, name, cv_text)

    # CV changed -> rescore this candidate against every job they were previously screened for
    prior_screenings = list_screenings_for_candidate(candidate_id)
    for s in prior_screenings:
        job = get_job(s["job_id"])
        if job:
            run_and_save_screening(candidate_id, s["job_id"], cv_text, job["description"])

    return {"id": candidate_id, "name": name, "cv_length": len(cv_text), "rescored_jobs": len(prior_screenings)}


@app.delete("/candidates/{candidate_id}")
def api_delete_candidate(candidate_id: int, user: str = Depends(get_current_user)):
    candidate = get_candidate(candidate_id)
    if not candidate or candidate.get("created_by") != user:
        return {"error": "Candidate not found"}
    delete_screenings_for_candidate(candidate_id)
    return {"deleted": delete_candidate(candidate_id)}


@app.get("/candidates/{candidate_id}/matches")
def api_candidate_matches(candidate_id: int, user: str = Depends(get_current_user)):
    candidate = get_candidate(candidate_id)
    if not candidate or candidate.get("created_by") != user:
        return {"error": "Candidate not found"}

    from app.agents.screening_agent import screen_candidate
    retrieved = find_matching_jobs(candidate["cv_text"], top_k=10)

    results = []
    for jm in retrieved:
        job = get_job(int(jm["id"]))
        if not job or job["created_by"] != user:
            continue
        result = screen_candidate(candidate["cv_text"], job["description"])
        result["job_id"] = job["id"]
        result["job_title"] = job["title"]
        results.append(result)
        if len(results) >= 3:
            break
    return results


# --- Screening ---

@app.post("/jobs/{job_id}/screen")
def api_screen_candidates(job_id: int, candidate_ids: str = Form(...), user: str = Depends(get_current_user)):
    if not _get_owned_job_or_error(job_id, user):
        return {"error": "Job not found"}
    ids = [int(x.strip()) for x in candidate_ids.split(",")]
    return screen_candidates_for_job(ids, job_id)


@app.get("/jobs/{job_id}/screenings")
def api_get_screenings(job_id: int, user: str = Depends(get_current_user)):
    if not _get_owned_job_or_error(job_id, user):
        return {"error": "Job not found"}
    return list_screenings_for_job(job_id)


# --- Scheduling ---

@app.post("/screenings/propose-times")
def api_propose_times(candidate_name: str = Form(...), job_title: str = Form(...), user: str = Depends(get_current_user)):
    return propose_interview_slots(candidate_name, job_title)


@app.post("/interviews")
def api_create_interview(candidate_id: int = Form(...), job_id: int = Form(...), confirmed_time: str = Form(...), user: str = Depends(get_current_user)):
    if not _get_owned_job_or_error(job_id, user):
        return {"error": "Job not found"}
    interview_id = create_interview(candidate_id, job_id, confirmed_time, user)
    candidate = get_candidate(candidate_id)
    job = get_job(job_id)
    message = build_confirmation_message(candidate["name"], job["title"], confirmed_time)
    return {"id": interview_id, "confirmed_time": confirmed_time, "confirmation_message": message}


@app.get("/interviews")
def api_list_interviews(user: str = Depends(get_current_user)):
    return list_interviews_for_hr(user)


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
def api_public_job_view(job_id: int):
    job = get_job(job_id)
    if not job:
        return {"error": "Job not found"}
    return {"id": job["id"], "title": job["title"], "description": job["description"], "requirements": job["requirements"]}


@app.post("/public/jobs/{job_id}/apply")
async def api_public_apply(job_id: int, name: str = Form(...), file: UploadFile = File(...)):
    job = get_job(job_id)
    if not job:
        return {"error": "Job not found"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        cv_text = extract_text_from_pdf(tmp_path)
    finally:
        os.remove(tmp_path)

    candidate_id = create_candidate(name, cv_text, job["created_by"], applied_job_id=job_id)
    return {"candidate_id": candidate_id, "job_id": job_id, "message": "Application received."}
    
@app.get("/jobs/{job_id}/pending-candidates")
def api_pending_candidates(job_id: int, user: str = Depends(get_current_user)):
    if not _get_owned_job_or_error(job_id, user):
        return {"error": "Job not found"}

    all_candidates = list_candidates(created_by=user)
    already_screened_ids = {s["candidate_id"] for s in list_screenings_for_job(job_id)}
    return [
        c for c in all_candidates
        if c.get("applied_job_id") == job_id and c["id"] not in already_screened_ids
    ]