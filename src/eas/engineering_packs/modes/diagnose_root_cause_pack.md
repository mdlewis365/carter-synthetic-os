<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: diagnose_root_cause_pack
pack_name: Diagnose Root Cause Mode Pack
pack_type: mode
supported_modes: diagnose-root-cause
domain_keywords:

## Scope

Use this mode pack when the user asks for root-cause diagnosis or explanation
of observed failures, anomalies, or unexpected behavior.

## MCM Routing Guidance

Use deterministic MCM to test hypotheses against observed values, compare
expected versus measured behavior, and identify impossible or unlikely causes.

## Reporting Guidance

State the most likely cause conditionally, show elimination logic, and avoid
turning diagnostic evidence criteria into release-status failures unless the
problem asks for release approval.
