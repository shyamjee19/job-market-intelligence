"""Backend for the AI tools pages (resume review, career advice, skill
gap, salary insights, job recommendations, interview prep).

Each is a thin layer over the same chat provider used by the RAG
chatbot, but with a specialized prompt - and wherever real numbers are
available (skill demand counts, salary stats, matching postings), those
come straight from Postgres rather than being left to the LLM to guess,
so the LLM's job is narration, not data invention.

Skill matching here (skill_gap, job_recommendations) is a simple
case-insensitive string match against dim_skill tag names, the same
"intentionally approximate, documented" pattern as utils/skill_categories.py
- it won't catch synonyms ("JS" vs "JavaScript"), just exact-ish tags.
"""
from ai.prompts import ai_tools as prompts
from ai.providers.base import ChatProvider
from ai.providers.registry import get_chat_provider
from database import queries as job_queries

_SAMPLE_SIZE = 50
_RECOMMENDATION_LIMIT = 10


def _job_brief(job: dict) -> dict:
    return {"id": job["id"], "position": job["position"], "company": job["company"], "location": job["location"]}


def analyze_resume(resume_text: str, chat_provider: ChatProvider | None = None) -> dict:
    top_skills = [r["tag"] for r in job_queries.top_tags(limit=15)]
    messages = prompts.resume_analysis_messages(resume_text, top_skills)
    chat = chat_provider or get_chat_provider()
    result = chat.generate(messages, temperature=0.3)
    return {"summary": result.text, "data": {"top_market_skills": top_skills}}


def career_advice(current_skills: str, goal: str, chat_provider: ChatProvider | None = None) -> dict:
    sample_jobs, _ = job_queries.list_jobs(search=goal, page=1, page_size=5)
    messages = prompts.career_advice_messages(current_skills, goal, sample_jobs)
    chat = chat_provider or get_chat_provider()
    result = chat.generate(messages, temperature=0.4)
    return {"summary": result.text, "data": {"sample_jobs": [_job_brief(j) for j in sample_jobs]}}


def skill_gap(current_skills: str, target_role: str, chat_provider: ChatProvider | None = None) -> dict:
    have = {s.strip().lower() for s in current_skills.split(",") if s.strip()}
    # page_size caps how many postings feed the demand tally below - the
    # reported sample_size is that analyzed count, not the (possibly much
    # larger) total match count, so it never overstates its own coverage.
    matching_jobs, _ = job_queries.list_jobs(search=target_role, page=1, page_size=_SAMPLE_SIZE)

    demand: dict[str, int] = {}
    for job in matching_jobs:
        for tag in job["tags"]:
            demand[tag] = demand.get(tag, 0) + 1
    ranked = sorted(demand.items(), key=lambda kv: -kv[1])[:15]

    matched = [(tag, count) for tag, count in ranked if tag.lower() in have]
    missing = [(tag, count) for tag, count in ranked if tag.lower() not in have]

    messages = prompts.skill_gap_messages(target_role, matched, missing)
    chat = chat_provider or get_chat_provider()
    result = chat.generate(messages, temperature=0.3)
    return {
        "summary": result.text,
        "data": {
            "have": [{"skill": t, "demand_count": c} for t, c in matched],
            "missing": [{"skill": t, "demand_count": c} for t, c in missing],
            "sample_size": len(matching_jobs),
        },
    }


def salary_insights(role: str | None, location: str | None, chat_provider: ChatProvider | None = None) -> dict:
    jobs, total = job_queries.list_jobs(search=role, location=location, page=1, page_size=100)
    salaries_min = [j["salary_min"] for j in jobs if j["salary_min"]]
    salaries_max = [j["salary_max"] for j in jobs if j["salary_max"]]
    stats = {
        "sample_size": total,
        "avg_salary_min": round(sum(salaries_min) / len(salaries_min)) if salaries_min else None,
        "avg_salary_max": round(sum(salaries_max) / len(salaries_max)) if salaries_max else None,
        "highest_salary": max(salaries_max) if salaries_max else None,
    }
    messages = prompts.salary_insights_messages(role, location, stats)
    chat = chat_provider or get_chat_provider()
    result = chat.generate(messages, temperature=0.3)
    return {"summary": result.text, "data": stats}


def job_recommendations(profile_skills: list[str], chat_provider: ChatProvider | None = None) -> dict:
    if not profile_skills:
        return {
            "summary": "Add some skills to your profile to get personalized job recommendations.",
            "data": {"jobs": []},
        }

    scored: dict[int, int] = {}
    jobs_by_id: dict[int, dict] = {}
    for skill in profile_skills:
        matches, _ = job_queries.list_jobs(tag=skill, page=1, page_size=20)
        for job in matches:
            scored[job["id"]] = scored.get(job["id"], 0) + 1
            jobs_by_id[job["id"]] = job

    if not scored:
        return {
            "summary": "No current postings match your profile skills yet - check back as new jobs are collected.",
            "data": {"jobs": []},
        }

    ranked_ids = sorted(scored, key=lambda jid: -scored[jid])[:_RECOMMENDATION_LIMIT]
    top_jobs = [jobs_by_id[jid] for jid in ranked_ids]

    messages = prompts.job_recommendations_messages(profile_skills, top_jobs)
    chat = chat_provider or get_chat_provider()
    result = chat.generate(messages, temperature=0.3)
    return {"summary": result.text, "data": {"jobs": [_job_brief(j) for j in top_jobs]}}


def interview_prep(role: str, company: str | None, chat_provider: ChatProvider | None = None) -> dict:
    sample_jobs: list[dict] = []
    if company:
        sample_jobs, _ = job_queries.list_jobs(company=company, page=1, page_size=3)

    messages = prompts.interview_prep_messages(role, company, sample_jobs)
    chat = chat_provider or get_chat_provider()
    result = chat.generate(messages, temperature=0.4)
    return {"summary": result.text, "data": {"grounded_in_real_postings": bool(sample_jobs)}}
