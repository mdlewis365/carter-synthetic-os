# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import json

from sis.workflow import IdeationWorkflow


def main() -> None:
    result = IdeationWorkflow().run(
        {
            "fixture_id": "synthetic_inspection_scheduler_v1",
            "mode": "system-architecture",
            "problem_statement": ("Generate a synthetic inspection scheduling hypothesis."),
        }
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
