# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import json

from csc.interpretation import interpret_buffer
from csc.state import SensorySessionStore


def main() -> None:
    session_id = "synthetic-csc-example"
    store = SensorySessionStore()
    store.set_hearing(session_id, True)
    event = store.add_transcript(
        session_id,
        "Carter, classify this synthetic transcript.",
        speech_detected=True,
        source="synthetic_text_fixture",
    )
    interpretation = interpret_buffer(store.context(session_id), backend="mock")
    store.set_interpretation(session_id, interpretation)
    print(
        json.dumps(
            {
                "event": event.public_dict(),
                "interpretation": interpretation,
                "state": store.snapshot(session_id),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
