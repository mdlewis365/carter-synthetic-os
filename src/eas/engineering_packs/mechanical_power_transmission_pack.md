<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: mechanical_power_transmission_pack
pack_name: Mechanical Power Transmission Pack
pack_type: domain
supported_modes: review-design, solve-problem, suggest-improvements
domain_keywords: conveyor, gearmotor, gearbox, gearbox ratio, reducer, drive pulley, pulley diameter, belt speed, belt pull, chain pull, output rpm, motor rpm, horsepower, startup horsepower, startup torque, shaft torque, gearbox rating, reducer rating, torque margin, belt drive, chain drive, sprocket, mechanical drive, power transmission

## Scope

Mechanical power-transmission and conveyor-drive screening, including conveyors,
gearmotors, belt drives, chain drives, pulleys, sprockets, reducer or gearbox
ratios, output rpm, belt or chain speed, motor horsepower, startup horsepower,
belt pull, chain pull, startup torque, gearbox output torque, shaft torque
ratings, service/design margins, and drive efficiency.

Use this pack for deterministic review of supplied drive sizing, speed range,
power capacity, startup torque, gearbox or reducer rating, and shaft limit
criteria. Do not use this pack for fluid pump loops, hydraulic actuators,
coolant loops, heat exchangers, electrical motor controls, or structural bracket
stress unless those domains are separately supported by the supplied evidence.

## Expected Document Roles

- conveyor, belt, chain, or driven-equipment requirements
- required speed range or throughput basis
- motor speed, motor horsepower, and operating limit notes
- gearbox/reducer ratio, efficiency, and torque rating
- pulley or sprocket diameter, radius, wrap, and traction basis
- steady belt or chain pull and startup factor
- shaft, key, bearing, or coupling ratings when credited
- acceptance criteria, service factor, or design margin requirements

## Canonical Units

- rotational speed: rpm
- linear speed: ft/min when using US customary conveyor formulas
- length: in or ft, with explicit in-to-ft conversion
- force or pull: lbf
- power: hp
- torque: lb-ft, lbft, or lbf*ft when supported by MCM normalization
- efficiency, ratio, service factor, and design margin: dimensionless

## Safe Equation Patterns

- output_rpm = motor_speed_rpm / gearbox_ratio
- pulley_diameter_ft = pulley_diameter_in / 12
- pulley_radius_ft = pulley_diameter_in / 24
- belt_speed_ft_per_min = PI_VALUE * pulley_diameter_ft * output_rpm
- steady_hp = belt_pull_lbf * belt_speed_ft_per_min / (33000 * efficiency)
- startup_force_lbf = steady_belt_pull_lbf * startup_factor
- startup_hp = startup_force_lbf * belt_speed_ft_per_min / (33000 * efficiency)
- motor_torque_lbft = hp * 5252 / rpm
- gearbox_output_torque_lbft = motor_torque_lbft * gearbox_ratio * gearbox_efficiency
- pulley_torque_lbft = belt_pull_lbf * pulley_radius_ft
- margined_startup_torque_lbft = pulley_torque_lbft * design_margin
- criterion_pass = computed_value >= minimum_required_value
- criterion_pass = computed_value <= maximum_allowed_value
- overall_release_status = PASS only when all source-defined hard criteria pass

## Constraint Patterns

Use deterministic MCM for pass/fail checks against source-defined speed range,
horsepower limits, startup horsepower limits, gearbox torque rating, reducer
rating, shaft torque limit, and supplied service or design margins. Treat a
failed criterion as a computed engineering result, not an MCM execution failure.

For review-design mode, report whether the proposed drive meets each supplied
criterion. For solve-problem mode, compute the requested sizing value or select
among supplied options only when all candidate data and acceptance criteria are
provided. For suggest-improvements mode, compare practical changes such as
gearbox ratio, pulley diameter, motor size, or service factor only when the
source documents provide enough bounds to keep the comparison deterministic.

## Diagnostic Logic Patterns

- speed ratio selection failure: computed belt or chain speed is outside the
  required speed range while horsepower and torque checks pass
- motor undersizing: steady or startup horsepower exceeds the allowed motor
  horsepower or service-factor basis
- gearbox/reducer torque undersizing: required startup torque with margin
  exceeds catalog output torque or reducer rating
- shaft limit failure: raw or margined torque exceeds the shaft, key, bearing,
  or coupling limit supplied by the source documents
- traction or wrap uncertainty: belt/chain pull is supplied but wrap, slip, or
  traction basis is missing; flag human review if it affects the conclusion

## Human-Review Triggers

Missing service factor basis; shock loading or reversing duty not defined;
braking or holding loads; vertical lifting or suspended loads; personnel safety
conveyor applications; unknown gearbox service class; missing duty cycle;
missing belt/chain wrap or traction/slip basis; missing shaft, key, or bearing
ratings; dynamic torsional vibration or resonance; and code-regulated machinery
safety claims.

## Reporting Guidance

Report output rpm, belt or chain speed, steady horsepower, startup horsepower,
motor torque, gearbox output torque, pulley torque, design-margin torque, and
each source-defined pass/fail check. Clearly distinguish speed failures from
power or torque capacity failures. Do not describe generic lbf, hp, rpm, motor,
gearbox, pulley, belt pull, shaft, efficiency, drive, or ratio terms as fluid
pump-loop evidence.

## Evidence-Basis Guidance

Tie conclusions to conveyor requirements, vendor motor/gearmotor data, gearbox
or reducer catalog ratings, pulley/sprocket dimensions, belt or chain pull
inputs, supplied startup factors, MCM-computed values, checked criteria,
assumptions, and missing service-factor or duty-cycle information.

## Forbidden Cross-Domain Language

Do not mention pump curve, NPSH, gpm, hydraulic pressure, coolant loop, heat
exchanger, AWG, fuse, 24 VDC, conductor, voltage drop, duct velocity, cfm, fpm
for ventilation, purge air, scfm, dewpoint, aircraft certification, airworthy,
or safe for flight unless those terms appear in the user problem or supplied
artifacts.
