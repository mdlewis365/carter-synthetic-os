<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: fluid_pump_loop_pack
pack_name: Fluid Pump Loop Pack
pack_type: domain
supported_modes: solve-problem, review-design, diagnose-root-cause, suggest-improvements, explore-novel-solution
domain_keywords: pump loop, coolant loop, cooling loop, low-flow alarm, low flow alarm, low flow, pump, pump head, pump selection, available head, pipe, pipe selection, piping, hose, centrifugal pump, transfer pump, closed loop, open loop, suction piping, discharge piping, strainer, fouled strainer, clean strainer, observed strainer loss, filter loss, filter pressure drop, pressure drop, friction loss, head loss, valve loss, manifold loss, hydraulic loss, hydraulic losses, hydraulic, hydraulic cylinder, hydraulic actuator, hydraulic press, press fixture, clamp force, low clamp force, cap-end pressure, rod-side, piston area, cylinder bore, bore diameter, pump pressure, relief valve, relief setting, directional valve, manifold pressure drop, valve pressure drop, restricted valve path, clogged valve screen, static leakdown, leakdown rate, hydraulic oil, oil cooler, cooling water, water flow, heat exchanger, lbf, psi, in^2, F = P * A, force = pressure * area, static head, elevation head, total dynamic head, TDH, ft head, pump rated head, rated head, pressure differential, flow demand, pipe velocity, pump curve, system curve, flow transmitter, pressure sensor, NPSH, cavitation, brake horsepower, BHP, shaft power, motor horsepower, motor hp, motor current, pump efficiency, hydraulic basis, hydraulic selection, hydraulics, gpm

## Scope

Fluid pump-loop design review, root-cause diagnosis, solve-problem sizing,
suggest-improvements, and bounded preliminary screening for pump/pipe systems.
Use this pack for centrifugal and transfer pumps; closed or open loops;
suction/discharge piping; strainer, filter, valve, and manifold losses;
static/elevation head; pressure differential; flow demand; pump curve or system
curve comparisons; NPSH/cavitation risk; and motor or shaft-power screening.
Also use this pack for hydraulic fluid-power circuits and hydraulic actuator or
cylinder diagnostics, including hydraulic press fixtures, clamp-force faults,
pump-pressure to cylinder-pressure relationships, directional valve or manifold
pressure drop, relief-valve capacity checks, restricted valve paths, clogged
valve screens, pressure-force conversion using F = P * A, and piston area from
cylinder bore diameter.

## Out Of Scope

Detailed pump selection without a supplied pump curve, certified pressure-vessel
or code compliance, two-phase or slurry hydraulics, corrosive or hazardous
fluid compatibility decisions, sanitary validation, chemical reaction hazards,
cavitation damage assessment without inspection evidence, and purely mechanical
power-transmission reviews such as conveyor gearmotors, gearbox ratios, drive
pulleys, belt speed, belt pull, shaft torque limits, and startup torque unless
fluid-specific evidence is also present.

Generic mechanical terms such as lbf, hp, horsepower, motor horsepower, motor,
torque, gearbox, pulley, belt pull, rpm, speed, shaft, efficiency, drive, and
ratio are not sufficient routing evidence for this pack by themselves.

## Expected Document Roles

- flow or duty-point requirement
- pump curve or tabulated pump performance
- system curve or loss summary
- suction/discharge piping geometry
- strainer/filter/valve/manifold loss data
- static head or elevation basis
- fluid properties or specific gravity
- motor rating and pump efficiency
- NPSHA/NPSHR basis when cavitation is in scope
- hydraulic cylinder bore diameter, cap-end pressure, pump pressure, relief
  setting, directional valve or manifold pressure drop, hydraulic oil condition,
  static leakdown rate, and required clamp force when actuator force is in scope
- acceptance criteria, safety margin, or troubleshooting observations

## Canonical Units

- flow: gpm; L/min or m^3/hr only when current MCM unit support validates them
- pressure: psi; Pa or kPa only when current MCM unit support validates them
- hydraulic head/loss: ft for display; use ft_head internally for head/loss/TDH/NPSH validation; accept ft_water, ft_h2o, feet_of_water, "ft of water", and "feet of water" as hydraulic-head aliases in water pump-loop contexts
- geometric length: ft, in, m; keep equivalent_pipe_length_ft, physical_installed_pipe_length_ft, pipe diameter, radius, and area as geometry unless a supported head/loss formula transforms them
- power: hp, kW, W
- force: lbf when using psi and in^2 actuator area
- actuator area: in^2 from bore diameter in in
- density/specific gravity: dimensionless specific gravity when used in US customary pump formulas
- efficiency: fraction or percent
- velocity: ft/s or m/s when valid area and flow conversions are supplied
- pipe diameter: in, ft, mm, m when conversion paths are explicit and unit-valid

