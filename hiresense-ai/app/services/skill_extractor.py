"""
Skill extraction and gap analysis.

Uses phrase-boundary matching (not naive substring search) against the
curated skills taxonomy so that, e.g., "java" does not spuriously match
inside "javascript". Multi-word skills ("machine learning") are matched
as whole phrases.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.skills_taxonomy import ALL_SKILLS

# Sort longest-first so multi-word phrases are matched before their
# shorter substrings get a chance to (e.g. "machine learning" before "machine").
_SORTED_SKILLS = sorted(ALL_SKILLS, key=len, reverse=True)

_SKILL_PATTERNS = {
    skill: re.compile(r"(?<![\w-])" + re.escape(skill) + r"(?![\w-])", re.IGNORECASE)
    for skill in _SORTED_SKILLS
}


@dataclass
class SkillGapResult:
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    job_skills_found: list[str] = field(default_factory=list)
    resume_skills_found: list[str] = field(default_factory=list)
    coverage_pct: float = 0.0


def extract_skills(text: str) -> list[str]:
    """Return the sorted list of taxonomy skills found in `text`."""
    if not text:
        return []
    found = [skill for skill, pattern in _SKILL_PATTERNS.items() if pattern.search(text)]
    return sorted(found)


def analyze_skill_gap(resume_text: str, job_text: str) -> SkillGapResult:
    """
    Compare skills mentioned in a resume against those required by a
    job description and report what's covered vs missing.
    """
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_text))

    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    coverage_pct = (len(matched) / len(job_skills) * 100) if job_skills else 100.0

    return SkillGapResult(
        matched_skills=matched,
        missing_skills=missing,
        job_skills_found=sorted(job_skills),
        resume_skills_found=sorted(resume_skills),
        coverage_pct=round(coverage_pct, 1),
    )


def recommend_keywords(job_text: str, resume_text: str, top_n: int = 10) -> list[str]:
    """
    Recommend keywords from the job description that the resume should
    incorporate, prioritizing skills missing from the resume.
    """
    gap = analyze_skill_gap(resume_text, job_text)
    recommendations = list(gap.missing_skills)

    # If there aren't enough missing skills to fill top_n, pad with
    # high-signal job keywords (capitalized acronyms, frequent nouns)
    # that aren't already in our taxonomy match.
    if len(recommendations) < top_n:
        extra = _extract_frequent_terms(job_text, exclude=set(gap.resume_skills_found))
        for term in extra:
            if term not in recommendations:
                recommendations.append(term)
            if len(recommendations) >= top_n:
                break

    return recommendations[:top_n]


_STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "have", "will",
    "you", "your", "our", "are", "able", "must", "all", "can", "etc",
    "job", "role", "work", "team", "years", "experience", "strong",
    "knowledge", "skills", "ability", "including", "such", "using",
}


def _extract_frequent_terms(text: str, exclude: set[str], min_len: int = 4) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z+/\.\-]{2,}", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        if w in _STOPWORDS or w in exclude or len(w) < min_len:
            continue
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked]
