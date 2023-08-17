"""Typed data models used by the audit and rendering layers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

CheckStatus = Literal["pass", "warn", "fail", "info"]


@dataclass(frozen=True)
class AuditCheck:
    """One explainable quality check."""

    check_id: str
    label: str
    status: CheckStatus
    earned: int
    possible: int
    detail: str
    recommendation: str | None = None

    @property
    def percentage(self) -> float:
        """Return this check's percentage score."""

        if self.possible == 0:
            return 0.0
        return round((self.earned / self.possible) * 100, 1)


@dataclass(frozen=True)
class ProfileSnapshot:
    """Public fields returned by GitHub's user endpoint."""

    login: str
    name: str = ""
    bio: str = ""
    blog: str = ""
    location: str = ""
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    html_url: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfileSnapshot":
        return cls(
            login=str(data.get("login") or ""),
            name=str(data.get("name") or ""),
            bio=str(data.get("bio") or ""),
            blog=str(data.get("blog") or ""),
            location=str(data.get("location") or ""),
            public_repos=int(data.get("public_repos") or 0),
            followers=int(data.get("followers") or 0),
            following=int(data.get("following") or 0),
            html_url=str(data.get("html_url") or ""),
        )


@dataclass(frozen=True)
class RepositorySnapshot:
    """Repository metadata needed for a portfolio-oriented audit."""

    full_name: str
    name: str
    description: str = ""
    html_url: str = ""
    default_branch: str = "main"
    fork: bool = False
    archived: bool = False
    license_name: str = ""
    topics: list[str] = field(default_factory=list)
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    created_at: str = ""
    pushed_at: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepositorySnapshot":
        license_data = data.get("license")
        license_name = ""
        if isinstance(license_data, dict):
            license_name = str(license_data.get("spdx_id") or license_data.get("name") or "")
        elif license_data:
            license_name = str(license_data)

        topics = data.get("topics") or []
        return cls(
            full_name=str(data.get("full_name") or ""),
            name=str(data.get("name") or ""),
            description=str(data.get("description") or ""),
            html_url=str(data.get("html_url") or ""),
            default_branch=str(data.get("default_branch") or "main"),
            fork=bool(data.get("fork", False)),
            archived=bool(data.get("archived", False)),
            license_name=license_name,
            topics=[str(topic) for topic in topics],
            stargazers_count=int(data.get("stargazers_count") or 0),
            forks_count=int(data.get("forks_count") or 0),
            open_issues_count=int(data.get("open_issues_count") or 0),
            created_at=str(data.get("created_at") or ""),
            pushed_at=str(data.get("pushed_at") or ""),
        )


@dataclass
class RepositoryAudit:
    """Audit result for one repository."""

    repository: RepositorySnapshot
    checks: list[AuditCheck]

    @property
    def score(self) -> float:
        possible = sum(check.possible for check in self.checks)
        earned = sum(check.earned for check in self.checks)
        if possible == 0:
            return 0.0
        return round((earned / possible) * 100, 1)

    @property
    def recommendations(self) -> list[str]:
        return _unique_recommendations(self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": asdict(self.repository),
            "score": self.score,
            "checks": [asdict(check) for check in self.checks],
            "recommendations": self.recommendations,
        }


@dataclass
class ProfileAudit:
    """Complete profile audit, including selected repository audits."""

    profile: ProfileSnapshot
    checks: list[AuditCheck]
    repositories: list[RepositoryAudit]
    generated_at: str

    @property
    def score(self) -> float:
        possible = sum(check.possible for check in self.checks)
        earned = sum(check.earned for check in self.checks)
        if possible == 0:
            return 0.0
        return round((earned / possible) * 100, 1)

    @property
    def recommendations(self) -> list[str]:
        return _unique_recommendations(
            [
                *[check for check in self.checks],
                *[
                    check
                    for repository in self.repositories
                    for check in repository.checks
                ],
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "profile": asdict(self.profile),
            "score": self.score,
            "checks": [asdict(check) for check in self.checks],
            "repositories": [repository.to_dict() for repository in self.repositories],
            "recommendations": self.recommendations,
        }


def _unique_recommendations(checks: list[AuditCheck]) -> list[str]:
    return _unique_strings(
        check.recommendation
        for check in checks
        if check.recommendation and check.status != "pass"
    )


def _unique_strings(values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result