## Safe Equation Patterns

- Use canonical MCM variable names for document-derived hydraulic inputs:
  - static_elevation_head_ft
  - fixed_equipment_loss_ft
  - equivalent_pipe_length_ft
  - physical_installed_pipe_length_ft
  - available_npsh_ft
- For pump/pipe selection, calculate installed pipe cost once per pipe option
  using component-level variables:
  - pipe_A_installed_cost_usd = physical_installed_pipe_length_ft * pipe_A_installed_cost_per_ft
  - pipe_B_installed_cost_usd = physical_installed_pipe_length_ft * pipe_B_installed_cost_per_ft
  - pipe_C_installed_cost_usd = physical_installed_pipe_length_ft * pipe_C_installed_cost_per_ft
- Do not name pipe-only installed cost as a candidate-local pump combination
  such as config_A_P1_installed_pipe_cost_usd. Candidate total installed
  cost should equal pump purchase cost plus the pipe installed cost, for
  example config_A_P2_total_installed_cost_usd = pump_P2_purchase_cost_usd
  + pipe_A_installed_cost_usd.
- Use candidate-local variables for TDH, required pump head, BHP, NPSH
  margin, C3/C4/C5 checks, total installed cost, all-criteria pass, and
  score. Use pipe-only variables for diameter, area, velocity, friction loss,
  C2 pass, and installed pipe cost.
- For pump motor-loading C5 checks, prefer canonical candidate-local names:
  - config_X_PY_brake_hp
  - config_X_PY_allowable_motor_hp
  - config_X_PY_C5_pass
  Common variants such as brake_horsepower, brake_horsepower_hp, BHP, and
  allowable_motor_bhp are acceptable, but the canonical names reduce schema
  repair.
- Static elevation aliases must map to static_elevation_head_ft, including
  "static elevation difference", "static elevation head", "elevation
  difference", "source tank liquid level to header", "lift", and "static lift".
- If equations reference a canonical hydraulic input, include the same key in
  mcm_request.variables with source="document-derived" when the source document
  provides the value.

- total_dynamic_head_ft = static_head_ft + friction_head_ft + minor_loss_head_ft + required_pressure_head_ft
- static_elevation_head_ft, fixed_equipment_loss_ft, pipe_*_friction_head_ft, pipe_*_friction_loss_ft, total_dynamic_head_ft/TDH, pump_*_rated_head_ft, required_pump_head_ft, available_npsh_ft, pump_*_required_npsh_ft, and npsh_margin_ft are hydraulic-head quantities even when displayed as ft
- Do not add geometric pipe length or diameter directly to hydraulic head/loss; first compute a supported friction/head-loss result, then add that head result to TDH
- pressure_head_ft = pressure_psi * 2.31 / specific_gravity
- pressure_psi = head_ft * specific_gravity / 2.31
- piston_radius_in = cylinder_bore_diameter_in / 2.0
- piston_area_in2 = PI_VALUE * (piston_radius_in ** 2)
- clamp_force_lbf = pressure_psi * piston_area_in2
- required_pressure_psi = required_force_lbf / piston_area_in2
- pressure_after_clean_valve_psi = pump_pressure_psi - expected_clean_valve_pressure_drop_psi
- predicted_clamp_force_clean_valve_lbf = pressure_after_clean_valve_psi * piston_area_in2
- hydraulic_hp = flow_gpm * head_ft * specific_gravity / 3960.0
- brake_hp = hydraulic_hp / pump_efficiency_fraction
- motor_margin_hp = motor_hp - brake_hp
- npsh_margin_ft = npsha_ft - npshr_ft
- pipe_area_sq_ft = PI_VALUE * ((pipe_diameter_in / 12.0 / 2.0) ** 2)
- velocity = flow / area only when the flow-to-area unit conversion is explicit and supported
- corrected_clean_loss_psi = clean_reference_loss_psi * flow_ratio ** 2 when the source documents justify square-law scaling
- criterion_pass = available_value >= required_value
- criterion_pass = candidate_value <= max_allowed_value

## Constraint Patterns

Use C1-C5 style checks when the evidence supports them:

- C1: observed flow or pressure/head meets the stated requirement
- C2: clean-condition or corrected-condition prediction meets the requirement
- C3: pump and motor capacity are adequate at the duty point
- C4: NPSH margin is adequate when NPSH data is provided
- C5: no evidence of leak, bypass, blocked discharge, suction restriction, or instrumentation error when diagnostic evidence is supplied

