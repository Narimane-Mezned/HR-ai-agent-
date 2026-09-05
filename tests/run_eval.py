import sys
import statistics
sys.path.insert(0, '..')

from eval_dataset import load_eval_cases
from deterministic_checks import run_all_deterministic_checks
from app.agents.screening_agent import screen_candidate
from app.agents.judge_agent import judge_screening_result


STABILITY_REPEATS = 3


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
            "routed_to_strong_model": result.get("routed_to_strong_model", False),
        }
        report_rows.append(row)

        print(f"Score: {score} (expected {case['expected_score_range']}) — {'OK' if score_in_expected_range else 'OUT OF RANGE'}")
        print(f"Verdict: {result.get('verdict')} (expected {case['expected_verdict']}) — {'MATCH' if verdict_matches_expected else 'MISMATCH'}")
        print(f"Deterministic checks: {'ALL PASSED' if det_checks['all_passed'] else det_checks['checks']}")
        print(f"Judge: quality={judgment.get('justification_quality')}, reasonable={judgment.get('verdict_reasonable')}")
        if row["routed_to_strong_model"]:
            print(f"Routing: score was ambiguous — re-screened with the stronger model")

    print("\n\n=== SUMMARY ===")
    total = len(report_rows)
    score_pass = sum(1 for r in report_rows if r["score_in_expected_range"])
    verdict_pass = sum(1 for r in report_rows if r["verdict_matches_expected"])
    det_pass = sum(1 for r in report_rows if r["deterministic_all_passed"])
    judge_reasonable = sum(1 for r in report_rows if r["judge_verdict_reasonable"])
    routed_count = sum(1 for r in report_rows if r["routed_to_strong_model"])

    print(f"Total cases: {total}")
    print(f"Score within expected range: {score_pass}/{total}")
    print(f"Verdict matches expected: {verdict_pass}/{total}")
    print(f"All deterministic checks passed: {det_pass}/{total}")
    print(f"Judge rated verdict reasonable: {judge_reasonable}/{total}")
    print(f"Cases routed to the stronger model (ambiguous score): {routed_count}/{total}")

    return report_rows


def run_stability_measurement(case_ids: list[str] = None):
    
    cases = load_eval_cases()
    if case_ids:
        cases = [c for c in cases if c["case_id"] in case_ids]

    stability_rows = []

    for case in cases:
        print(f"\n Stability check: {case['case_id']} ({STABILITY_REPEATS} repeats) ")
        scores = []

        for repeat_num in range(1, STABILITY_REPEATS + 1):
            result = screen_candidate(
                case["cv_text"], case["job_description"], bypass_cache=True
            )
            score = result.get("score")
            scores.append(score)
            print(f"  Repeat {repeat_num}: score={score}, verdict={result.get('verdict')}")

        valid_scores = [s for s in scores if s is not None]
        if len(valid_scores) >= 2:
            score_stdev = round(statistics.pstdev(valid_scores), 2)
            score_range = max(valid_scores) - min(valid_scores)
        else:
            score_stdev = None
            score_range = None

        stability_rows.append({
            "case_id": case["case_id"],
            "scores": scores,
            "stdev": score_stdev,
            "range": score_range,
        })

        print(f"Scores: {scores} — stdev={score_stdev}, range={score_range}")

    print("\n\n=== STABILITY SUMMARY ===")
    for row in stability_rows:
        flag = " <-- HIGH VARIANCE" if (row["range"] or 0) >= 20 else ""
        print(f"{row['case_id']}: scores={row['scores']} stdev={row['stdev']} range={row['range']}{flag}")

    return stability_rows


if __name__ == "__main__":
    run_evaluation()
    print("\n\n" + "=" * 60)
    print("Running stability measurement on known hard cases...")
    print("=" * 60)
    run_stability_measurement(case_ids=[
        "real_cv_indirect_reasoning_required",
        "synthetic_career_changer_indirect_reasoning",
        "synthetic_data_science_indirect_reasoning",
        "synthetic_devops_overqualified",
    ])