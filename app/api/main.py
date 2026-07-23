import tempfile
import os

from fastapi import FastAPI, UploadFile, File, Form, Depends

from app.db.jobs import create_job, get_job, list_jobs, update_job, delete_job
from app.db.candidates import create_candidate, get_candidate, list_candidates
from app.db.screenings import list_screenings_for_job
from app.pdf_utils import extract_text_from_pdf
from app.graph.orchestrator import screen_candidates_for_job
from app.agents.scheduling_agent import propose_interview_slots, build_confirmation_message
from app.db.interviews import create_interview, list_interviews_for_hr
from app.db.users import create_user, verify_user
from app.auth import create_access_token, get_current_user

app = FastAPI(title="HR AI Agent API")


@app.get("/")
def root():
    return {"status": "running"}




@app.post("/register")
def api_register(username: str = Form(...), password: str = Form(...)):
    user_id = create_user(username, password)
    return {"id": user_id, "username": username}


@app.post("/login")
def api_login(username: str = Form(...), password: str = Form(...)):
    if not verify_user(username, password):
        return {"error": "Invalid username or password"}
    token = create_access_token(username)
    return {"access_token": token, "token_type": "bearer"}



def _get_owned_job_or_error(job_id: int, user: str):
   
    job = get_job(job_id)
    if not job or job["created_by"] != user:
        return None
    return job


@app.get("/jobs")
def api_list_jobs(user: str = Depends(get_current_user)):
    return list_jobs(created_by=user)


@app.get("/jobs/{job_id}")
def api_get_job(job_id: int, user: str = Depends(get_current_user)):
    job = _get_owned_job_or_error(job_id, user)
    if not job:
        return {"error": "Job not found"}
    return job


@app.post("/jobs")
def api_create_job(title: str = Form(...), description: str = Form(...), requirements: str = Form(""), user: str = Depends(get_current_user)):
    job_id = create_job(title, description, requirements, user)
    return get_job(job_id)


@app.put("/jobs/{job_id}")
def api_update_job(job_id: int, title: str = Form(None), description: str = Form(None), requirements: str = Form(None), user: str = Depends(get_current_user)):
    if not _get_owned_job_or_error(job_id, user):
        return {"error": "Job not found"}
    update_job(job_id, title=title, description=description, requirements=requirements)
    return get_job(job_id)


@app.delete("/jobs/{job_id}")
def api_delete_job(job_id: int, user: str = Depends(get_current_user)):
    if not _get_owned_job_or_error(job_id, user):
        return {"error": "Job not found"}
    deleted = delete_job(job_id)
    return {"deleted": deleted}




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



@app.post("/jobs/{job_id}/screen")
def api_screen_candidates(job_id: int, candidate_ids: str = Form(...), user: str = Depends(get_current_user)):
    if not _get_owned_job_or_error(job_id, user):
        return {"error": "Job not found"}
    ids = [int(x.strip()) for x in candidate_ids.split(",")]
    results = screen_candidates_for_job(ids, job_id)
    return results


@app.get("/jobs/{job_id}/screenings")
def api_get_screenings(job_id: int, user: str = Depends(get_current_user)):
    if not _get_owned_job_or_error(job_id, user):
        return {"error": "Job not found"}
    return list_screenings_for_job(job_id)



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