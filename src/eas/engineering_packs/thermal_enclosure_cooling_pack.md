<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: thermal_enclosure_cooling_pack
pack_name: Thermal Enclosure Cooling Pack
pack_type: domain
supported_modes: solve-problem, review-design, diagnose-root-cause, suggest-improvements, explore-novel-solution
domain_keywords: enclosure cooling, control cabinet cooling, cabinet overheating, overheating cabinet, thermal enclosure, cabinet thermal, heat load, temperature rise, internal temperature, cabinet fan, fan sizing, filter fan, enclosure fan, cooling capacity, BTU/hr, BTUh, derated airflow, component derating, thermal derating, VFD heat load, PLC cabinet thermal, NEMA enclosure cooling, sealed enclosure cooling, enclosure ventilation, air conditioner cooling capacity, heat exchanger cooling capacity, ambient temperature screening, solar load

## Scope

Preliminary thermal enclosure and control-cabinet cooling analysis, including
component heat-load estimation, cabinet fan or filter-fan airflow screening,
temperature-rise checks, internal cabinet temperature prediction, heat
exchanger or air-conditioner cooling capacity checks, sealed enclosure thermal
screening, component derating review, ambient-temperature screening, supported
solar-load screening, and overheating cabinet diagnostics.

## Out Of Scope

UL/NEMA/IP or code certification, hazardous-location certification, explosive
or flammable atmospheres, safety-critical shutdown design, detailed CFD,
transient thermal modeling, detailed conduction modeling, electronics
reliability/lifetime prediction beyond simple temperature screening, and
outdoor solar-load conclusions without supplied environmental data.

## Expected Document Roles

- component heat-load schedule or power-dissipation list
- enclosure drawing, volume, surface area, or ventilation layout
- ambient temperature requirement or field observation
- maximum internal cabinet temperature limit
- component maximum temperature or derating limit
- fan, filter fan, heat exchanger, or air-conditioner datasheet
- fan/filter derating basis or dirty-filter observation
- cooling-capacity or airflow requirement
- NEMA/IP/UL/environmental constraints when supplied
- thermal trend log, alarm history, or overheating observation

## Canonical Units

- heat load and cooling capacity: W, kW, BTU/hr
- airflow: cfm; m^3/hr only when current MCM unit support validates it
- temperature: C or F for source values; prefer explicit delta_t_F, delta_t_C, temperature_rise_F, or temperature_rise_C variables for differences
- enclosure surface area: ft^2, m^2
- conductance or UA: W/C when supplied and supported
- thermal resistance: C/W when supplied and supported
- fan/filter/temperature derating factors: dimensionless
- component power dissipation: W

If absolute degF/degC arithmetic is uncertain, use explicit temperature
difference variables such as allowable_delta_t_F, predicted_delta_t_F,
ambient_temp_F, and max_internal_temp_F. Do not silently coerce unsupported
temperature units.

## Safe Equation Patterns

- total_heat_load_W = component_1_heat_load_W + component_2_heat_load_W
- total_heat_load_BTU_hr = total_heat_load_W * 3.412 when explicit W-to-BTU/hr conversion is intended and unit validation supports it
- allowable_delta_t_F = max_internal_temp_F - ambient_temp_F
- required_airflow_CFM = heat_load_BTU_hr / (1.08 * allowable_delta_t_F)
- predicted_delta_t_F = heat_load_BTU_hr / (1.08 * available_airflow_CFM)
- derated_airflow_CFM = fan_airflow_CFM * filter_derating_factor * temperature_derating_factor
- cooling_margin_BTU_hr = cooling_capacity_BTU_hr - heat_load_BTU_hr
- cooling_margin_W = cooling_capacity_W - total_heat_load_W
- cooling_utilization = total_heat_load_W / cooling_capacity_W
- predicted_internal_temp_F = ambient_temp_F + predicted_delta_t_F
- thermal_margin_F = max_internal_temp_F - predicted_internal_temp_F
- passive_heat_rejection_W = UA_W_per_C * delta_t_C only when UA and delta_t are supplied
- required_cooling_capacity_W = heat_load_W * safety_factor when a design safety factor is specified
- criterion_pass = actual_value <= allowable_value
- criterion_pass = available_value >= required_value

