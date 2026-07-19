import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.pdf_utils import extract_text_from_pdf


SYNTHETIC_JOB = "Python, FastAPI, RAG/embeddings experience, machine learning fundamentals."

SYNTHETIC_CASES = [
    {
        "case_id": "synthetic_strong_match",
        "cv_text": "Experienced Python developer. Built RAG pipelines using FastAPI and FAISS. Machine learning background with TensorFlow.",
        "job_description": SYNTHETIC_JOB,
        "expected_score_range": (75, 100),
        "expected_verdict": "Suitable",
        "notes": "Deliberately overlaps almost entirely with job requirements.",
    },
    {
        "case_id": "synthetic_weak_match",
        "cv_text": "Marketing specialist with 5 years experience in social media campaigns and content strategy. No programming background.",
        "job_description": SYNTHETIC_JOB,
        "expected_score_range": (0, 25),
        "expected_verdict": "Not suitable",
        "notes": "Zero technical overlap — unambiguous reject case.",
    },
    {
        "case_id": "synthetic_partial_match",
        "cv_text": "Java developer with 3 years experience in Spring Boot. Familiar with basic Python scripting, no ML experience.",
        "job_description": SYNTHETIC_JOB,
        "expected_score_range": (10, 40),
        "expected_verdict": "Not suitable",
        "notes": "Some overlap (Python scripting) but missing core requirements (FastAPI, RAG, ML).",
    },
]


REAL_CV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sample_cvs", "mon_cv.pdf")

REAL_CV_CASES = [
    {
        "case_id": "real_cv_direct_match",
        "job_description": "AI/Backend Engineer Internship. Requirements: Python, FastAPI, RAG/embeddings experience, machine learning fundamentals.",
        "expected_score_range": (70, 100),
        "expected_verdict": "Suitable",
        "notes": "Direct keyword overlap — consistently scored 85-95 across multiple prior runs.",
    },
    {
        "case_id": "real_cv_clear_mismatch",
        "job_description": "Senior Java Backend Engineer. Requirements: 8+ years Java/Spring Boot experience, Kubernetes, microservices at scale, no AI/ML background needed.",
        "expected_score_range": (0, 30),
        "expected_verdict": "Not suitable",
        "notes": "Real years-of-experience and stack mismatch — consistently scored 15-20 across prior runs.",
    },
    {
        "case_id": "real_cv_indirect_reasoning_required",
        "job_description": "Machine Learning Engineer. Requirements: 3+ years production ML experience, MLOps practices (CI/CD, model monitoring, containerization), Python, hands-on experience deploying models to production environments.",
        "expected_score_range": (30, 60),
        "expected_verdict": "Borderline",
        "notes": "The hard case from Week 2's findings: requires connecting the AlzheiCare project's real production ML deployment to the job's phrasing, without shared keywords. Prior runs varied 0-35 depending on model/run — this case is EXPECTED to show high variance; that variance is itself the finding.",
    },
]


def load_eval_cases() -> list[dict]:
    
    real_cv_text = extract_text_from_pdf(REAL_CV_PATH)

    resolved_real_cases = []
    for case in REAL_CV_CASES:
        resolved_case = {**case, "cv_text": real_cv_text}
        resolved_real_cases.append(resolved_case)

    return SYNTHETIC_CASES + resolved_real_cases