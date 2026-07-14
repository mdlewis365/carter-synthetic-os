<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: aerospace_preliminary_design_pack
pack_name: Aerospace Preliminary Design Pack
pack_type: domain
supported_modes: solve-problem, review-design, diagnose-root-cause, suggest-improvements, explore-novel-solution
domain_keywords: aerospace, aircraft, UAV, drone, airframe, wing, lift, drag, thrust, propulsion, payload, mission profile, endurance, range, stall speed, wing loading, thrust-to-weight, takeoff weight, gross weight, empty weight, mass properties, center of gravity, load factor, airspeed, dynamic pressure, altitude, density, battery endurance, electric propulsion, propeller, rotor, fixed wing, VTOL

## Scope

Preliminary aerospace engineering assessments involving early-stage sizing,
mass properties, mission requirements, payload, lift/drag estimates, wing
loading, thrust-to-weight, stall speed, range/endurance estimates, propulsion
matching, basic load-factor awareness, and candidate concept screening.

## Out Of Scope

- certification claims
- airworthiness approval
- flight safety certification
- detailed finite element analysis
- detailed CFD
- detailed flight controls certification
- human-rated launch or flight decisions
- weapons guidance or targeting
- hazardous operational instructions
- regulatory compliance determinations unless source documents provide explicit criteria

## Expected Document Roles

- mission requirements
- payload requirements
- airframe geometry
- mass budget
- propulsion or motor data
- battery or fuel data
- aerodynamic assumptions
- environmental assumptions
- acceptance criteria
- safety margins
- regulatory or certification constraints if supplied

## Canonical Units

- mass: kg, lbm
- force: N, lbf
- speed: m/s, ft/s, mph, knots
- area: m^2, ft^2
- power: W, kW, hp
- energy: Wh, kWh, J
- density: kg/m^3, slug/ft^3
- acceleration: m/s^2, ft/s^2
- distance: m, ft, km, nmi
- time: s, min, hr
- dimensionless: coefficient, ratio, load factor

## Safe Equation Patterns

- wing_loading = weight / wing_area
- thrust_to_weight = thrust / weight
- lift = 0.5 * air_density * velocity ** 2 * wing_area * lift_coefficient
- drag = 0.5 * air_density * velocity ** 2 * reference_area * drag_coefficient
- stall_speed = sqrt((2 * weight) / (air_density * wing_area * max_lift_coefficient))
- endurance_hr = usable_energy_Wh / average_power_W
- range = cruise_speed * endurance
- margin = available_value - required_value
- criterion_pass = available_value >= required_value
- criterion_pass = candidate_value <= max_allowed_value

## Constraint Patterns

Check required payload capacity, maximum takeoff weight, minimum
thrust-to-weight ratio, maximum wing loading, minimum endurance, minimum range,
stall speed limit, power or energy budget, CG/mass-property bounds when source
data exists, structural load factor only when source criteria exist, and safety
margin requirements from supplied documents.

## Common Failure Modes

Missing or inconsistent mass budget, invented aerodynamic coefficients,
unsupplied structural allowables, unclear altitude/density condition, comparing
mass to force without weight conversion, energy budget double counting,
payload omitted from takeoff weight, and treating preliminary estimates as
real-world approval.

## MCM Routing Guidance

Use deterministic MCM for bounded sizing, unit-bearing estimates, pass/fail
checks, candidate screening, margin calculations, and selection among supplied
aerospace design options. Do not invent aerodynamic coefficients, structural
allowables, battery properties, or certification criteria when not supplied.

## Human-Review Triggers

Missing mass budget, missing payload requirement, missing wing area or
reference area, missing air density or altitude condition, missing lift/drag
coefficients, missing propulsion data, missing energy/fuel data, missing safety
margin, missing structural allowable, missing regulatory/certification
criteria, any flight-safety, airworthiness, human-rated, or operational
deployment claim, or any extrapolation beyond supplied source evidence.

## Reporting Guidance

Reports must clearly label outputs as preliminary engineering analysis. Include
selected concept, governing assumptions, source basis, computed margins,
pass/fail criteria, rejected alternatives, and verification steps. Do not claim
flight readiness, certification, or safety of flight. Recommend qualified
aerospace engineering review before real-world use.

## Evidence-Basis Guidance

Tie conclusions to uploaded mission requirements, candidate tables,
datasheets, aerodynamic assumptions, MCM-computed values, checked criteria, and
missing information. Distinguish source-provided aerodynamic/structural values
from assumed or missing values.

## Forbidden Cross-Domain Language

Do not mention AWG, fuse, 24 VDC, conductor, voltage drop, duct velocity, fan
static pressure, purge air, scfm, dewpoint, hydraulic pressure, pump flow, or
bracket stress unless those terms appear in the user problem or supplied
artifacts.
