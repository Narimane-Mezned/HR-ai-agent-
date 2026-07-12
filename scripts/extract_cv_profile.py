"""
Week 1 deliverable: CV text -> structured JSON via one LLM call.
Uses the shared call_llm() function from app/llm_client.py.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from app.llm_client import call_llm

CV_TEXT = """
Amina Belhadj
Backend Software Engineer

Experience:
- Senior Backend Engineer, TechNova (2021-present): built and maintained
  Python/Django microservices handling 2M+ daily requests, migrated
  infrastructure to AWS (ECS, RDS, S3).
- Backend Developer, DataSoft (2019-2021): developed REST APIs in Python,
  worked with PostgreSQL and Redis.

Education: MSc Computer Science, University of Tunis, 2019

Skills: Python, Django, FastAPI, PostgreSQL, AWS, Docker, Redis
"""

SYSTEM_PROMPT = """You are a CV parsing assistant. Given raw CV text, extract
structured information and return ONLY a JSON object with this exact shape,
no text before or after it:
{
  "name": string,
  "years_experience": number,
  "skills": [string],
  "most_recent_title": string
}"""


def main():
    print("Sending CV to the LLM for structured extraction...\n")

    raw_response = call_llm(SYSTEM_PROMPT, CV_TEXT)
    print("DEBUG - raw response was:", repr(raw_response))


    try:
        
        profile = json.loads(raw_response)
    except json.JSONDecodeError:
        print("The model didn't return clean JSON. Raw response was:")
        print(raw_response)
        return

    print("Extracted profile:")
    for key, value in profile.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()