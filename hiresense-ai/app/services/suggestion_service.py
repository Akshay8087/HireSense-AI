"""
Resume improvement suggestion service.

Uses the Gemini API to generate specific, actionable resume rewrite
suggestions grounded in the actual skill gap between a resume and a
job description. If no Gemini API key is configured (or the call
fails), the service degrades gracefully to a deterministic rule-based
suggestion generator so the product still works end-to-end without a
paid API key — a requirement for local development, CI, and demos.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.core.exceptions import SuggestionServiceError
from app.services.skill_extractor import SkillGapResult

SYSTEM_INSTRUCTION = """You are an expert resume coach and technical recruiter.
Given a candidate's resume text, a target job description, and a structured
skill-gap analysis, produce specific, actionable suggestions to improve the
resume's match for this exact job. Be concrete: reference real phrasing the
candidate could add, not generic advice like "tailor your resume."

Respond ONLY with valid JSON matching this schema, no other text:
{
  "summary": "<one or two sentence overview of the fit>",
  "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>", ...],
  "rewrite_example": "<one example of a rewritten bullet point that incorporates a missing skill/keyword naturally>"
}
"""


@dataclass
class SuggestionResult:
    summary: str
    improvement_suggestions: list[str] = field(default_factory=list)
    rewrite_example: str = ""
    source: str = "fallback"  # "gemini" or "fallback"

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "improvement_suggestions": self.improvement_suggestions,
            "rewrite_example": self.rewrite_example,
            "source": self.source,
        }


class SuggestionService:
    def __init__(self, api_key: str | None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._client_configured = False

    def _configure_client(self) -> None:
        if self._client_configured or not self.api_key:
            return
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        self._client_configured = True

    def generate(
        self,
        resume_text: str,
        job_text: str,
        gap: SkillGapResult,
        match_score: float,
    ) -> SuggestionResult:
        if self.api_key:
            try:
                return self._generate_with_gemini(resume_text, job_text, gap, match_score)
            except Exception:
                # Any Gemini failure (quota, network, malformed response)
                # should never break the user-facing match request —
                # we degrade to the deterministic fallback instead.
                pass

        return self._generate_fallback(gap, match_score)

    # ------------------------------------------------------------------
    # Gemini-backed generation
    # ------------------------------------------------------------------
    def _generate_with_gemini(
        self,
        resume_text: str,
        job_text: str,
        gap: SkillGapResult,
        match_score: float,
    ) -> SuggestionResult:
        import google.generativeai as genai

        self._configure_client()
        model = genai.GenerativeModel(
            model_name=self.model_name, system_instruction=SYSTEM_INSTRUCTION
        )

        prompt = self._build_prompt(resume_text, job_text, gap, match_score)

        try:
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.4, "response_mime_type": "application/json"},
            )
            payload = json.loads(response.text)
        except Exception as exc:
            raise SuggestionServiceError(f"Gemini suggestion generation failed: {exc}") from exc

        return SuggestionResult(
            summary=payload.get("summary", ""),
            improvement_suggestions=payload.get("improvement_suggestions", []),
            rewrite_example=payload.get("rewrite_example", ""),
            source="gemini",
        )

    @staticmethod
    def _build_prompt(
        resume_text: str, job_text: str, gap: SkillGapResult, match_score: float
    ) -> str:
        # Truncate generously but bound the prompt size for latency/cost control.
        resume_excerpt = resume_text[:4000]
        job_excerpt = job_text[:3000]
        return (
            f"MATCH SCORE: {match_score}/100\n\n"
            f"MATCHED SKILLS: {', '.join(gap.matched_skills) or 'none detected'}\n"
            f"MISSING SKILLS: {', '.join(gap.missing_skills) or 'none'}\n\n"
            f"RESUME TEXT:\n{resume_excerpt}\n\n"
            f"JOB DESCRIPTION:\n{job_excerpt}\n"
        )

    # ------------------------------------------------------------------
    # Offline / rule-based fallback
    # ------------------------------------------------------------------
    @staticmethod
    def _generate_fallback(gap: SkillGapResult, match_score: float) -> SuggestionResult:
        if match_score >= 85:
            summary = "Excellent alignment with this role's requirements."
        elif match_score >= 70:
            summary = "Strong alignment, with a few targeted gaps worth closing."
        elif match_score >= 55:
            summary = "Moderate alignment — several relevant skills are missing or unstated."
        else:
            summary = "Significant gaps between this resume and the job's requirements."

        suggestions: list[str] = []

        if gap.missing_skills:
            top_missing = gap.missing_skills[:5]
            suggestions.append(
                "Add explicit mentions of these required skills if you have "
                f"experience with them: {', '.join(top_missing)}."
            )

        if gap.matched_skills:
            suggestions.append(
                "Move your strongest matched skills "
                f"({', '.join(gap.matched_skills[:3])}) higher in your resume "
                "(e.g., into the summary or first bullet of your most recent role) "
                "since recruiters and ATS systems weight early content more heavily."
            )

        suggestions.append(
            "Quantify achievements with numbers (%, $, time saved, team size) "
            "wherever possible — quantified bullets consistently score higher "
            "with both human reviewers and automated screening."
        )

        if gap.coverage_pct < 50:
            suggestions.append(
                "Consider whether this role is a strong match for your "
                "background; the skill overlap is currently low."
            )

        rewrite_example = ""
        if gap.missing_skills:
            skill = gap.missing_skills[0]
            rewrite_example = (
                f'Example: "Leveraged {skill} to streamline workflows, '
                f'collaborating cross-functionally to deliver measurable impact."'
            )

        return SuggestionResult(
            summary=summary,
            improvement_suggestions=suggestions,
            rewrite_example=rewrite_example,
            source="fallback",
        )
