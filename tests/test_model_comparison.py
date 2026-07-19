
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.jobs import create_job
from app.db.candidates import create_candidate
from app.agents.screening_agent import screen_candidate
from app.db.call_logs import get_call_summary
from app.config import OPENROUTER_MODEL_CHEAP



job_id = create_job(
    'AI Backend Engineer Intern',
    'Python, FastAPI, RAG/embeddings experience, machine learning fundamentals.',
    'Python, FastAPI, RAG',
    'Narimane'
)

candidates = [
    ('Strong Match', 'Experienced Python developer. Built RAG pipelines using FastAPI and FAISS. Machine learning background with TensorFlow.'),
    ('Weak Match', 'Marketing specialist with 5 years experience in social media campaigns and content strategy. No programming background.'),
    ('Partial Match', 'Java developer with 3 years experience in Spring Boot. Familiar with basic Python scripting, no ML experience.'),
]

job_description = 'Python, FastAPI, RAG/embeddings experience, machine learning fundamentals.'

models_to_compare = [
    'openai/gpt-oss-20b:free',
    'meta-llama/llama-3.3-70b-instruct:free',
]

for model in models_to_compare:
    print(f"\n=== Testing model: {model} ===")
    for name, cv_text in candidates:
        result = screen_candidate(cv_text, job_description, model=model)
        print(f"{name}: score={result.get('score')}, verdict={result.get('verdict')}")

    print("Cumulative call summary so far:", get_call_summary())