"""Validate model output before rendering, storing or converting it to a document."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Short = Annotated[str, Field(min_length=1, max_length=500)]
Long = Annotated[str, Field(min_length=1, max_length=2000)]
Score = Annotated[int, Field(ge=0, le=100, strict=True)]


class Structured(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SubScores(Structured):
    ats: Score
    impact: Score
    clarity: Score
    formatting: Score


class Issue(Structured):
    issue: Short
    fix: Short


class Bullet(Structured):
    original: Short
    improved: Short


class Analysis(Structured):
    score: Score
    subscores: SubScores
    strengths: Annotated[list[Short], Field(max_length=8)]
    issues: Annotated[list[Issue], Field(max_length=8)]
    rewritten_bullets: Annotated[list[Bullet], Field(max_length=8)]
    missing_sections: Annotated[list[Short], Field(max_length=8)]
    suggested_roles: Annotated[list[Short], Field(max_length=6)]
    language: Annotated[str, Field(min_length=2, max_length=32)]

    def summary(self) -> dict:
        # Detailed CV excerpts and original/rewritten bullets remain in the short-lived memory session.
        return self.model_dump(exclude={"rewritten_bullets"})


class JobMatch(Structured):
    score: Score
    missing_keywords: Annotated[list[Short], Field(max_length=15)]
    tailored_bullets: Annotated[list[Short], Field(max_length=8)]


class LinkedIn(Structured):
    headline: Short
    summary: Long


class InterviewQuestions(Structured):
    questions: Annotated[list[Short], Field(min_length=5, max_length=5)]


class AnswerFeedback(Structured):
    score: Score
    feedback: Long


class CVSection(Structured):
    title: Short
    bullets: Annotated[list[Short], Field(max_length=20)]


class ImprovedCV(Structured):
    name: Short
    headline: Short
    contact: Annotated[str, Field(max_length=500)]
    summary: Long
    sections: Annotated[list[CVSection], Field(min_length=1, max_length=12)]
