<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: aerospace_aerodynamics_pack
pack_name: Aerospace Aerodynamics Pack
pack_type: domain
supported_modes: solve-problem, review-design, diagnose-root-cause, suggest-improvements, explore-novel-solution
domain_keywords: aerodynamics, aerodynamic, aircraft aerodynamics, wing lift, aircraft lift, aircraft drag, drag estimation, drag polar, lift coefficient, drag coefficient, stall speed, wing loading, dynamic pressure, aspect ratio, induced drag, parasitic drag, Reynolds number, Mach number, airfoil, airfoil screening, CLmax, L/D ratio, lift-to-drag, UAV aerodynamics, aerodynamic efficiency, aerodynamic release, cruise drag

## Scope

Preliminary aerospace aerodynamic screening, including bounded lift and drag
estimation, supplied dynamic-pressure calculations, wing loading checks, required
lift-coefficient checks, stall-speed requirement screening when the needed data
or converted values are supplied, drag-polar calculations, Reynolds/Mach regime
screening, and preliminary flight-configuration assessment for supplied
candidate configurations.

## Out Of Scope

Certification claims, airworthiness approval, safety-of-flight approval, detailed
CFD, detailed wind-tunnel validation, flight-test signoff, flight controls
certification, flutter or aeroelastic approval, propeller/rotor/downwash modeling
without supplied data, hazardous operational instructions, weapons guidance or
targeting, and regulatory compliance determinations unless the source documents
provide explicit criteria.

## Expected Document Roles

- aerodynamic requirements or acceptance criteria
- wing/reference area and geometry
- weight or required lift basis
- supplied dynamic pressure or validated speed/density conversion basis
- lift and drag coefficient data
- CLmax or stall criterion
- zero-lift drag coefficient, aspect ratio, and Oswald efficiency factor
- Reynolds or Mach validity range
- airfoil data or empirical method source
- thrust/drag limit or allowable drag criterion
- mission speed or configuration condition

## Canonical Units

- force: lbf, N
- dynamic pressure and wing loading: psf or lbf/ft^2 when supported; Pa only when current MCM unit support validates it
- area: ft^2, m^2
- speed: ft/s or m/s when supported; mph and knots only when explicitly converted before MCM
- density: slug/ft^3 or kg/m^3 only when the current unit algebra supports the exact expression
- coefficients, aspect ratio, Reynolds number, Mach number, L/D ratio: dimensionless
- span and chord: ft, m

Do not silently coerce knots, mph, slug/ft^3, or kg/m^3. If density-times-speed
dynamic-pressure algebra is not supported for a case, use a source-supplied or
explicitly converted dynamic_pressure_psf value and state that limitation.

## Safe Equation Patterns

- wing_loading_psf = weight_lbf / wing_area_ft2
- required_lift_coefficient = weight_lbf / (dynamic_pressure_psf * wing_area_ft2)
- available_lift_lbf = dynamic_pressure_psf * wing_area_ft2 * max_lift_coefficient
- predicted_drag_lbf = dynamic_pressure_psf * wing_area_ft2 * drag_coefficient
- lift_to_drag_ratio = lift_coefficient / drag_coefficient
- aspect_ratio = wingspan_ft ** 2 / wing_area_ft2
- induced_drag_coefficient = lift_coefficient ** 2 / (PI_VALUE * oswald_efficiency * aspect_ratio)
- total_drag_coefficient = zero_lift_drag_coefficient + induced_drag_coefficient
- drag_margin_lbf = allowable_drag_lbf - predicted_drag_lbf
- lift_margin_lbf = available_lift_lbf - weight_lbf
- stall_margin_ft_per_s = cruise_speed_ft_per_s - stall_speed_ft_per_s when stall speed is supplied or validly computed
- cl_margin = max_lift_coefficient - required_lift_coefficient
- reynolds_number = velocity * chord / kinematic_viscosity only when units are supported
- mach_number = velocity / speed_of_sound when both values use compatible speed units
- criterion_pass = available_value >= required_value
- criterion_pass = candidate_value <= max_allowed_value

Use supplied dynamic pressure when exact density * velocity ** 2 unit algebra is
unsupported. Do not invent CLmax, CD0, Oswald efficiency, airfoil validity
ranges, or thrust limits.

