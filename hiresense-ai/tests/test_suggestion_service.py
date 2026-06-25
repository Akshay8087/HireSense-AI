"""Unit tests for app.services.suggestion_service (fallback path, no Gemini key)."""
from app.services.skill_extractor import analyze_skill_gap
from app.services.suggestion_service import SuggestionService


def test_fallback_used_when_no_api_key(suggestion_service_fallback: SuggestionService):
    gap = analyze_skill_gap(
        resume_text="Python and Flask developer.",
        job_text="Need Python, Flask, Kubernetes, and Terraform skills.",
    )
    result = suggestion_service_fallback.generate(
        resume_text="Python and Flask developer.",
        job_text="Need Python, Flask, Kubernetes, and Terraform skills.",
        gap=gap,
        match_score=55.0,
    )
    assert result.source == "fallback"
    assert result.summary
    assert isinstance(result.improvement_suggestions, list)
    assert len(result.improvement_suggestions) > 0


def test_fallback_mentions_missing_skills(suggestion_service_fallback: SuggestionService):
    gap = analyze_skill_gap(
        resume_text="Java developer.",
        job_text="Need strong Kubernetes and Terraform experience.",
    )
    result = suggestion_service_fallback.generate(
        resume_text="Java developer.",
        job_text="Need strong Kubernetes and Terraform experience.",
        gap=gap,
        match_score=20.0,
    )
    joined = " ".join(result.improvement_suggestions).lower()
    assert "kubernetes" in joined or "terraform" in joined


def test_fallback_summary_reflects_score_band(suggestion_service_fallback: SuggestionService):
    gap = analyze_skill_gap("Python, Flask, Docker.", "Python, Flask, Docker.")
    result = suggestion_service_fallback.generate(
        resume_text="Python, Flask, Docker.",
        job_text="Python, Flask, Docker.",
        gap=gap,
        match_score=95.0,
    )
    assert "excellent" in result.summary.lower()
