"""Command-line entry point for Gitfolio Audit."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .audit import audit_profile, audit_repository
from .client import GitHubAPIError, GitHubClient
from .models import ProfileSnapshot, RepositorySnapshot
from .render import render_json, render_markdown, render_terminal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitfolio-audit",
        description="Audit a public GitHub profile and selected repositories.",
    )
    parser.add_argument("username", help="GitHub username to audit")
    parser.add_argument(
        "--format",
        choices=("terminal", "markdown", "json"),
        default="terminal",
        help="Report format (default: terminal)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the report to a file instead of stdout",
    )
    parser.add_argument(
        "--repo-limit",
        type=int,
        default=6,
        help="Maximum number of recently updated repositories to inspect (default: 6)",
    )
    parser.add_argument(
        "--token",
        help="Optional GitHub token; GITHUB_TOKEN is used when omitted",
    )
    parser.add_argument(
        "--as-of",
        help="Optional ISO timestamp for reproducible scoring, e.g. 2026-08-28T00:00:00Z",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.repo_limit < 0:
        print("--repo-limit must be zero or greater.", file=sys.stderr)
        return 2

    try:
        as_of = _parse_as_of(args.as_of)
        client = GitHubClient(token=args.token or os.getenv("GITHUB_TOKEN"))
        profile = ProfileSnapshot.from_dict(client.get_profile(args.username))
        raw_repositories = client.list_repositories(args.username)
        repositories = [RepositorySnapshot.from_dict(item) for item in raw_repositories]
        repositories = _recent_repositories(repositories, args.repo_limit)
        profile_readme_exists = client.has_profile_readme(args.username)
        repository_audits = []
        for repository in repositories:
            entries = client.list_contents(repository.full_name, ref=repository.default_branch)
            repository_audits.append(
                audit_repository(repository, entries, as_of=as_of)
            )
        report = audit_profile(
            profile,
            repositories,
            profile_readme_exists=profile_readme_exists,
            as_of=as_of,
        )
        report.repositories = repository_audits
        rendered = _render(report, args.format)
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except GitHubAPIError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


def _recent_repositories(
    repositories: list[RepositorySnapshot],
    limit: int,
) -> list[RepositorySnapshot]:
    return sorted(
        repositories,
        key=lambda repository: repository.pushed_at or repository.created_at,
        reverse=True,
    )[:limit]


def _parse_as_of(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _render(report, output_format: str) -> str:
    if output_format == "json":
        return render_json(report)
    if output_format == "markdown":
        return render_markdown(report)
    return render_terminal(report)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
