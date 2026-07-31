# HR AI Agent

A multi-agent HR recruitment platform built during a summer internship — AI-powered CV screening, candidate-job matching, interview scheduling, and onboarding, wrapped in a real web application with authentication and per-user data isolation.

Built as a focused implementation of the "AI Agents – Conception et orchestration" internship brief (RAG, classification, content generation, automation, advanced prompt engineering, multi-agent orchestration, cost/quality optimization, evaluation pipelines).

---

## What it does

1. **HR posts a job** — internal creation, or a real public application link (no login required for candidates)
2. **Candidates apply** via the public link, PDF CV + a few AI-generated pre-screening questions
3. **Screening Agent** parses the CV, scores it against the job, with hallucination guardrails and PII redaction
4. **Matching Agent** (RAG) finds the best-fit jobs for any candidate, or the best-fit candidates for any job
5. **Scheduling Agent** proposes interview times and books a real Google Calendar event
6. **Onboarding Agent** generates a personalized welcome checklist once a candidate is marked hired
7. **Dashboard** shows pipeline funnel, average scores, and top skills across the whole account

All of this is scoped per logged-in HR officer — strict authentication and data isolation, verified with a real second account seeing zero cross-account data.

---

## Architecture

```
hr-ai-agent/
├── app/
│   ├── agents/            # screening, matching (via RAG), scheduling, onboarding, pre-screening
│   ├── graph/               # LangGraph orchestrator — screens, categorizes, persists
│   ├── rag/                   # ChromaDB job indexing/retrieval
│   ├── db/                     # SQLite CRUD for every entity + migrations
│   ├── api/                     # FastAPI app — every HTTP endpoint
│   ├── llm_client.py              # single point every LLM call goes through (logging, retries, model routing)
│   ├── auth.py                     # JWT issuing/verification
│   ├── calendar_service.py          # Google Calendar OAuth + event creation
│   └── pdf_utils.py                  # PDF text extraction, PII redaction, contact-info extraction
├── frontend/                # vanilla JS (ES modules) — services / pages / components / router
├── tests/                   # labeled eval dataset, deterministic checks, LLM-as-judge, eval runner
├── docs/                    # findings, project log
└── requirements.txt
```

**Backend**: Python, FastAPI, LangGraph, ChromaDB, SQLite, bcrypt + JWT.
**Frontend**: vanilla JavaScript (ES modules).
**LLM provider**: OpenRouter (free-tier models throughout, by deliberate choice — see [Known limitations](#known-limitations)).

---

## Setup

```bash
git clone https://github.com/Narimane-Mezned/HR-ai-agent-.git
cd hr-ai-agent
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your-key-here
OPENROUTER_MODEL_CHEAP=openrouter/free
```

Initialize the database:
```bash
python -c "from app.db.database import init_db; init_db()"
```

### Optional: Google Calendar sync
Real interview scheduling requires a Google Cloud project with the Calendar API enabled and OAuth credentials (`credentials.json` in the project root). Without it, interviews still save internally, just without a real calendar event. See `docs/project-log.md` for the exact setup steps taken.

### Run it
```bash
uvicorn app.api.main:app --reload
```
Open `http://127.0.0.1:8000/app` — register an account and go.

---

## Mapped against the brief

| Requirement | Where |
|---|---|
| RAG | `app/rag/job_store.py`, `app/agents/matching_agent.py` |
| Classification | `app/agents/screening_agent.py` |
| Content generation | `app/agents/scheduling_agent.py`, `app/agents/onboarding_agent.py` |
| Automation | Batch screening, auto-rescoring on job/CV updates |
| Advanced prompt engineering | Grounding rules, hallucination guardrails, retry-with-backoff, reasoning-trace suppression |
| Multi-agent orchestration | `app/graph/orchestrator.py` (LangGraph, conditional routing) |
| Cost/quality optimization | `app/db/call_logs.py`, response caching, documented model comparison |
| Evaluation pipelines | `tests/` — labeled dataset, deterministic checks, LLM-as-judge |

Full build log, every bug found and fixed, and every design decision with its reasoning: [`docs/project-log.md`](docs/project-log.md).

---

## Known limitations

- **Free-tier LLMs only**, by deliberate choice — documented reliability trade-offs (rate limits, occasional malformed output) in the project log, mitigated with retries, caching, and code-level guardrails rather than paid-tier reliability.
- **Small formal evaluation set** (6 labeled cases) — proves the evaluation pipeline works correctly, not a statistically large benchmark.
- **PDF text extraction only** — scanned/image-based CVs aren't supported (no OCR).
- **No real job-board API integrations** — "automated job posting" means a real shareable application link, not multi-channel distribution to LinkedIn/Indeed (those require enterprise partner access, investigated and found infeasible for this project).
- **Shared Google Calendar authorization** — one OAuth-authorized calendar for the whole platform, not per-HR-officer login to their own calendar; a real production deployment would need proper per-user OAuth.

---

## Credits

Built by Narimane Mezned during a summer internship. Reference inspiration: Welyne, Kakoo, Agentova, Limova, Sintra.