## Constraint Patterns

Use C1-C5 style checks when the source evidence supports them:

- C1: available lift >= required lift or weight
- C2: required CL <= CLmax with margin
- C3: stall speed <= allowable stall speed, or equivalent CL-at-allowable-stall check passes
- C4: predicted drag <= allowable drag or available thrust
- C5: Mach/Reynolds regime remains within supplied data validity range

Deterministic aerodynamic failure is still a computed result. Do not return
needs_human_review only because lift, CL, stall, drag, or regime criteria fail.

## Aerodynamic Reasoning Patterns

- insufficient lift: available lift is below weight at the supplied condition
- excessive required CL: required lift coefficient exceeds CLmax or supplied limit
- stall risk: stall speed exceeds allowable speed or CL requirement at allowable stall speed exceeds CLmax
- excessive drag: predicted drag exceeds available thrust or allowable drag
- poor L/D: lift-to-drag ratio falls below supplied target
- induced-drag dominance: high CL or low aspect ratio drives total CD
- parasitic-drag dominance: CD0 dominates at high-speed/low-CL conditions
- aspect-ratio effect: lower aspect ratio increases induced drag for the same CL
- missing CLmax prevents deterministic stall certification
- missing CD0, aspect ratio, or Oswald factor prevents drag-polar calculation
- Reynolds or Mach outside source-data range requires limitation or human review

## Common Failure Modes

Mixing mass and force, using mph or knots without explicit conversion, treating
generic airfoil data as validated configuration data, inventing coefficient
values, applying airfoil data outside Reynolds/Mach range, claiming flight
safety from screening arithmetic, double-counting induced drag, and ignoring
configuration differences such as flaps, landing gear, stores, or propeller
slipstream when those effects matter.

## MCM Routing Guidance

Use deterministic MCM for bounded coefficient calculations, supplied
dynamic-pressure lift/drag estimates, wing loading, aspect ratio, drag polar
terms, lift/drag ratio, margins, pass/fail criteria, and candidate screening
when all required source values are present. Keep density-derived dynamic
pressure, stall-speed derivation, Reynolds number, Mach corrections, CFD,
wind-tunnel, transonic, post-stall, and certification claims partial unless the
source evidence provides validated inputs and the unit algebra is supported.

## Human-Review Triggers

Crewed aircraft certification; flight-critical design release; FAA, EASA, or
military certification claims; stability and control conclusions without
stability derivatives; flutter, aeroelasticity, or structural coupling;
transonic, supersonic, or hypersonic flow; high angle-of-attack nonlinear flow;
separated flow or post-stall behavior; propeller, rotor, or downwash
interactions without data; icing, rain, contamination, or roughness effects;
missing compressibility correction where required; CFD without mesh, turbulence
model, boundary conditions, validation, and convergence data; wind tunnel claims
without setup and scaling details; Reynolds number outside provided data range;
missing air density, velocity, wing area, CL/CD data, or weight; unsupported
units or unresolved conversions; and safety-critical UAV/drone operation over
people or property.

## Reporting Guidance

Use phrases such as "Assumptions and calculation basis", "Aerodynamic release
checks", "Lift/drag screening", "Regime validity", and "Human-review triggers".
Report computed aerodynamic values, source-supplied coefficients, validity
limits, failed criteria, recommended corrective actions, and verification steps.
Clearly label results as preliminary aerodynamic screening and do not claim
certification, airworthiness, or safety of flight.

## Evidence-Basis Guidance

Tie conclusions to uploaded aerodynamic requirements, geometry, source-supplied
coefficients, airfoil or empirical data, dynamic-pressure basis, MCM-computed
margins, checked criteria, assumptions, and missing information. Distinguish
source-provided aerodynamic values from inferred causes or recommended changes.

## Forbidden Cross-Domain Language

Do not mention AWG, fuse, 24 VDC, conductor, voltage drop, duct velocity, fan
static pressure, purge air, scfm, dewpoint, pump head, NPSH, gpm, bracket
stress, enclosure cooling, BTU/hr, stack traces, or API routes unless those
terms appear in the user problem or supplied artifacts.
