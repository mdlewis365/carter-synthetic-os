<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: dc_controls_power_pack
pack_name: DC Controls Power Pack
pack_type: domain
supported_modes: solve-problem, review-design, diagnose-root-cause, suggest-improvements, explore-novel-solution
domain_keywords: 24 VDC, 24VDC, voltage drop, conductor, fuse, power supply, load current, panel, AWG, terminal, connector, inrush, remote panel

## Scope

Low-voltage DC controls power, load-current aggregation, conductor voltage-drop
checks, fuse and power-supply sizing, branch/feeder separation, and control
panel source discipline.

## Expected Document Roles

- load schedule or bill of loads
- power supply rating or datasheet
- fuse ratings or protection criteria
- conductor size, length, resistance, or AWG table
- field notes for remote panel distance or installed measurements

## Canonical Units

- voltage: V
- current: A
- power: W
- resistance: ohm
- conductor size: AWG
- length: ft

## Safe Equation Patterns

- load_power_W = load_voltage_V * load_current_A
- total_load_A = load_1_current_A + load_2_current_A
- voltage_drop_V = load_current_A * conductor_resistance_ohm_per_ft * one_way_length_ft * 2.0
- voltage_drop_percent = voltage_drop_V / nominal_voltage_V * 100.0
- criterion_pass = voltage_drop_percent <= maximum_voltage_drop_percent
- conductor_18_AWG_score = if(conductor_18_AWG_pass, conductor_18_AWG, null)
- selected_conductor_AWG = max_ignore_null([conductor_18_AWG_score, conductor_16_AWG_score, conductor_14_AWG_score])
- selected_conductor_AWG_label = argmax_label_ignore_null([conductor_18_AWG_score, conductor_16_AWG_score, conductor_14_AWG_score], ["18 AWG", "16 AWG", "14 AWG"])

Use `max_ignore_null` for AWG selection when larger AWG numbers represent the
smallest acceptable physical conductor among viable candidates. Use
`min_ignore_null` for minimum acceptable ratings such as power-supply ampere
rating or fuse ampere rating.

## Constraint Patterns

Check supply capacity, derating basis, fuse rating, voltage drop, conductor
rating, and source-specific load allocation without double-counting.

## Common Failure Modes

Double-counted schedule and field-note loads, comparing derated usable capacity
to required rated output, missing conductor length, missing AWG resistance,
unsupported inrush assumptions, and terminal/connector losses not supplied by
source evidence.

## MCM Routing Guidance

Use deterministic MCM for load totals, voltage-drop checks, selected conductor,
power-supply rating, fuse rating, and pass/fail criteria when required source
values are present.

## Human-Review Triggers

Missing conductor route length, missing protection criteria, unresolved
duplicate load sources, unknown inrush/transient requirement, or code/vendor
requirements outside the supplied evidence.

## Reporting Guidance

Use electrical controls language only when grounded in the problem or artifacts.
Report selected conductor, power supply, fuse, voltage-drop margin, and source
limitations separately.

## Evidence-Basis Guidance

Tie conclusions to uploaded schedules/datasheets/field notes, MCM-computed load
and voltage-drop outputs, checked criteria, and unresolved missing electrical
source values.

## Forbidden Cross-Domain Language

Do not mention duct velocity, fan static pressure, round duct diameter, cfm, or
fpm unless those terms appear in the user problem or supplied artifacts.
