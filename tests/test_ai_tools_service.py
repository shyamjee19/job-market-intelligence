import pytest

from ai.providers.base import ChatMessage, ChatProvider, ChatResult
from ai.services import ai_tools_service
from database.connection import get_connection
from database.repository import upsert_jobs


class FakeChatProvider(ChatProvider):
    name = "fake"

    def __init__(self):
        self.received_messages: list[list[ChatMessage]] = []

    def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> ChatResult:
        self.received_messages.append(messages)
        return ChatResult(text="fake AI summary", prompt_tokens=10, completion_tokens=5)


@pytest.fixture
def seeded_jobs(use_test_db):
    """A couple of Data Engineer postings with overlapping/differing
    skill tags, so skill-gap/salary/recommendation logic has real
    signal to compute over."""
    upsert_jobs(
        "remoteok",
        [
            {
                "external_id": "ai-tools-job-1",
                "company": "Acme Data",
                "position": "Data Engineer",
                "location": "Remote",
                "remote_type": "remote",
                "salary_min": 100000,
                "salary_max": 140000,
                "date_posted": None,
                "tags": ["python", "sql", "airflow"],
                "job_url": "https://example.com/1",
                "apply_url": "https://example.com/apply/1",
                "description": "Build pipelines.",
            },
            {
                "external_id": "ai-tools-job-2",
                "company": "Beta Data",
                "position": "Data Engineer",
                "location": "Remote",
                "remote_type": "remote",
                "salary_min": 110000,
                "salary_max": 150000,
                "date_posted": None,
                "tags": ["python", "spark", "airflow"],
                "job_url": "https://example.com/2",
                "apply_url": "https://example.com/apply/2",
                "description": "Scale data infra.",
            },
        ],
        dbname=use_test_db,
    )
    with get_connection(dbname=use_test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT job_key FROM fact_jobs WHERE external_id IN ('ai-tools-job-1', 'ai-tools-job-2')")
            return [row[0] for row in cursor.fetchall()]


def test_analyze_resume_returns_summary_and_top_skills(use_test_db, seeded_jobs):
    chat = FakeChatProvider()
    result = ai_tools_service.analyze_resume("Experienced engineer with Python and SQL.", chat_provider=chat)

    assert result["summary"] == "fake AI summary"
    assert "python" in result["data"]["top_market_skills"]
    assert len(chat.received_messages) == 1


def test_skill_gap_separates_matched_and_missing_skills(use_test_db, seeded_jobs):
    chat = FakeChatProvider()
    result = ai_tools_service.skill_gap("python, sql", "Data Engineer", chat_provider=chat)

    have_skills = {row["skill"] for row in result["data"]["have"]}
    missing_skills = {row["skill"] for row in result["data"]["missing"]}

    assert "python" in have_skills
    assert "airflow" in missing_skills
    assert "sql" not in missing_skills
    assert result["data"]["sample_size"] == 2


def test_skill_gap_with_no_matching_jobs_reports_empty(use_test_db):
    chat = FakeChatProvider()
    result = ai_tools_service.skill_gap("python", "Nonexistent Role Xyz", chat_provider=chat)

    assert result["data"]["have"] == []
    assert result["data"]["missing"] == []
    assert result["data"]["sample_size"] == 0


def test_salary_insights_computes_real_averages(use_test_db, seeded_jobs):
    chat = FakeChatProvider()
    result = ai_tools_service.salary_insights("Data Engineer", None, chat_provider=chat)

    assert result["data"]["sample_size"] == 2
    assert result["data"]["avg_salary_min"] == 105000
    assert result["data"]["avg_salary_max"] == 145000
    assert result["data"]["highest_salary"] == 150000


def test_job_recommendations_ranks_by_skill_overlap(use_test_db, seeded_jobs):
    chat = FakeChatProvider()
    result = ai_tools_service.job_recommendations(["python", "spark"], chat_provider=chat)

    companies = [job["company"] for job in result["data"]["jobs"]]
    assert "Beta Data" in companies  # matches both python and spark
    assert companies[0] == "Beta Data"  # ranked first for the higher overlap


def test_job_recommendations_with_no_profile_skills_skips_llm_call(use_test_db):
    chat = FakeChatProvider()
    result = ai_tools_service.job_recommendations([], chat_provider=chat)

    assert result["data"]["jobs"] == []
    assert len(chat.received_messages) == 0


def test_career_advice_grounds_in_sample_jobs(use_test_db, seeded_jobs):
    chat = FakeChatProvider()
    result = ai_tools_service.career_advice("python", "Data Engineer", chat_provider=chat)

    assert result["summary"] == "fake AI summary"
    assert len(result["data"]["sample_jobs"]) > 0


def test_interview_prep_without_company_has_no_grounding(use_test_db):
    chat = FakeChatProvider()
    result = ai_tools_service.interview_prep("Data Engineer", None, chat_provider=chat)

    assert result["data"]["grounded_in_real_postings"] is False


def test_interview_prep_with_matching_company_is_grounded(use_test_db, seeded_jobs):
    chat = FakeChatProvider()
    result = ai_tools_service.interview_prep("Data Engineer", "Acme Data", chat_provider=chat)

    assert result["data"]["grounded_in_real_postings"] is True
