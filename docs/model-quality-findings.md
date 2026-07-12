# Model quality findings — Screening Agent

Informal but evidence-based observations from manually testing `screen_candidate()`
against a real CV across multiple job descriptions and free-tier models on
OpenRouter. These are early, informal notes from initial development and manual
testing — not a formal evaluation. A proper evaluation pipeline (labeled test set,
repeatable scoring, multiple runs per case) is planned as a next step.

## Test setup

- **CV**: one real candidate CV (AI/Data Engineering student, strong project-based
  background: RAG chatbot, ML classifiers, full-stack projects — no traditional
  work history).
- **Method**: same CV run against several job descriptions of varying match
  difficulty, checking (a) score/verdict reasonableness, (b) skills list accuracy
  against the literal CV text, (c) justification quality.

## Results

| Job description                                                                              | Model                                                                  | Run | Score | Verdict      | Skills accuracy                                                                            | Notes                                                                                        |
| -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | --- | ----- | ------------ | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| AI/Backend internship (direct keyword match: Python, FastAPI, RAG)                           | `meta-llama/llama-3.3-70b-instruct:free`-class (via `openrouter/free`) | 1   | 95    | Suitable     | Correct, complete                                                                          | Strong, well-grounded result                                                                 |
| Senior Java Backend Engineer (clear mismatch)                                                | same                                                                   | 1   | 15    | Not suitable | Correct, complete                                                                          | Correctly identified real gaps (years, no Spring Boot)                                       |
| Backend Developer, Node.js/Express (partial overlap: has NestJS, not Express)                | reasoning model (via `openrouter/free`)                                | 1   | 35    | Not suitable | Correct — explicitly distinguished NestJS from Node.js/Express rather than conflating them | Best reasoning observed                                                                      |
| ML Engineer (requires inferring "production deployment" from AlzheiCare project description) | `openai/gpt-oss-20b:free` (pinned)                                     | 1   | 0     | Not suitable | Missed everything except "Python"                                                          | Failed badly — did not connect described work to the requirement                             |
| ML Engineer — same exact input, rerun                                                        | `openai/gpt-oss-20b:free` (pinned)                                     | 2   | 25    | Not suitable | Correct, complete                                                                          | Skills fine this run; still never credited AlzheiCare as production ML deployment experience |
| AI/Backend internship (direct match, rerun for comparison)                                   | `openai/gpt-oss-20b:free` (pinned)                                     | 1   | 85    | Suitable     | Correct, complete                                                                          | Confirms direct matching is reliable even on the smaller model                               |

## Key takeaways

1. **Direct keyword/skill matching is reliable** across models tested, including
   the smaller `gpt-oss-20b:free`. When required skills are stated in similar
   language to the CV, scoring and skills extraction are consistently accurate.

2. **Indirect/inferred matching is unreliable, and specifically weak on smaller
   models.** The clearest example: the CV describes a real production ML
   deployment (FastAPI service, port 8001, real inference bug fixes, consumed by
   another backend) without ever using the phrase "production deployment" or
   "MLOps." The smaller model never credited this as relevant experience, even
   though a human reviewer clearly would. This is a reasoning/inference gap, not
   a formatting or extraction problem.

3. **Run-to-run variance is real, even at low temperature.** The exact same CV +
   job description produced a 0 on one run and a 25 on an identical rerun with
   the same model. Any single evaluation of a model's quality should be treated
   as one data point, not a verdict — this is part of the motivation for building
   a proper evaluation pipeline (multiple runs, labeled ground truth) rather than
   relying on spot-checks like these.

4. **Free-tier routing introduces its own failure modes**, separate from model
   capability: the `openrouter/free` auto-router occasionally routed requests to
   a moderation-only model that returned just a safety verdict instead of an
   actual answer (e.g. `"User Safety: unsafe\nSafety Categories: PII/Privacy"`),
   triggered by the CV's real email/phone number. Fixed by (a) redacting PII
   before sending CV text to the LLM (`redact_pii()` in `pdf_utils.py`), and
   (b) pinning to a specific named model instead of the auto-router, for
   predictability.

## Implication for model routing strategy

This motivates a concrete routing strategy rather than a hypothetical one:
smaller/cheaper models are trustworthy for direct skill/keyword matching, but
final suitability decisions — especially for CVs with project-based (rather than
job-title-based) experience — should be routed to a stronger model, or at minimum
flagged for human review when the CV lacks direct keyword overlap with the job
description.
