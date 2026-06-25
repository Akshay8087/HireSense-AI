"""
Resume-to-job matching engine.

Combines two signals into a final match score:
  1. Semantic similarity (cosine similarity of Sentence-Transformer /
     BERT embeddings) — captures overall contextual relevance even
     when exact keywords differ.
  2. Skill-keyword coverage — captures explicit, auditable overlap of
     hard skills, which recruiters and ATS systems often filter on.

The blended score is more robust than either signal alone: pure
embedding similarity can be fooled by topically-similar but
under-qualified resumes, while pure keyword matching misses synonyms
and paraphrased experience.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.services.embedding_service import EmbeddingService
from app.services.skill_extractor import SkillGapResult, analyze_skill_gap, recommend_keywords

# Weight given to semantic similarity vs. skill-keyword coverage in the
# final blended score. Tuned to favor semantic understanding while still
# rewarding explicit skill overlap that keyword-based ATS systems check.
SEMANTIC_WEIGHT = 0.6
SKILL_WEIGHT = 0.4

FIT_CATEGORY_THRESHOLDS = (
    (85, "Excellent Fit"),
    (70, "Strong Fit"),
    (55, "Moderate Fit"),
    (40, "Weak Fit"),
    (0, "Poor Fit"),
)


@dataclass
class MatchResult:
    match_score: float
    semantic_similarity: float
    skill_coverage_pct: float
    job_fit_category: str
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    recommended_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "match_score": self.match_score,
            "semantic_similarity": self.semantic_similarity,
            "skill_coverage_pct": self.skill_coverage_pct,
            "job_fit_category": self.job_fit_category,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "recommended_keywords": self.recommended_keywords,
        }


def classify_fit(score: float) -> str:
    for threshold, label in FIT_CATEGORY_THRESHOLDS:
        if score >= threshold:
            return label
    return "Poor Fit"


class MatchingEngine:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    def score(self, resume_text: str, job_text: str) -> MatchResult:
        resume_vec = self.embedding_service.embed(resume_text)
        job_vec = self.embedding_service.embed(job_text)

        semantic_sim = self.embedding_service.cosine_similarity(resume_vec, job_vec)
        # Cosine similarity for normalized BERT-family embeddings is
        # typically concentrated in [0.2, 0.9] for related text, so we
        # rescale to a 0-100 "percentage" that feels intuitive to users
        # rather than reporting raw cosine values (which would look
        # artificially low even for genuinely strong matches).
        semantic_pct = _rescale_similarity(semantic_sim)

        gap: SkillGapResult = analyze_skill_gap(resume_text, job_text)
        skill_pct = gap.coverage_pct

        blended = SEMANTIC_WEIGHT * semantic_pct + SKILL_WEIGHT * skill_pct
        blended = round(min(max(blended, 0.0), 100.0), 1)

        keywords = recommend_keywords(job_text, resume_text, top_n=10)

        return MatchResult(
            match_score=blended,
            semantic_similarity=round(semantic_pct, 1),
            skill_coverage_pct=skill_pct,
            job_fit_category=classify_fit(blended),
            matched_skills=gap.matched_skills,
            missing_skills=gap.missing_skills,
            recommended_keywords=keywords,
        )


def _rescale_similarity(cosine_sim: float, floor: float = 0.15, ceiling: float = 0.85) -> float:
    """
    Map raw cosine similarity (typically 0.15-0.85 for resume/job text
    pairs with this embedding model) onto an intuitive 0-100 scale.
    Values are clamped at the boundaries.
    """
    clamped = min(max(cosine_sim, floor), ceiling)
    return (clamped - floor) / (ceiling - floor) * 100
