# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Local development command for Carter Synthetic OS."""

from __future__ import annotations

import logging

from shared.config import ConfigError, load_settings

from .web import create_app


def main() -> int:
    try:
        settings = load_settings()
    except ConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if settings.ephemeral_secret:
        logging.getLogger(__name__).warning(
            "FLASK_SECRET_KEY is unset or a placeholder; sessions will reset "
            "when this process exits."
        )
    app = create_app(settings)
    print(f"Carter Synthetic OS: http://{settings.host}:{settings.port}")
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        use_reloader=settings.debug,
        threaded=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
