<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: review_design_pack
pack_name: Review Design Mode Pack
pack_type: mode
supported_modes: review-design
domain_keywords:

## Scope

Use this mode pack when the user asks whether an existing design, sizing,
installation, or release package is acceptable.

## MCM Routing Guidance

Use deterministic MCM for design sufficiency checks, code or source acceptance
criteria, margins, and explicit pass/fail comparisons.

## Reporting Guidance

Separate design findings from source limitations. A failed deterministic
criterion is a computed engineering result, not a tool failure.