If component maximum operating temperature is supplied, compare predicted
internal temperature to the component limit. If derating curves are supplied,
use only the provided derating points or request human review; do not invent
curve values.

## Constraint Patterns

Use C1-C5 style checks when the evidence supports them:

- C1: total heat load <= cooling capacity
- C2: required airflow <= derated available airflow
- C3: predicted internal temperature <= maximum allowable internal temperature
- C4: thermal margin >= required margin
- C5: component operating temperature or derating limits are not exceeded

Deterministic thermal-release failure is still a computed result. Do not return
needs_human_review only because heat load, airflow, cooling capacity, or
temperature-margin criteria fail.

## Diagnostic Logic Patterns

- insufficient fan airflow: required airflow exceeds derated available airflow
- clogged or dirty filter: dirty-filter derating predicts overheating while clean-filter prediction meets the limit
- excessive component heat load: total heat load exceeds cooling capacity or dominates predicted temperature rise
- ambient temperature too high: allowable delta-T becomes too small for the available cooling method
- undersized cooling device: cooling capacity margin is negative at supplied heat load
- sealed enclosure limitation: no adequate heat exchanger, air conditioner, or UA basis is supplied
- VFD, drive, power supply, or transformer heat load dominates when source heat-load data supports it
- solar or outdoor installation risk: use only supplied solar/environmental data
- fan failure, reversed airflow, blocked intake, or blocked exhaust path: diagnose only when field evidence supports it
- installation environment issue: distinguish high ambient or blocked airflow from component defect when evidence supports it
- electrical load is not automatically heat load: use only dissipated power inside the enclosure

## Common Failure Modes

Treating nameplate electrical load as cabinet heat dissipation, ignoring fan or
filter derating, using nominal fan flow after filter clogging, mixing absolute
temperature and temperature-rise values, claiming NEMA/IP/UL compliance from
thermal arithmetic, ignoring high ambient, double-counting heat loads, and
inventing derating curve values.

## MCM Routing Guidance

Use deterministic MCM for bounded heat-load sums, W-to-BTU/hr conversion when
explicit, sensible-airflow temperature-rise checks, derated fan airflow,
cooling-capacity margin, predicted internal temperature, thermal margin,
component-limit checks, and pass/fail criteria when source values are present.
Keep hazardous-location, certification, derating-curve interpolation,
condensation, solar, transient, CFD, or reliability conclusions partial unless
the supplied evidence provides the method and required inputs.

## Human-Review Triggers

Hazardous locations; explosive atmospheres; flammable vapors or dusts; UL,
NEMA, IP, or safety certification implications; outdoor solar loading without
solar/environment data; sealed washdown, food-grade, or pharma enclosures;
corrosive environments; condensation or dew point risk; high-altitude cooling
derating without correction data; electronics reliability/lifetime prediction;
missing heat-load data; missing ambient temperature; missing max internal or
component temperature limit; missing cooling-device capacity; missing fan/filter
derating information when filter loading is central; unsupported temperature
units; CFD, transient thermal analysis, or detailed conduction modeling claims
without model details; and code-governed safety certification where the
applicable standard is unknown.

## Reporting Guidance

Use phrases such as "Assumptions and calculation basis", "Thermal release
checks", "Cooling capacity margin", and "Human-review triggers". Report
computed heat load, required and available cooling or airflow, temperature
assumptions, predicted internal temperature, failed criteria, recommended
corrective actions, and validation steps. Do not expose raw internal JSON,
model names, or governance objects.

## Evidence-Basis Guidance

Tie conclusions to component heat-load schedules, cabinet drawings, ambient and
internal temperature limits, fan/filter/cooling-device datasheets, derating
factors, field observations, MCM-computed margins, checked criteria,
assumptions, and missing information. Separate computed values from source
assumptions and human-review triggers.

## Forbidden Cross-Domain Language

Do not mention AWG, fuse, voltage drop, duct velocity, fan static pressure,
purge scfm, dewpoint, pump head, NPSH, gpm, bracket stress, lift coefficient,
thrust-to-weight, stall speed, stack traces, or API routes unless those terms
appear in the user problem or supplied artifacts.
