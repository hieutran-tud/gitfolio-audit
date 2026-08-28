# Gitfolio Audit

Gitfolio Audit is a small, read-only command-line tool that turns a public GitHub profile into an actionable portfolio-quality report.

It checks whether a profile communicates a clear direction and whether selected repositories show the engineering signals a visitor expects: documentation, reproducible setup, tests, CI, licensing, discoverability, ownership, and maintenance.

The project is intentionally dependency-light. Runtime code uses Python's standard library; `pytest` is only needed for development.

## Why this exists

GitHub profiles often contain useful work that is difficult to evaluate quickly. A score alone is not useful, so every point in this tool is tied to an explainable finding and a concrete recommendation.

The score is a conversation starter, not a judgment of a developer's ability.

This repository is the index for the [ML Reliability Toolkit](https://github.com/hieutran-tud/hieutran-tud), a set of companion projects that demonstrate the engineering practices the auditor checks. Together, they cover data validation, experiment tracking, model documentation, and drift monitoring:

- [Data Contract Checker](https://github.com/hieutran-tud/data-contract-checker)
- [Experiment Tracker Lite](https://github.com/hieutran-tud/experiment-tracker-lite)
- [Model Card Generator](https://github.com/hieutran-tud/model-card-generator)
- [Data Drift Monitor](https://github.com/hieutran-tud/data-drift-monitor)

## Features

- Audits a public GitHub profile and recently updated repositories.
- Detects profile positioning, external links, public work, and recent activity.
- Checks repository descriptions, READMEs, licenses, topics, dependency manifests, tests, CI, fork status, and maintenance.
- Produces terminal, Markdown, or JSON output.
- Supports an optional `GITHUB_TOKEN` to reduce anonymous API rate-limit pressure.
- Uses injected timestamps and an in-memory test suite for deterministic verification.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"

gitfolio-audit octocat
python -m gitfolio_audit octocat
gitfolio-audit octocat --format markdown --output report.md
gitfolio-audit octocat --format json --output report.json
```

For repeated use, set a token in the environment rather than putting it in shell history:

```bash
export GITHUB_TOKEN="your-token"
# PowerShell: $env:GITHUB_TOKEN = "your-token"
gitfolio-audit octocat
```

The tool only requests public profile, repository, and root-content endpoints. It does not modify GitHub data.

## Reproducible example

Run an audit and save both a human-readable report and machine-readable output:

```bash
gitfolio-audit octocat --format markdown --output report.md
gitfolio-audit octocat --format json --output report.json
```

The generated files make the findings easy to review, share, or process in another tool.

## Scoring model

The profile score is out of 100:

| Area | Points |
| --- | ---: |
| Profile README | 25 |
| Display name | 10 |
| Professional positioning | 20 |
| External link | 10 |
| Public body of work | 20 |
| Recent activity | 15 |

Repository scores are normalized to 100 from nine checks: description, README, license, topics, reproducible setup, tests, CI, project ownership, and maintenance.

## Example output

```text
Gitfolio Audit — @octocat
Overall score: 72.0/100

Profile checks
[PASS] Profile README: 25/25 — A profile README is visible to visitors.
[PASS] Display name: 10/10 — The profile identifies you as The Octocat.
[WARN] Public body of work: 10/20 — The account exposes only 2 public repositories.
```

## Design notes

The project is split into four small layers:

1. `client.py` handles GitHub HTTP requests and friendly API errors.
2. `models.py` converts API responses into stable, typed snapshots.
3. `audit.py` applies deterministic checks without network access.
4. `render.py` formats the same report for humans or automation.

This separation makes the scoring rules easy to test and makes it possible to add another renderer without changing the audit logic.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

The GitHub Actions workflow runs the test suite on Python 3.11 and 3.12 for pushes and pull requests.

## Limitations and roadmap

The first version intentionally focuses on public REST data and repository root signals. It does not try to infer code quality, measure commit authenticity, or scrape dynamic profile sections such as pinned repositories.

Possible next steps:

- Add a local `--from-json` mode for offline audits.
- Add optional README section checks for setup, usage, results, and limitations.
- Add a configuration file for custom scoring thresholds.
- Add a GitHub App mode for organization-wide audits.

## License

MIT. See [LICENSE](LICENSE).
