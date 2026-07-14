<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: structural_mechanical_bracket_pack
pack_name: Structural Mechanical Bracket Pack
pack_type: domain
supported_modes: solve-problem, review-design, diagnose-root-cause, suggest-improvements, explore-novel-solution
domain_keywords: bracket, bracket release, bracket design, cantilever bracket, wall bracket, mounting plate, equipment support bracket, support bracket, support arm, gusset, gusseted bracket, bolted plate, welded bracket, load-bearing bracket, fixture mount, mechanical support, support plate, cantilever support, static force, bending moment, bending stress, shear stress, bearing stress, fastener load, fastener shear, bolt shear, bolt bearing, section modulus, moment of inertia, tip deflection, deflection limit

## Scope

Preliminary structural/mechanical bracket and support screening, including
cantilever brackets, wall brackets, mounting plates, equipment support brackets,
gusseted brackets, tabs, lugs, clevis-style simple supports, bolted brackets,
load-bearing arms, support plates, fixture mounts, static load-path checks,
stress checks, fastener load checks, and deflection screening.

Use welded-bracket guidance only for screening unless weld size, weld length,
material, filler/electrode basis, loading, and code/method criteria are supplied.

## Out Of Scope

Certified structural approval, life-safety supports, lifting or suspended loads
over people, seismic/crash/blast/impact qualification, fatigue or vibration
qualification, pressure-vessel attachments, aircraft/vehicle/medical or other
regulated safety-critical release, detailed finite element analysis, nonlinear
contact/prying analysis, and code-governed design without an explicit source
criterion.

## Expected Document Roles

- load requirement with magnitude, direction, and load case
- bracket geometry, moment arm, plate thickness, section modulus, or I/c
- material grade and allowable stress
- deflection limit or stiffness requirement
- fastener grade, count, diameter, layout, and allowable shear/tension/bearing
- weld size, length, material, and method basis when welds are in scope
- gusset geometry or load-path sketch when gussets are credited
- required factor of safety, utilization, or margin criteria
- notes identifying dynamic, fatigue, vibration, impact, seismic, or code constraints

## Canonical Units

- force/load: lbf or N when supported; use lbf for current US-customary bracket checks
- moment: lbf_in, lb_in, lbf*ft, lb*ft, or N*m when supported
- length: in, ft, mm, or m when conversion paths are explicit and unit-valid
- area: in^2, ft^2, mm^2, or m^2 when supported
- stress/modulus: psi, ksi, Pa, or MPa when supported; prefer psi for in/lbf equations
- section properties: in^3 and in^4 for US-customary section modulus and inertia
- deflection: in or mm when supported
- factor of safety, utilization ratio, count, and margin ratio: dimensionless

If a requested unit is unsupported by MCM, keep the item partial or require
human review rather than silently coercing it.

## Safe Equation Patterns

- applied_moment_lbf_in = load_lbf * moment_arm_in
- bending_stress_psi = moment_lbf_in / section_modulus_in3
- bending_stress_psi = moment_lbf_in * c_in / moment_of_inertia_in4
- shear_stress_psi = shear_force_lbf / shear_area_in2
- bearing_area_in2 = plate_thickness_in * bolt_diameter_in * bolt_count
- bearing_stress_psi = load_lbf / bearing_area_in2
- fastener_shear_per_bolt_lbf = total_shear_lbf / bolt_count
- fastener_tension_per_bolt_lbf = total_tension_lbf / bolt_count
- tip_deflection_in = load_lbf * length_in ** 3 / (3.0 * elastic_modulus_psi * moment_of_inertia_in4)
- utilization_ratio = actual_stress_psi / allowable_stress_psi
- factor_of_safety = allowable_stress_psi / actual_stress_psi
- margin = allowable_value - actual_value
- criterion_pass = actual_value <= allowable_value
- criterion_pass = factor_of_safety >= required_factor_of_safety

Calculate bending and shear separately when both are supplied. Do not invent
von Mises, prying, weld-group, bolt-group, fatigue, or interaction equations
unless the source documents provide the method.

## Constraint Patterns

Use C1-C5 style checks when the evidence supports them:

