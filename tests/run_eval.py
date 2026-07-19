import sys
sys.path.insert(0, '..')

from eval_dataset import load_eval_cases
from deterministic_checks import run_all_deterministic_checks
from app.agents.screening_agent import screen_candidate
from app.agents.judge_agent import judge_screening_result


def run_evaluation():
    cases = load_eval_cases()
    report_rows = []

    for case in cases:
        print(f"\n Running: {case['case_id']} ")

        result = screen_candidate(case["cv_text"], case["job_description"])
        det_checks = run_all_deterministic_checks(result, case["cv_text"])
        judgment = judge_screening_result(case["cv_text"], case["job_description"], result)

        score = result.get("score")
        expected_min, expected_max = case["expected_score_range"]
        score_in_expected_range = score is not None and expected_min <= score <= expected_max
        verdict_matches_expected = result.get("verdict") == case["expected_verdict"]

        row = {
            "case_id": case["case_id"],
            "score": score,
            "expected_range": case["expected_score_range"],
            "score_in_expected_range": score_in_expected_range,
            "verdict": result.get("verdict"),
            "expected_verdict": case["expected_verdict"],
            "verdict_matches_expected": verdict_matches_expected,
            "deterministic_all_passed": det_checks["all_passed"],
            "judge_justification_quality": judgment.get("justification_quality"),
            "judge_verdict_reasonable": judgment.get("verdict_reasonable"),
        }
        report_rows.append(row)

        print(f"Score: {score} (expected {case['expected_score_range']}) — {'OK' if score_in_expected_range else 'OUT OF RANGE'}")
        print(f"Verdict: {result.get('verdict')} (expected {case['expected_verdict']}) — {'MATCH' if verdict_matches_expected else 'MISMATCH'}")
        print(f"Deterministic checks: {'ALL PASSED' if det_checks['all_passed'] else det_checks['checks']}")
        print(f"Judge: quality={judgment.get('justification_quality')}, reasonable={judgment.get('verdict_reasonable')}")

    print("\n\n=== SUMMARY ===")
    total = len(report_rows)
    score_pass = sum(1 for r in report_rows if r["score_in_expected_range"])
    verdict_pass = sum(1 for r in report_rows if r["verdict_matches_expected"])
    det_pass = sum(1 for r in report_rows if r["deterministic_all_passed"])
    judge_reasonable = sum(1 for r in report_rows if r["judge_verdict_reasonable"])

    print(f"Total cases: {total}")
    print(f"Score within expected range: {score_pass}/{total}")
    print(f"Verdict matches expected: {verdict_pass}/{total}")
    print(f"All deterministic checks passed: {det_pass}/{total}")
    print(f"Judge rated verdict reasonable: {judge_reasonable}/{total}")

    return report_rows


if __name__ == "__main__":
    run_evaluation()