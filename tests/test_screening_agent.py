import json
import pytest
from app.agents.screening_agent import _normalize_verdict, _filter_hallucinated_skills, _extract_json


# _normalize_verdict 

def test_normalize_verdict_none_score_returns_error():
    assert _normalize_verdict(None) == "Error"


def test_normalize_verdict_high_score_is_suitable():
    assert _normalize_verdict(85) == "Suitable"


def test_normalize_verdict_boundary_70_is_suitable():
    assert _normalize_verdict(70) == "Suitable"


def test_normalize_verdict_just_below_70_is_borderline():
    assert _normalize_verdict(69) == "Borderline"


def test_normalize_verdict_boundary_40_is_borderline():
    assert _normalize_verdict(40) == "Borderline"


def test_normalize_verdict_just_below_40_is_not_suitable():
    assert _normalize_verdict(39) == "Not suitable"


def test_normalize_verdict_zero_is_not_suitable():
    assert _normalize_verdict(0) == "Not suitable"


def test_normalize_verdict_max_score_is_suitable():
    assert _normalize_verdict(100) == "Suitable"


#  _filter_hallucinated_skills 

def test_filter_keeps_skill_present_in_cv():
    cv_text = "Experienced with Python and Docker."
    skills = ["Python"]
    assert _filter_hallucinated_skills(skills, cv_text) == ["Python"]


def test_filter_removes_skill_not_in_cv():
    cv_text = "Experienced with Python and Docker."
    skills = ["Kubernetes"]
    assert _filter_hallucinated_skills(skills, cv_text) == []


def test_filter_is_case_insensitive():
    cv_text = "Strong background in PYTHON development."
    skills = ["python"]
    assert _filter_hallucinated_skills(skills, cv_text) == ["python"]


def test_filter_mixed_real_and_hallucinated_skills():
    cv_text = "Skills: Python, Docker, Git."
    skills = ["Python", "Kubernetes", "Docker", "AWS"]
    assert _filter_hallucinated_skills(skills, cv_text) == ["Python", "Docker"]


def test_filter_empty_skills_list_returns_empty():
    cv_text = "Skills: Python, Docker."
    assert _filter_hallucinated_skills([], cv_text) == []


def test_filter_empty_cv_text_removes_all_skills():
    assert _filter_hallucinated_skills(["Python", "Docker"], "") == []


#  _extract_json 

def test_extract_json_plain_valid_json():
    raw = '{"score": 85, "verdict": "Suitable"}'
    assert _extract_json(raw) == {"score": 85, "verdict": "Suitable"}


def test_extract_json_wrapped_in_markdown_fences():
    raw = '```json\n{"score": 42, "verdict": "Borderline"}\n```'
    assert _extract_json(raw) == {"score": 42, "verdict": "Borderline"}


def test_extract_json_wrapped_in_plain_fences_no_json_tag():
    raw = '```\n{"score": 10}\n```'
    assert _extract_json(raw) == {"score": 10}


def test_extract_json_with_stray_text_before_and_after():
    raw = 'Sure, here is the result:\n{"score": 55}\nLet me know if you need anything else.'
    assert _extract_json(raw) == {"score": 55}


def test_extract_json_none_input_raises_json_decode_error():
    with pytest.raises(json.JSONDecodeError):
        _extract_json(None)


def test_extract_json_no_object_found_raises_json_decode_error():
    with pytest.raises(json.JSONDecodeError):
        _extract_json("This response contains no JSON object at all.")


def test_extract_json_empty_string_raises_json_decode_error():
    with pytest.raises(json.JSONDecodeError):
        _extract_json("")