"""Allow ``python -m gitfolio_audit`` to run the CLI."""

from .cli import main


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
