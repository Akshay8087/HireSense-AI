"""Unit tests for app.services.skill_extractor."""
from app.services.skill_extractor import (
    analyze_skill_gap,
    extract_skills,
    recommend_keywords,
)


def test_extract_skills_finds_known_skills():
    text = "Experienced with Python, Flask, Docker, and machine learning pipelines."
    skills = extract_skills(text)
    assert "python" in skills
    assert "flask" in skills
    assert "docker" in skills
    assert "machine learning" in skills


def test_extract_skills_avoids_false_substring_matches():
    # "java" must not match inside "javascript"
    text = "Strong experience with JavaScript and TypeScript front-end development."
    skills = extract_skills(text)
    assert "java" not in skills
    assert "javascript" in skills
    assert "typescript" in skills


def test_extract_skills_is_case_insensitive():
    text = "PYTHON and Flask and DOCKER experience."
    skills = extract_skills(text)
    assert "python" in skills
    assert "docker" in skills


def test_extract_skills_empty_text_returns_empty_list():
    assert extract_skills("") == []
    assert extract_skills(None) == []


def test_analyze_skill_gap_identifies_matched_and_missing():
    resume = "Skilled in Python, Flask, SQL, and Git."
    job = "Looking for Python, Flask, Kubernetes, and Docker experience."

    gap = analyze_skill_gap(resume, job)

    assert "python" in gap.matched_skills
    assert "flask" in gap.matched_skills
    assert "kubernetes" in gap.missing_skills
    assert "docker" in gap.missing_skills
    assert "sql" not in gap.job_skills_found  # SQL isn't required by this job


def test_analyze_skill_gap_full_coverage_is_100_percent():
    resume = "Python, Flask, Docker expert."
    job = "We need Python and Flask skills."
    gap = analyze_skill_gap(resume, job)
    assert gap.coverage_pct == 100.0
    assert gap.missing_skills == []


def test_analyze_skill_gap_no_job_skills_is_100_percent_by_convention():
    resume = "Python developer."
    job = "We are a fast growing startup looking for a great team player."
    gap = analyze_skill_gap(resume, job)
    assert gap.coverage_pct == 100.0


def test_recommend_keywords_prioritizes_missing_skills():
    resume = "Python and Flask developer."
    job = "Need Python, Flask, Kubernetes, Terraform, and AWS experience."
    keywords = recommend_keywords(job, resume, top_n=5)
    assert "kubernetes" in keywords
    assert "terraform" in keywords
    assert "aws" in keywords
