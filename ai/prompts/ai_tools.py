"""Prompt construction for the AI tools pages (resume review, career
advice, skill gap, salary insights, job recommendations, interview prep).

Same convention as ai/prompts/rag_chatbot.py: plain functions, not a
templating engine. Where real numbers are available (skill demand
counts, salary stats, matching postings), those are computed in
ai/services/ai_tools_service.py from Postgres and handed to the LLM as
given facts - the LLM's job is narration and prioritization, not
inventing figures.
"""
from ai.providers.base import ChatMessage

_GROUNDING_RULE = (
    "Only reference figures, skills, or postings given to you below - never invent salary "
    "numbers, company names, or statistics. If the provided data is thin, say so plainly."
)


def _format_jobs(jobs: list[dict]) -> str:
    lines = [f"- {j.get('position')} at {j.get('company')} ({j.get('location') or 'location unknown'})" for j in jobs[:8]]
    return "\n".join(lines)


def resume_analysis_messages(resume_text: str, top_market_skills: list[str]) -> list[ChatMessage]:
    system = f"""You are a career coach reviewing a resume. {_GROUNDING_RULE}

Currently in-demand skills across job postings on this platform: {", ".join(top_market_skills) or "(none available)"}.

Structure your feedback as:
1. Strengths (2-3 bullets)
2. Gaps or weaknesses (2-3 bullets)
3. Skills from the in-demand list above that this resume doesn't mention
4. One concrete next step"""
    return [
        ChatMessage(role="system", content=system),
        ChatMessage(role="user", content=f"Here is the resume:\n\n{resume_text}"),
    ]


def career_advice_messages(current_skills: str, goal: str, sample_jobs: list[dict]) -> list[ChatMessage]:
    postings = _format_jobs(sample_jobs) or "(no matching postings found for this goal)"
    system = f"""You are a career advisor. {_GROUNDING_RULE}

Real postings currently matching the user's stated goal:
{postings}

Give a short roadmap: 3-5 concrete steps toward the goal, referencing the real postings above where relevant."""
    return [
        ChatMessage(role="system", content=system),
        ChatMessage(role="user", content=f"My current skills: {current_skills}\nMy goal: {goal}"),
    ]


def skill_gap_messages(target_role: str, matched: list[tuple[str, int]], missing: list[tuple[str, int]]) -> list[ChatMessage]:
    matched_str = ", ".join(f"{s} ({c} postings)" for s, c in matched) or "(none)"
    missing_str = ", ".join(f"{s} ({c} postings)" for s, c in missing) or "(none found - good coverage)"
    system = f"""You are a skills coach. The data below was computed directly from real job postings matching "{target_role}" - treat it as ground truth, don't recompute or contradict it, just explain and prioritize it.

Skills the user already has that are in demand: {matched_str}
Skills in demand that the user is missing: {missing_str}

Write 2-3 sentences prioritizing which missing skills to learn first and why."""
    return [ChatMessage(role="system", content=system), ChatMessage(role="user", content="Summarize my skill gap and what to prioritize.")]


def salary_insights_messages(role: str | None, location: str | None, stats: dict) -> list[ChatMessage]:
    system = f"""You are a compensation analyst. {_GROUNDING_RULE}

Computed statistics for role={role or "any"}, location={location or "any"}:
sample size: {stats["sample_size"]}, average minimum salary: {stats["avg_salary_min"]}, average maximum salary: {stats["avg_salary_max"]}, highest observed: {stats["highest_salary"]}.

Write 2-4 sentences interpreting these numbers for the user. Explicitly note if the sample size is small and the estimate is therefore uncertain."""
    return [ChatMessage(role="system", content=system), ChatMessage(role="user", content="Summarize the salary outlook.")]


def job_recommendations_messages(skills: list[str], jobs: list[dict]) -> list[ChatMessage]:
    postings = _format_jobs(jobs) or "(no matches found)"
    system = f"""You are a job-matching assistant. {_GROUNDING_RULE}

The user's profile skills: {", ".join(skills)}
Real postings ranked by skill overlap with the profile:
{postings}

Write a short (2-3 sentence) summary of why these postings fit, referencing specific ones by company and position."""
    return [ChatMessage(role="system", content=system), ChatMessage(role="user", content="Why do these fit my profile?")]


def interview_prep_messages(role: str, company: str | None, sample_jobs: list[dict]) -> list[ChatMessage]:
    context = _format_jobs(sample_jobs) if sample_jobs else "(no real postings found for this company - answer generically)"
    target = f'"{role}" role at {company}' if company else f'"{role}" role'
    system = f"""You are an interview coach preparing a candidate for a {target}.

Real postings for context:
{context}

Produce exactly:
1. Five likely interview questions
2. A one-line preparation tip for each"""
    return [ChatMessage(role="system", content=system), ChatMessage(role="user", content="Help me prepare.")]