For hydraulic clamp-force diagnosis, use the same C1-C5 discipline:

- C1 observed failed condition: observed_clamp_force_lbf < required_clamp_force_lbf
- C2 pump pressure capacity is adequate
- C3 relief valve setting is adequate
- C4 clean-valve/manifold pressure-drop recovery meets required clamp force
- C5 cylinder static leakdown is acceptable

For selection or screening, require all hard criteria first, then select by the
source-stated objective such as lowest power, lowest head loss, or highest
margin. Keep rejected alternatives visible with their failed criteria.
For pump/pipe configuration selection, keep machine-readable candidate keys
separate from display labels. Use keys that match candidate-scoped computed
fields, for example `config_A_P1`, `config_B_P2`, and `config_C_P3`.
Selection equations should compute `viable_configuration_keys`,
`viable_configuration_labels`, `selected_configuration_key`,
`selected_configuration_label`, and `selected_min_cost_usd`, with
`selected_configuration_key` selected from the key list and
`selected_configuration_label` looked up from the selected key. Do not use
display text such as `Pipe B, Pump P2` as the primary key for governance.

## Diagnostic Logic Patterns

- fouled strainer or filter: observed strainer/filter differential pressure exceeds clean or allowed loss while pump/motor/suction evidence is otherwise adequate
- restricted valve or manifold path: downstream differential pressure is excessive and clean strainer/filter evidence does not explain the loss
- undersized or too-long piping: calculated friction or minor loss consumes the available head margin
- inadequate suction head or cavitation risk: NPSH margin is below the supplied minimum or suction pressure/vacuum evidence is out of range
- pump cannot meet duty point: supplied pump curve or operating point cannot satisfy required flow/head
- motor overload: brake horsepower exceeds motor rating or allowed service-factor basis
- wrong impeller diameter or speed: only diagnose when curve/speed/impeller data are supplied
- hydraulic clamp-force restriction: observed clamp force fails, pump pressure
  capacity passes, relief setting passes, static leakdown passes, and predicted
  clamp force with a clean valve/manifold pressure drop meets the required clamp
  force; root cause should be excessive directional valve/manifold pressure
  drop, likely a restricted valve path or clogged valve screen
- measurement inconsistency: conflicting pressure/flow data or missing curve evidence should lead to human review, not a forced root cause

## Common Failure Modes

Confusing pressure with head, using water-specific 2.31 conversion for
non-water fluids without specific gravity, double-counting static and pressure
head, treating dirty filter loss as clean prediction, extrapolating beyond pump
curve range, ignoring NPSH, comparing motor hp to hydraulic hp instead of brake
hp, and accepting unsupported unit conversions.

## MCM Routing Guidance

Use deterministic MCM for bounded pressure/head/flow calculations, hydraulic
pressure-force conversion, actuator piston-area calculations, pump and motor
margin checks, relief-capacity checks, NPSH margin checks, corrected dirty/clean
loss comparisons, diagnostic pass/fail criteria, and selection among supplied
pump-loop options. Do not invent pump curves, fluid properties, loss
coefficients, efficiency, NPSH values, hydraulic component settings, or
regulatory/code criteria.

## Human-Review Triggers

Missing pump curve when pump selection is requested, missing fluid properties
for non-water or nonstandard fluid, two-phase flow, slurry, corrosive,
high-temperature, hazardous, sanitary, or chemically reactive fluids,
safety-critical pressure vessel/code compliance, cavitation damage assessment
without inspection data, extrapolation beyond provided pump curve or
affinity-law limits, unsupported units or unresolved conversions, and
insufficient evidence to distinguish pump wear, blockage, suction restriction,
and instrumentation error.

## Reporting Guidance

Report the duty point, observed and required flow/head/pressure, actuator force
and area when supplied, pump/motor margin, relief margin, NPSH margin when
supplied, likely diagnostic cause when supported, failed criteria, assumptions,
and the next verification step. Deterministic criteria failures are engineering
findings, not MCM execution failures.

## Evidence-Basis Guidance

Tie conclusions to pump curves, system/loss summaries, field pressure and flow
readings, strainer/filter observations, motor data, NPSH data, MCM-computed
margins, checked criteria, assumptions, and missing values.

## Forbidden Cross-Domain Language

Do not mention AWG, fuse, 24 VDC, conductor, voltage drop, duct velocity, fan
static pressure, purge air, scfm, dewpoint, aircraft certification, airworthy,
safe for flight, bracket stress, or payload unless those terms appear in the
user problem or supplied artifacts.
