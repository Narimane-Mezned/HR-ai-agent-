import tempfile
import os
from app.agents.scheduling_agent import propose_interview_slots, build_confirmation_message

from fastapi import FastAPI, UploadFile, File, Form

from app.db.jobs import create_job, get_job, list_jobs, update_job, delete_job
from app.db.candidates import create_candidate
from app.db.screenings import list_screenings_for_job
from app.pdf_utils import extract_text_from_pdf
from app.graph.orchestrator import screen_candidates_for_job
from app.agents.scheduling_agent import propose_interview_slots
from app.db.interviews import create_interview, list_interviews_for_hr

app = FastAPI(title="HR AI Agent API")


@app.get("/")
def root():
    return {"status": "running"}



@app.get("/jobs")
def api_list_jobs(created_by: str = None):
    return list_jobs(created_by=created_by)


@app.get("/jobs/{job_id}")
def api_get_job(job_id: int):
    job = get_job(job_id)
    if not job:
        return {"error": "Job not found"}
    return job


@app.post("/jobs")
def api_create_job(title: str = Form(...), description: str = Form(...), requirements: str = Form(""), created_by: str = Form(...)):
    job_id = create_job(title, description, requirements, created_by)
    return get_job(job_id)


@app.put("/jobs/{job_id}")
def api_update_job(job_id: int, title: str = Form(None), description: str = Form(None), requirements: str = Form(None)):
    updated = update_job(job_id, title=title, description=description, requirements=requirements)
    if not updated:
        return {"error": "Job not found"}
    return get_job(job_id)


@app.delete("/jobs/{job_id}")
def api_delete_job(job_id: int):
    deleted = delete_job(job_id)
    return {"deleted": deleted}



@app.post("/candidates")
async def api_create_candidate(name: str = Form(...), file: UploadFile = File(...)):
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        cv_text = extract_text_from_pdf(tmp_path)
    finally:
        os.remove(tmp_path)  

    candidate_id = create_candidate(name, cv_text)
    return {"id": candidate_id, "name": name, "cv_length": len(cv_text)}




@app.post("/jobs/{job_id}/screen")
def api_screen_candidates(job_id: int, candidate_ids: str = Form(...)):
   
    ids = [int(x.strip()) for x in candidate_ids.split(",")]
    results = screen_candidates_for_job(ids, job_id)
    return results


@app.get("/jobs/{job_id}/screenings")
def api_get_screenings(job_id: int):
    return list_screenings_for_job(job_id)



@app.post("/screenings/propose-times")
def api_propose_times(candidate_name: str = Form(...), job_title: str = Form(...)):
    return propose_interview_slots(candidate_name, job_title)



@app.post("/interviews")
def api_create_interview(candidate_id: int = Form(...), job_id: int = Form(...), confirmed_time: str = Form(...), created_by: str = Form(...)):
    from app.db.candidates import get_candidate
    from app.db.jobs import get_job

    interview_id = create_interview(candidate_id, job_id, confirmed_time, created_by)

    candidate = get_candidate(candidate_id)
    job = get_job(job_id)
    message = build_confirmation_message(candidate["name"], job["title"], confirmed_time)

    return {"id": interview_id, "confirmed_time": confirmed_time, "confirmation_message": message}


@app.get("/interviews")
def api_list_interviews(created_by: str):
    return list_interviews_for_hr(created_by)