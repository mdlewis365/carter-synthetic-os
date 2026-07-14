# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import json

from eas.workflow import EngineeringWorkflow


def main() -> None:
    result = EngineeringWorkflow().run(
        {
            "fixture_id": "synthetic_thermal_enclosure_v1",
            "case_id": "synthetic-eas-example",
            "mode": "review-design",
            "problem_statement": "Evaluate the synthetic enclosure fixture.",
            "timestamp_utc": "2026-01-01T00:00:00+00:00",
        }
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
