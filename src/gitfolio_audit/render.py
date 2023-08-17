"""Human-readable renderers for audit reports."""

from __future__ import annotations

import json
from typing import Iterable

from .models import AuditCheck, ProfileAudit, RepositoryAudit


def render_json(report: ProfileAudit) -> str:
    """Render a machine-readable report."""

    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def render_terminal(report: ProfileAudit) -> str:
    """Render a compact report suitable for a terminal."""

    lines = [
        f"Gitfolio Audit - @{report.profile.login}",
        f"Overall score: {report.score:.1f}/100",
        "",
        "Profile checks",
    ]
    lines.extend(_terminal_check(check) for check in report.checks)
    if report.repositories:
        lines.extend(["", "Repository checks"])
        for repository in report.repositories:
            lines.append(
                f"\n{repository.repository.full_name} - {repository.score:.1f}/100"
            )
            lines.extend(_terminal_check(check, indent="  ") for check in repository.checks)
    recommendations = report.recommendations
    if recommendations:
        lines.extend(["", "Top recommendations"])
        lines.extend(f"- {recommendation}" for recommendation in recommendations[:8])
    return "\n".join(lines) + "\n"


def render_markdown(report: ProfileAudit) -> str:
    """Render a report that can be attached to an issue or committed as Markdown."""

    lines = [
        f"# Gitfolio Audit — @{report.profile.login}",
        "",
        f"**Overall score:** {report.score:.1f}/100  ",
        f"**Generated:** {report.generated_at}",
        "",
        "## Profile checks",
        "",
        _markdown_table(report.checks),
    ]
    if report.repositories:
        lines.extend(["", "## Repository checks", ""])
        for repository in report.repositories:
            lines.extend(
                [
                    f"### [{repository.repository.full_name}]({repository.repository.html_url or '#'})",
                    "",
                    f"**Score:** {repository.score:.1f}/100",
                    "",
                    _markdown_table(repository.checks),
                ]
            )
    if report.recommendations:
        lines.extend(["", "## Recommended next steps", ""])
        lines.extend(f"- {recommendation}" for recommendation in report.recommendations)
    lines.append("")
    return "\n".join(lines)


def _terminal_check(check: AuditCheck, *, indent: str = "") -> str:
    return (
        f"{indent}[{check.status.upper():4}] {check.label}: "
        f"{check.earned}/{check.possible} - {check.detail}"
    )


def _markdown_table(checks: Iterable[AuditCheck]) -> str:
    lines = [
        "| Check | Status | Score | Finding |",
        "| --- | --- | ---: | --- |",
    ]
    for check in checks:
        finding = _escape_pipe(check.detail)
        lines.append(
            f"| {check.label} | {check.status} | "
            f"{check.earned}/{check.possible} | {finding} |"
        )
    return "\n".join(lines)


def _escape_pipe(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
