"""Unit tests for app.services.matching_engine."""
from app.services.matching_engine import MatchingEngine, classify_fit


def test_classify_fit_thresholds():
    assert classify_fit(90) == "Excellent Fit"
    assert classify_fit(85) == "Excellent Fit"
    assert classify_fit(75) == "Strong Fit"
    assert classify_fit(60) == "Moderate Fit"
    assert classify_fit(45) == "Weak Fit"
    assert classify_fit(10) == "Poor Fit"


def test_score_returns_full_match_result(matching_engine: MatchingEngine, sample_resume_text, sample_job_text):
    result = matching_engine.score(sample_resume_text, sample_job_text)

    assert 0 <= result.match_score <= 100
    assert 0 <= result.semantic_similarity <= 100
    assert 0 <= result.skill_coverage_pct <= 100
    assert result.job_fit_category in {
        "Excellent Fit", "Strong Fit", "Moderate Fit", "Weak Fit", "Poor Fit"
    }
    assert isinstance(result.matched_skills, list)
    assert isinstance(result.missing_skills, list)


def test_well_matched_resume_scores_higher_than_unrelated(matching_engine: MatchingEngine, sample_job_text):
    good_resume = (
        "Backend engineer with 5 years building REST APIs in Python and Flask, "
        "PostgreSQL data modeling, Docker containerization, and Kubernetes deployment. "
        "Strong collaborator with machine learning teams."
    )
    unrelated_resume = (
        "Pastry chef with 5 years of experience in high-volume bakeries, "
        "specializing in laminated dough, cake decoration, and inventory management."
    )

    good_result = matching_engine.score(good_resume, sample_job_text)
    bad_result = matching_engine.score(unrelated_resume, sample_job_text)

    assert good_result.match_score > bad_result.match_score


def test_match_result_to_dict_has_expected_keys(matching_engine: MatchingEngine, sample_resume_text, sample_job_text):
    result = matching_engine.score(sample_resume_text, sample_job_text)
    payload = result.to_dict()
    expected_keys = {
        "match_score", "semantic_similarity", "skill_coverage_pct",
        "job_fit_category", "matched_skills", "missing_skills", "recommended_keywords",
    }
    assert expected_keys.issubset(payload.keys())
