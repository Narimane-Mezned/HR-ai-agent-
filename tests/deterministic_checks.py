def check_valid_structure(result: dict) -> tuple[bool, str]:
   
    required_fields = ["name", "years_experience", "skills", "score", "verdict", "justification"]
    missing = [f for f in required_fields if f not in result]

    if missing:
        return False, f"Missing fields: {missing}"

    if result["verdict"] == "Error":
        return False, "Result is an error/parse-failure placeholder"

    return True, "OK"


def check_score_in_range(result: dict) -> tuple[bool, str]:
    
    score = result.get("score")

    if score is None:
        return False, "Score is None"

    if not isinstance(score, (int, float)):
        return False, f"Score is not numeric: {type(score)}"

    if not (0 <= score <= 100):
        return False, f"Score out of range: {score}"

    return True, "OK"


def check_skills_grounded(result: dict, cv_text: str) -> tuple[bool, str]:
    
    skills = result.get("skills", [])
    cv_lower = cv_text.lower()

    ungrounded = [s for s in skills if s.lower() not in cv_lower]

    if ungrounded:
        return False, f"Skills not found in CV text: {ungrounded}"

    return True, "OK"


def check_verdict_matches_score(result: dict) -> tuple[bool, str]:
    
    score = result.get("score")
    verdict = result.get("verdict")

    if score is None or verdict is None:
        return False, "Missing score or verdict"

    if score >= 70 and verdict != "Suitable":
        return False, f"Score {score} but verdict is '{verdict}', expected 'Suitable'"
    if 40 <= score < 70 and verdict != "Borderline":
        return False, f"Score {score} but verdict is '{verdict}', expected 'Borderline'"
    if score < 40 and verdict != "Not suitable":
        return False, f"Score {score} but verdict is '{verdict}', expected 'Not suitable'"

    return True, "OK"


def run_all_deterministic_checks(result: dict, cv_text: str) -> dict:
    
    checks = {
        "valid_structure": check_valid_structure(result),
        "score_in_range": check_score_in_range(result),
        "skills_grounded": check_skills_grounded(result, cv_text),
        "verdict_matches_score": check_verdict_matches_score(result),
    }

    all_passed = all(passed for passed, _ in checks.values())

    return {
        "all_passed": all_passed,
        "checks": {name: {"passed": passed, "detail": detail} for name, (passed, detail) in checks.items()},
    }