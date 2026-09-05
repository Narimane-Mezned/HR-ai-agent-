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

    
    {
        "case_id": "synthetic_marketing_strong_match",
        "cv_text": "Digital marketing manager, 6 years experience. Led SEO strategy, managed a $500k paid ads budget across Google and Meta, ran A/B tests on landing pages, built email nurture campaigns with a 22% open rate.",
        "job_description": "Digital Marketing Manager. Requirements: 5+ years digital marketing experience, SEO, paid advertising (Google/Meta), A/B testing, email marketing campaigns.",
        "expected_score_range": (75, 100),
        "expected_verdict": "Suitable",
        "notes": "Direct, unambiguous overlap in a non-tech field.",
    },
    {
        "case_id": "synthetic_marketing_no_match",
        "cv_text": "Mechanical engineer with 4 years designing HVAC systems. Proficient in AutoCAD and SolidWorks. No marketing or advertising experience.",
        "job_description": "Digital Marketing Manager. Requirements: 5+ years digital marketing experience, SEO, paid advertising (Google/Meta), A/B testing, email marketing campaigns.",
        "expected_score_range": (0, 20),
        "expected_verdict": "Not suitable",
        "notes": "Completely unrelated field — unambiguous reject.",
    },
    {
        "case_id": "synthetic_sales_strong_match",
        "cv_text": "B2B sales representative, 4 years. Consistently exceeded quota by 120%, managed a pipeline of 50+ enterprise accounts using Salesforce, closed deals averaging $80k ARR.",
        "job_description": "Enterprise Sales Representative. Requirements: 3+ years B2B sales, CRM experience (Salesforce preferred), track record of exceeding quota, enterprise deal closing.",
        "expected_score_range": (75, 100),
        "expected_verdict": "Suitable",
        "notes": "Direct match, quantified achievements present in CV.",
    },
    {
        "case_id": "synthetic_customer_support_partial_match",
        "cv_text": "Retail store associate, 2 years, handled customer complaints and returns in person. No experience with support ticketing software, phone support, or remote work tools.",
        "job_description": "Remote Customer Support Specialist. Requirements: 2+ years customer support experience, ticketing systems (Zendesk/Intercom), phone and chat support, comfortable working remotely.",
        "expected_score_range": (20, 45),
        "expected_verdict": "Not suitable",
        "notes": "Some relevant soft skills (handling complaints) but missing the specific tools and channel experience required.",
    },
    {
        "case_id": "synthetic_finance_strong_match",
        "cv_text": "Financial analyst, 5 years. Built financial models in Excel, prepared quarterly forecasts, performed variance analysis, presented findings to senior leadership, CFA Level II candidate.",
        "job_description": "Senior Financial Analyst. Requirements: 4+ years financial analysis, advanced Excel modeling, forecasting, variance analysis, CFA a plus.",
        "expected_score_range": (75, 100),
        "expected_verdict": "Suitable",
        "notes": "Direct overlap plus a stated bonus qualification (CFA).",
    },
    {
        "case_id": "synthetic_finance_junior_underqualified",
        "cv_text": "Recent accounting graduate, one unpaid internship doing basic bookkeeping in QuickBooks. No forecasting or modeling experience.",
        "job_description": "Senior Financial Analyst. Requirements: 4+ years financial analysis, advanced Excel modeling, forecasting, variance analysis, CFA a plus.",
        "expected_score_range": (0, 25),
        "expected_verdict": "Not suitable",
        "notes": "Real years-of-experience mismatch — a 'senior' role against an entry-level profile.",
    },
    {
        "case_id": "synthetic_product_management_strong_match",
        "cv_text": "Product manager, 4 years, owned the roadmap for a B2B SaaS product, ran user interviews, wrote PRDs, worked closely with engineering on sprint planning, shipped features used by 10k+ customers.",
        "job_description": "Product Manager. Requirements: 3+ years product management, roadmap ownership, PRD writing, cross-functional collaboration with engineering, user research.",
        "expected_score_range": (75, 100),
        "expected_verdict": "Suitable",
        "notes": "Direct, well-documented match with quantified impact.",
    },
    {
        "case_id": "synthetic_ux_design_partial_match",
        "cv_text": "Graphic designer, 3 years, mostly print and branding work (logos, brochures). Some Figma experience but no user research, wireframing, or usability testing background.",
        "job_description": "Senior UX Designer. Requirements: 4+ years UX design, user research, wireframing/prototyping in Figma, usability testing, collaborating with product and engineering.",
        "expected_score_range": (20, 45),
        "expected_verdict": "Not suitable",
        "notes": "Adjacent skill (Figma) but the core UX-specific competencies (research, testing) are absent.",
    },
    {
        "case_id": "synthetic_nursing_strong_match",
        "cv_text": "Registered nurse, 6 years in a hospital ICU. ACLS and BLS certified, experienced with ventilator management and critical care patient monitoring.",
        "job_description": "ICU Registered Nurse. Requirements: RN license, 3+ years ICU experience, ACLS/BLS certification, critical care patient monitoring.",
        "expected_score_range": (80, 100),
        "expected_verdict": "Suitable",
        "notes": "Confirms the screening logic generalizes well outside tech/business roles.",
    },
    {
        "case_id": "synthetic_teaching_strong_match",
        "cv_text": "High school math teacher, 7 years, certified educator, designed curriculum for AP Calculus, improved average student pass rate from 68% to 89% over three years.",
        "job_description": "High School Math Teacher. Requirements: teaching certification, 3+ years classroom experience, curriculum design, demonstrated student outcome improvement.",
        "expected_score_range": (80, 100),
        "expected_verdict": "Suitable",
        "notes": "Direct match with a quantified outcome.",
    },
    {
        "case_id": "synthetic_legal_partial_match",
        "cv_text": "Paralegal, 2 years, mostly document filing and scheduling for a small family-law practice. No experience drafting contracts or conducting legal research for corporate clients.",
        "job_description": "Corporate Paralegal. Requirements: 3+ years paralegal experience in corporate law, contract drafting, legal research, due diligence support.",
        "expected_score_range": (20, 45),
        "expected_verdict": "Not suitable",
        "notes": "Same job title (paralegal) but a different legal specialty and missing core tasks — tests that the model doesn't over-credit a matching job title alone.",
    },
    {
        "case_id": "synthetic_hr_recruiting_strong_match",
        "cv_text": "Technical recruiter, 4 years, sourced and screened candidates for engineering roles, managed the full interview pipeline in Greenhouse, built relationships with hiring managers.",
        "job_description": "Technical Recruiter. Requirements: 3+ years recruiting for technical roles, ATS experience (Greenhouse/Lever), sourcing, interview pipeline management.",
        "expected_score_range": (75, 100),
        "expected_verdict": "Suitable",
        "notes": "Direct match — relevant since this is the same domain as the platform itself.",
    },
    {
        "case_id": "synthetic_devops_strong_match",
        "cv_text": "DevOps engineer, 4 years, built CI/CD pipelines with GitHub Actions, managed AWS infrastructure with Terraform, ran Kubernetes clusters in production, on-call for incident response.",
        "job_description": "DevOps Engineer. Requirements: 3+ years DevOps experience, CI/CD pipelines, infrastructure as code (Terraform), Kubernetes, cloud platform experience (AWS/GCP/Azure).",
        "expected_score_range": (80, 100),
        "expected_verdict": "Suitable",
        "notes": "Direct keyword and concept overlap.",
    },
    {
        "case_id": "synthetic_devops_overqualified",
        "cv_text": "Principal infrastructure engineer, 12 years, led platform architecture for a company running 500+ microservices, designed the org's entire cloud migration strategy, manages a team of 8 engineers.",
        "job_description": "Junior DevOps Engineer. Requirements: 0-2 years experience, willingness to learn CI/CD and cloud basics, entry-level role with mentorship provided.",
        "expected_score_range": (30, 65),
        "expected_verdict": "Borderline",
        "notes": "Deliberately overqualified case — tests whether the model recognizes a seniority mismatch in the other direction (too senior, likely to be unhappy/overpriced for the role) rather than scoring it as an automatic 'Suitable' just because skills technically exceed requirements.",
    },
    {
        "case_id": "synthetic_career_changer_indirect_reasoning",
        "cv_text": "Former high school physics teacher, 8 years, transitioning to software engineering after completing a 6-month intensive coding bootcamp. Built three personal full-stack projects using React and Node.js during the program; no professional software engineering job history yet.",
        "job_description": "Junior Full-Stack Developer. Requirements: 0-2 years professional experience OR a strong portfolio of self-directed projects, React, Node.js, ability to learn quickly.",
        "expected_score_range": (40, 70),
        "expected_verdict": "Borderline",
        "notes": "Hard case: requires crediting bootcamp projects as legitimate experience per the job's own stated 'or a strong portfolio' clause, without a traditional job history — echoes the Week 2 'indirect reasoning' finding in a new context.",
    },
    {
        "case_id": "synthetic_data_science_indirect_reasoning",
        "cv_text": "Academic researcher, PhD in computational biology, 5 years publishing peer-reviewed papers using Python for statistical modeling, hypothesis testing, and building predictive models on genomic datasets. Never held an industry 'data scientist' job title.",
        "job_description": "Data Scientist. Requirements: 3+ years applying statistical modeling and predictive analytics to real-world data, strong Python skills, experience communicating findings to stakeholders.",
        "expected_score_range": (45, 75),
        "expected_verdict": "Borderline",
        "notes": "Hard case: the CV never uses the words 'data scientist' or 'stakeholders', but the underlying skills (statistical modeling, predictive models, Python, real datasets) map closely to the job — tests whether the model connects substance over exact terminology, or under-credits due to a mismatched job title.",
    },
    {
        "case_id": "synthetic_student_projects_only",
        "cv_text": "Third-year computer science student. No internships or paid work yet. Built a personal project implementing a REST API in FastAPI with a SQLite backend, and a class project training a small image classifier in PyTorch.",
        "job_description": "Backend Engineering Intern. Requirements: currently pursuing a CS degree, familiarity with a backend framework (FastAPI/Django/Flask), basic understanding of databases, eagerness to learn.",
        "expected_score_range": (55, 85),
        "expected_verdict": "Borderline",
        "notes": "Echoes the project's own documented weak spot: candidates who are students with only project-based experience and no traditional job history.",
    },
    {
        "case_id": "synthetic_long_verbose_cv",
        "cv_text": (
            "Software engineer with 5 years of professional experience across multiple companies and roles. "
            "Started career as a junior developer maintaining a legacy PHP monolith, then transitioned to a mid-level "
            "role building REST APIs in Python with Flask, then most recently spent two years as a senior backend "
            "engineer at a fintech startup building services in FastAPI, integrating with PostgreSQL and Redis, "
            "writing extensive unit and integration tests with pytest, and mentoring two junior engineers. "
            "Outside of work, maintains several open-source Python libraries with a combined 400+ GitHub stars, "
            "regularly writes technical blog posts about API design, and has spoken at two regional Python meetups "
            "about testing strategies. Also has some exposure to machine learning through a self-directed project "
            "building a small recommendation system using scikit-learn, though this was not part of any paid role."
        ),
        "job_description": SYNTHETIC_JOB,
        "expected_score_range": (70, 100),
        "expected_verdict": "Suitable",
        "notes": "Robustness check: a long, verbose CV with the real signal (Python, FastAPI, some ML) buried among a lot of narrative detail and tangential achievements.",
    },
    {
        "case_id": "synthetic_mixed_relevant_irrelevant_skills",
        "cv_text": "Full-stack developer, 3 years. Built internal tools using Python and FastAPI. Also spent significant time on unrelated work: managing the company's physical office network hardware and doing occasional graphic design for internal newsletters.",
        "job_description": SYNTHETIC_JOB,
        "expected_score_range": (35, 65),
        "expected_verdict": "Borderline",
        "notes": "Real relevant experience (Python/FastAPI) is present but diluted by a lot of unrelated work and no RAG/ML experience at all — tests that the model weighs relevance rather than just total years worked.",
    },
    {
        "case_id": "synthetic_keyword_stuffing_should_not_fool_model",
        "cv_text": "Aspiring professional. Skills: Python Python Python, FastAPI, machine learning, RAG, embeddings, AI, deep learning. No projects, no work history, no education listed.",
        "job_description": SYNTHETIC_JOB,
        "expected_score_range": (0, 35),
        "expected_verdict": "Not suitable",
        "notes": "Adversarial-style case: keyword list with zero substantiating experience, projects, or education — tests that the model (and the hallucination guardrail) doesn't reward keyword-stuffing alone.",
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