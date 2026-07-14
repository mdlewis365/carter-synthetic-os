# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import json

from carter.runtime import CarterRuntime
from shared.config import load_settings


def main() -> None:
    runtime = CarterRuntime(load_settings({}))
    result = runtime.respond(
        "synthetic-example-session",
        "Run the deterministic Carter public example.",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
