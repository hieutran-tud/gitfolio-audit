import io
import json
from urllib.error import HTTPError

import pytest

from gitfolio_audit.client import GitHubAPIError, GitHubClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_client_uses_github_headers_and_parses_profile():
    calls = []

    def opener(request, timeout):
        calls.append((request.full_url, request.headers, timeout))
        return FakeResponse({"login": "alex-dev", "public_repos": 2})

    client = GitHubClient(token="secret", opener=opener)
    result = client.get_profile("alex-dev")

    assert result["login"] == "alex-dev"
    assert calls[0][0].endswith("/users/alex-dev")
    assert calls[0][1]["Authorization"] == "Bearer secret"
    assert calls[0][1]["X-github-api-version"] == "2022-11-28"


def test_client_reports_api_errors_with_status_code():
    def opener(request, timeout):
        raise HTTPError(
            request.full_url,
            404,
            "Not Found",
            {},
            io.BytesIO(b'{"message":"Not Found"}'),
        )

    client = GitHubClient(opener=opener)

    with pytest.raises(GitHubAPIError, match="Not Found") as error:
        client.get_repository("alex-dev/missing")

    assert error.value.status_code == 404


def test_invalid_repository_name_is_rejected_before_request():
    client = GitHubClient(opener=lambda *args, **kwargs: FakeResponse({}))

    with pytest.raises(GitHubAPIError, match="owner/name"):
        client.get_repository("not-a-repository")
