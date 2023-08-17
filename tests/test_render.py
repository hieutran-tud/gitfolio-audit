from datetime import datetime, timezone

from gitfolio_audit.audit import audit_profile
from gitfolio_audit.models import ProfileSnapshot
from gitfolio_audit.render import render_json, render_markdown, render_terminal


def test_renderers_include_score_and_recommendations():
    report = audit_profile(
        ProfileSnapshot(login="alex-dev", name="Alex", public_repos=0),
        [],
        as_of=datetime(2026, 8, 28, tzinfo=timezone.utc),
    )

    terminal = render_terminal(report)
    markdown = render_markdown(report)
    json_report = render_json(report)

    assert "Overall score" in terminal
    assert "Recommended next steps" in markdown
    assert '"score"' in json_report
