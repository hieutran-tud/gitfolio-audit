from datetime import datetime, timezone

from gitfolio_audit.audit import audit_profile, audit_repository
from gitfolio_audit.models import ProfileSnapshot, RepositorySnapshot


AS_OF = datetime(2026, 8, 28, tzinfo=timezone.utc)


def _repository(**overrides) -> RepositorySnapshot:
    values = {
        "full_name": "alex-dev/forecast-api",
        "name": "forecast-api",
        "description": "A reproducible forecasting API with evaluation and monitoring.",
        "html_url": "https://github.com/alex-dev/forecast-api",
        "default_branch": "main",
        "license_name": "MIT",
        "topics": ["python", "machine-learning"],
        "pushed_at": "2026-08-20T12:00:00Z",
    }
    values.update(overrides)
    return RepositorySnapshot(**values)


def _profile(**overrides) -> ProfileSnapshot:
    values = {
        "login": "alex-dev",
        "name": "Alex Developer",
        "bio": "Machine learning engineer building reliable data products and evaluation tools.",
        "blog": "https://alex.dev",
        "public_repos": 4,
    }
    values.update(overrides)
    return ProfileSnapshot(**values)


def test_complete_repository_gets_full_score():
    entries = ["README.md", "LICENSE", "pyproject.toml", "tests", ".github"]

    result = audit_repository(_repository(), entries, as_of=AS_OF)

    assert result.score == 100.0
    assert all(check.status == "pass" for check in result.checks)


def test_fork_with_missing_engineering_signals_is_actionable():
    result = audit_repository(
        _repository(
            description="ML notes",
            license_name="",
            topics=[],
            fork=True,
            pushed_at="2023-01-01T00:00:00Z",
        ),
        [],
        as_of=AS_OF,
    )

    checks = {check.check_id: check for check in result.checks}
    assert checks["originality"].status == "warn"
    assert checks["readme"].status == "fail"
    assert checks["dependencies"].status == "fail"
    assert "learning fork" in " ".join(result.recommendations)
    assert result.score < 50


def test_empty_profile_is_scored_without_network_data():
    result = audit_profile(_profile(name="", bio="", blog="", public_repos=0), [], as_of=AS_OF)

    assert result.score == 0.0
    assert {check.check_id for check in result.checks} == {
        "profile_readme",
        "identity",
        "bio",
        "website",
        "public_work",
        "recent_activity",
    }
    assert result.recommendations


def test_profile_activity_uses_injected_as_of_date():
    result = audit_profile(_profile(public_repos=1), [_repository()], as_of=AS_OF)

    activity = next(check for check in result.checks if check.check_id == "recent_activity")
    assert activity.status == "pass"
    assert "7 days" in activity.detail
