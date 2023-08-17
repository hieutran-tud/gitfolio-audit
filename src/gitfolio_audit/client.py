"""Small, dependency-free GitHub REST client used by the CLI."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://api.github.com"
_LOGIN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}$")


class GitHubAPIError(RuntimeError):
    """Friendly wrapper for network, API, and response errors."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class GitHubClient:
    """Read public GitHub data with optional token-based rate-limit relief."""

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 15.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.opener = opener

    def get_profile(self, username: str) -> dict[str, Any]:
        _validate_login(username)
        return self._request(f"/users/{quote(username, safe='')}")

    def list_repositories(self, username: str) -> list[dict[str, Any]]:
        _validate_login(username)
        repositories: list[dict[str, Any]] = []
        page = 1
        while page <= 10:
            result = self._request(
                f"/users/{quote(username, safe='')}/repos?per_page=100&sort=updated&page={page}"
            )
            if not isinstance(result, list):
                raise GitHubAPIError("GitHub returned an unexpected repository response.")
            repositories.extend(result)
            if len(result) < 100:
                break
            page += 1
        return repositories

    def get_repository(self, full_name: str) -> dict[str, Any]:
        owner, repository = _split_repository_name(full_name)
        return self._request(f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}")

    def list_contents(
        self,
        full_name: str,
        path: str = "",
        *,
        ref: str | None = None,
    ) -> list[dict[str, Any]]:
        owner, repository = _split_repository_name(full_name)
        encoded_path = quote(path.strip("/"), safe="/")
        endpoint = f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/contents"
        if encoded_path:
            endpoint += f"/{encoded_path}"
        if ref:
            endpoint += f"?ref={quote(ref, safe='') }"
        result = self._request(endpoint)
        if isinstance(result, dict):
            return [result]
        if not isinstance(result, list):
            raise GitHubAPIError("GitHub returned an unexpected contents response.")
        return result

    def has_profile_readme(self, username: str) -> bool:
        """Check for the conventional public ``username/username`` repository."""

        _validate_login(username)
        try:
            repository = self.get_repository(f"{username}/{username}")
            entries = self.list_contents(str(repository.get("full_name") or f"{username}/{username}"))
        except GitHubAPIError as error:
            if error.status_code == 404:
                return False
            raise
        return any(
            str(entry.get("name") or "").lower() == "readme.md"
            for entry in entries
        )

    def _request(self, endpoint: str) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "gitfolio-audit/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, headers=headers, method="GET")
        try:
            with self.opener(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as error:
            detail = _error_detail(error)
            raise GitHubAPIError(
                f"GitHub API request failed ({error.code}): {detail}",
                status_code=error.code,
            ) from error
        except URLError as error:
            raise GitHubAPIError(f"Could not reach GitHub: {error.reason}") from error
        except TimeoutError as error:
            raise GitHubAPIError("The GitHub API request timed out.") from error

        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GitHubAPIError("GitHub returned an invalid JSON response.") from error


def _validate_login(login: str) -> None:
    if not _LOGIN_PATTERN.fullmatch(login):
        raise GitHubAPIError(f"Invalid GitHub username: {login!r}")


def _split_repository_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip("/").split("/")
    if len(parts) != 2 or not all(parts):
        raise GitHubAPIError("Repository names must use the owner/name format.")
    _validate_login(parts[0])
    if not re.fullmatch(r"^[A-Za-z0-9_.-]+$", parts[1]):
        raise GitHubAPIError(f"Invalid GitHub repository name: {parts[1]!r}")
    return parts[0], parts[1]


def _error_detail(error: HTTPError) -> str:
    try:
        payload = json.loads(error.read().decode("utf-8"))
        if isinstance(payload, dict) and payload.get("message"):
            return str(payload["message"])
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        pass
    return error.reason or "unknown error"
