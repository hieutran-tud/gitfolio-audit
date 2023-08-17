"""Deterministic, explainable rules for auditing GitHub portfolios."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from .models import (
    AuditCheck,
    ProfileAudit,
    ProfileSnapshot,
    RepositoryAudit,
    RepositorySnapshot,
)

DEPENDENCY_FILES = {
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "environment.yml",
    "environment.yaml",
    "package.json",
    "go.mod",
    "cargo.toml",
    "pom.xml",
    "gemfile",
}


def audit_profile(
    profile: ProfileSnapshot,
    repositories: list[RepositorySnapshot],
    *,
    profile_readme_exists: bool = False,
    as_of: datetime | None = None,
) -> ProfileAudit:
    """Audit profile positioning and public proof of work.

    ``as_of`` is injectable so reports and tests can be reproduced.
    """

    as_of = as_of or datetime.now(timezone.utc)
    checks = [
        _profile_readme_check(profile_readme_exists),
        _identity_check(profile),
        _bio_check(profile),
        _website_check(profile),
        _public_work_check(profile, repositories),
        _recent_activity_check(repositories, as_of),
    ]
    return ProfileAudit(
        profile=profile,
        checks=checks,
        repositories=[],
        generated_at=as_of.isoformat(),
    )


def audit_repository(
    repository: RepositorySnapshot,
    root_entries: Iterable[dict[str, Any] | str],
    *,
    as_of: datetime | None = None,
    stale_after_days: int = 180,
) -> RepositoryAudit:
    """Audit the visible engineering signals in a repository root."""

    as_of = as_of or datetime.now(timezone.utc)
    names = _normalise_entries(root_entries)
    checks = [
        _description_check(repository),
        _readme_check(names),
        _license_check(repository),
        _topics_check(repository),
        _dependency_check(names),
        _tests_check(names),
        _ci_check(names),
        _originality_check(repository),
        _repository_activity_check(repository, as_of, stale_after_days),
    ]
    return RepositoryAudit(repository=repository, checks=checks)


def _profile_readme_check(exists: bool) -> AuditCheck:
    if exists:
        return AuditCheck(
            "profile_readme",
            "Profile README",
            "pass",
            25,
            25,
            "A profile README is visible to visitors.",
        )
    return AuditCheck(
        "profile_readme",
        "Profile README",
        "fail",
        0,
        25,
        "No profile README was detected.",
        "Create a public repository named exactly like your GitHub username and add a focused README.",
    )


def _identity_check(profile: ProfileSnapshot) -> AuditCheck:
    if profile.name.strip():
        return AuditCheck(
            "identity",
            "Display name",
            "pass",
            10,
            10,
            f"The profile identifies you as {profile.name.strip()}.",
        )
    return AuditCheck(
        "identity",
        "Display name",
        "fail",
        0,
        10,
        "No display name is visible.",
        "Use the name or professional identity people will recognize.",
    )


def _bio_check(profile: ProfileSnapshot) -> AuditCheck:
    length = len(profile.bio.strip())
    if length >= 50:
        return AuditCheck(
            "bio",
            "Professional positioning",
            "pass",
            20,
            20,
            "The bio gives visitors enough context about your focus.",
        )
    if length:
        return AuditCheck(
            "bio",
            "Professional positioning",
            "warn",
            10,
            20,
            "A bio exists, but it is too brief to communicate a clear direction.",
            "State your role or target role, strongest areas, and the kind of work you build.",
        )
    return AuditCheck(
        "bio",
        "Professional positioning",
        "fail",
        0,
        20,
        "No bio is visible.",
        "Add a one-sentence professional positioning statement.",
    )


def _website_check(profile: ProfileSnapshot) -> AuditCheck:
    if profile.blog.strip():
        return AuditCheck(
            "website",
            "External link",
            "pass",
            10,
            10,
            "A website or external profile is linked.",
        )
    return AuditCheck(
        "website",
        "External link",
        "warn",
        0,
        10,
        "No website or professional profile link is visible.",
        "Add LinkedIn, a portfolio, resume, or personal site if you have one.",
    )


def _public_work_check(
    profile: ProfileSnapshot,
    repositories: list[RepositorySnapshot],
) -> AuditCheck:
    count = max(profile.public_repos, len(repositories))
    if count >= 3:
        return AuditCheck(
            "public_work",
            "Public body of work",
            "pass",
            20,
            20,
            f"The account exposes {count} public repositories.",
        )
    if count:
        return AuditCheck(
            "public_work",
            "Public body of work",
            "warn",
            10,
            20,
            f"The account exposes only {count} public repository.",
            "Publish two or three original, finished projects that demonstrate your target skills.",
        )
    return AuditCheck(
        "public_work",
        "Public body of work",
        "fail",
        0,
        20,
        "No public repositories were found.",
        "Publish at least one complete project with documentation and a clear outcome.",
    )


def _recent_activity_check(
    repositories: list[RepositorySnapshot],
    as_of: datetime,
) -> AuditCheck:
    dates = [_parse_timestamp(repository.pushed_at) for repository in repositories]
    dates = [date for date in dates if date is not None]
    if not dates:
        return AuditCheck(
            "recent_activity",
            "Recent activity",
            "warn",
            0,
            15,
            "No repository activity date was available.",
            "Keep at least one public project maintained and visibly active.",
        )
    newest = max(dates)
    age = _age_in_days(newest, as_of)
    if age <= 180:
        return AuditCheck(
            "recent_activity",
            "Recent activity",
            "pass",
            15,
            15,
            f"The newest visible repository activity is {age} days old.",
        )
    if age <= 365:
        return AuditCheck(
            "recent_activity",
            "Recent activity",
            "warn",
            8,
            15,
            f"The newest visible repository activity is {age} days old.",
            "Add a substantive update to a public project when you have meaningful progress.",
        )
    return AuditCheck(
        "recent_activity",
        "Recent activity",
        "warn",
        3,
        15,
        f"The newest visible repository activity is {age} days old.",
        "Refresh or replace stale showcase projects so the profile reflects current skills.",
    )


def _description_check(repository: RepositorySnapshot) -> AuditCheck:
    length = len(repository.description.strip())
    if length >= 40:
        return AuditCheck(
            "description",
            "Repository description",
            "pass",
            10,
            10,
            "The description explains the repository's purpose.",
        )
    if length:
        return AuditCheck(
            "description",
            "Repository description",
            "warn",
            5,
            10,
            "A description exists, but it is too vague or short.",
            "Describe the problem, audience, and primary technology in one sentence.",
        )
    return AuditCheck(
        "description",
        "Repository description",
        "fail",
        0,
        10,
        "No repository description is visible.",
        "Add a one-sentence description that explains the project's value.",
    )


def _readme_check(names: set[str]) -> AuditCheck:
    if "readme.md" in names:
        return AuditCheck(
            "readme",
            "Project README",
            "pass",
            15,
            15,
            "A README is present at the repository root.",
        )
    return AuditCheck(
        "readme",
        "Project README",
        "fail",
        0,
        15,
        "No root README was detected.",
        "Document the problem, setup, usage, results, and limitations in README.md.",
    )


def _license_check(repository: RepositorySnapshot) -> AuditCheck:
    if repository.license_name.strip():
        return AuditCheck(
            "license",
            "License",
            "pass",
            10,
            10,
            f"The repository declares a {repository.license_name} license.",
        )
    return AuditCheck(
        "license",
        "License",
        "warn",
        0,
        10,
        "No license was detected.",
        "Add a license for code you own; preserve upstream licensing for forked code.",
    )


def _topics_check(repository: RepositorySnapshot) -> AuditCheck:
    count = len(repository.topics)
    if count >= 2:
        return AuditCheck(
            "topics",
            "Repository topics",
            "pass",
            5,
            5,
            f"The repository has {count} descriptive topics.",
        )
    if count == 1:
        return AuditCheck(
            "topics",
            "Repository topics",
            "warn",
            3,
            5,
            "The repository has only one topic.",
            "Add a few accurate topics such as python, machine-learning, or data-engineering.",
        )
    return AuditCheck(
        "topics",
        "Repository topics",
        "warn",
        0,
        5,
        "No repository topics were detected.",
        "Add a small set of accurate topics to improve discovery.",
    )


def _dependency_check(names: set[str]) -> AuditCheck:
    dependencies = sorted(DEPENDENCY_FILES.intersection(names))
    if dependencies:
        return AuditCheck(
            "dependencies",
            "Reproducible setup",
            "pass",
            10,
            10,
            f"Dependency metadata found: {', '.join(dependencies)}.",
        )
    return AuditCheck(
        "dependencies",
        "Reproducible setup",
        "fail",
        0,
        10,
        "No common dependency or environment file was detected.",
        "Add a dependency manifest and explain how to create the development environment.",
    )


def _tests_check(names: set[str]) -> AuditCheck:
    has_tests = any(
        name in {"tests", "test", "__tests__"}
        or name.startswith("test_")
        or name.endswith("_test.py")
        for name in names
    )
    if has_tests:
        return AuditCheck(
            "tests",
            "Automated tests",
            "pass",
            10,
            10,
            "A test directory or test file is visible.",
        )
    return AuditCheck(
        "tests",
        "Automated tests",
        "warn",
        0,
        10,
        "No obvious test suite was detected.",
        "Add focused tests for core behavior, especially before publishing a library or service.",
    )


def _ci_check(names: set[str]) -> AuditCheck:
    has_ci = ".github" in names or ".github/workflows" in names
    if has_ci:
        return AuditCheck(
            "ci",
            "Continuous integration",
            "pass",
            10,
            10,
            "A GitHub configuration directory is visible.",
        )
    return AuditCheck(
        "ci",
        "Continuous integration",
        "warn",
        0,
        10,
        "No GitHub configuration directory was detected.",
        "Add a small workflow that runs tests and basic quality checks on every pull request.",
    )


def _originality_check(repository: RepositorySnapshot) -> AuditCheck:
    if not repository.fork:
        return AuditCheck(
            "originality",
            "Project ownership",
            "pass",
            10,
            10,
            "The repository is not marked as a fork.",
        )
    return AuditCheck(
        "originality",
        "Project ownership",
        "warn",
        2,
        10,
        "The repository is marked as a fork, so visitors may attribute most history upstream.",
        "Label the repository as a learning fork or feature an original project alongside it.",
    )


def _repository_activity_check(
    repository: RepositorySnapshot,
    as_of: datetime,
    stale_after_days: int,
) -> AuditCheck:
    if repository.archived:
        return AuditCheck(
            "activity",
            "Repository maintenance",
            "warn",
            2,
            10,
            "The repository is archived.",
            "Unarchive it if it is still a showcase project, or explain its historical status.",
        )
    pushed_at = _parse_timestamp(repository.pushed_at)
    if pushed_at is None:
        return AuditCheck(
            "activity",
            "Repository maintenance",
            "warn",
            2,
            10,
            "No recent activity date was available.",
            "Keep the repository metadata and documentation current.",
        )
    age = _age_in_days(pushed_at, as_of)
    if age <= stale_after_days:
        return AuditCheck(
            "activity",
            "Repository maintenance",
            "pass",
            10,
            10,
            f"The latest push was {age} days ago.",
        )
    return AuditCheck(
        "activity",
        "Repository maintenance",
        "warn",
        4,
        10,
        f"The latest push was {age} days ago.",
        "Refresh the project or mark it clearly as archived learning material.",
    )


def _normalise_entries(entries: Iterable[dict[str, Any] | str]) -> set[str]:
    names: set[str] = set()
    for entry in entries:
        if isinstance(entry, str):
            value = entry
        else:
            value = str(entry.get("path") or entry.get("name") or "")
        if value:
            names.add(value.strip("/").lower())
    return names


def _parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_in_days(timestamp: datetime, as_of: datetime) -> int:
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    delta = max(as_of.astimezone(timezone.utc) - timestamp, timedelta(0))
    return delta.days