- C1: bending stress <= allowable bending stress
- C2: shear stress <= allowable shear stress
- C3: tip deflection <= allowable deflection
- C4: fastener shear, tension, or bearing <= allowable values
- C5: factor of safety >= required factor of safety

Deterministic engineering failure is still a computed result. Do not return
needs_human_review only because a stress, deflection, fastener, or FOS criterion
fails.

## Diagnostic Logic Patterns

- bending overstress: applied moment and section modulus/I-c evidence produce stress above the supplied allowable
- excessive deflection: calculated tip deflection exceeds the supplied limit even if stress passes
- insufficient section modulus or plate thickness: utilization improves directly with larger section property or thickness
- bolt shear overload: per-bolt shear exceeds supplied allowable
- bearing overload: load divided by plate-thickness and bolt-diameter bearing area exceeds supplied bearing allowable
- inadequate factor of safety: supplied allowable-to-actual ratio is below the required FOS
- unclear load path: load direction, support reactions, eccentricity, or bracket restraint is not defined
- eccentric loading: include moment amplification only when eccentricity geometry is supplied
- missing gusset geometry: do not credit gusset strength without supplied dimensions and load path
- base-plate prying risk: flag human review when geometry is incomplete or prying method is absent
- weld adequacy: screening only unless weld dimensions, material, and acceptance method are supplied
- fatigue/dynamic/vibration cases: human review unless simplified static screening is explicitly requested

## Common Failure Modes

Using unsupported or mixed units, confusing lb mass with lbf, comparing moment
to stress, omitting eccentric moment, using gross plate area where net or
bearing area is required, crediting welds or gussets without details, treating a
failed criterion as an MCM execution failure, and claiming code/certification
acceptance from simplified static equations.

## MCM Routing Guidance

Use deterministic MCM for bounded static loads, moment, bending stress, shear
stress, bearing stress, fastener load, deflection, utilization, factor of
safety, margin, and pass/fail checks when the supplied evidence defines the
load case, geometry, material allowable, and acceptance criteria. Keep combined
loading, weld qualification, prying, buckling, fatigue, vibration, dynamic,
regulated, or FEA conclusions partial unless the source documents provide the
method and all required inputs.

## Human-Review Triggers

Life-safety structural supports; lifting, hoisting, rigging, fall protection,
cranes, elevators, or suspended loads over people; seismic, crash, blast,
impact, or dynamic loading; fatigue-critical, vibration-critical, cyclic, or
resonance-sensitive brackets; pressure boundary or pressure vessel attachments;
aircraft, vehicle, medical, or regulated safety-critical structures; missing
material grade or allowable stress; missing load magnitude or direction;
missing bracket geometry; missing fastener grade, count, diameter, or layout;
missing weld size, length, or specification; buckling-prone slender members
without a buckling method; nonlinear/contact/prying action not captured by
simplified equations; unknown code basis; unsupported units or invalid MCM unit
algebra; and finite-element-analysis claims without model details, boundary
conditions, mesh quality, and validation basis.

## Reporting Guidance

Report that the assessment is preliminary/static screening unless source
documents provide a stronger basis. Include load case, geometry basis, material
allowable, computed moment/stress/deflection/fastener values, pass/fail
criteria, factor of safety or utilization, failed criteria, assumptions,
human-review triggers, and practical corrective actions such as increasing
section modulus, shortening moment arm, adding verified gusset geometry,
increasing plate thickness, or revising fastener pattern when supported.

## Evidence-Basis Guidance

Tie conclusions to uploaded load requirements, bracket drawings, material
allowables, fastener data, weld details, MCM-computed stresses/deflections,
checked criteria, assumptions, and missing information. Separate computed
values from source assumptions and from items requiring licensed engineering
review.

## Forbidden Cross-Domain Language

Do not mention duct velocity, fan static pressure, cfm, fpm, purge air, scfm,
dewpoint, AWG, fuse, 24 VDC, conductor, voltage drop, pump curve, NPSH, gpm,
airworthy, certified, or safe for flight unless those terms appear in the user
problem or supplied artifacts.
