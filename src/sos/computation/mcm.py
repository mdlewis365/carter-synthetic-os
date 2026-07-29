# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""
Synthetic OS MCM - Math Computation Module
Author: Michael D. Lewis
May 5, 2026
"""

import ast
import copy
import difflib
import keyword
import logging
import math
import operator
import re
from decimal import Decimal

logger = logging.getLogger(__name__)

SUPPORTED_OPERATIONS = {
    "add": sum,
    "sum": sum,
    "multiply": math.prod,
    "product": math.prod,
    "min": min,
    "max": max,
}

FORMULA_ALIASES = {
    "thermal": "thermal_energy_cooldown",
    "thermal_energy": "thermal_energy_cooldown",
    "thermal_energy_cooldown": "thermal_energy_cooldown",
    "cooldown": "thermal_energy_cooldown",
    "chiller_cooldown": "thermal_energy_cooldown",
    "cooling_time": "power_energy_time",
    "energy_power_time": "power_energy_time",
    "power_energy_time": "power_energy_time",
    "constraint_check": "requirement_check",
    "pass_fail": "requirement_check",
    "requirement": "requirement_check",
    "requirement_check": "requirement_check",
    "ohm": "ohms_law",
    "ohms": "ohms_law",
    "ohms_law": "ohms_law",
    "power": "electrical_power",
    "electrical_power": "electrical_power",
    "fos": "factor_of_safety",
    "safety_factor_check": "factor_of_safety",
    "factor_of_safety": "factor_of_safety",
}

ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

ALLOWED_COMPAREOPS = {
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}

ALLOWED_COMPARATOR_SYMBOLS = {
    "<": ast.Lt,
    "<=": ast.LtE,
    ">": ast.Gt,
    ">=": ast.GtE,
    "==": ast.Eq,
    "!=": ast.NotEq,
}


def _safe_boolean_int(value):
    if isinstance(value, bool):
        return 1 if value else 0
    raise ValueError("int() only supports boolean operands in MCM expressions")


def _safe_numeric_max(*args):
    return max(_safe_numeric_extreme_values("max", args))


def _safe_numeric_min(*args):
    return min(_safe_numeric_extreme_values("min", args))


def _safe_numeric_max_ignore_null(values):
    if not isinstance(values, (list, tuple)):
        raise ValueError("max_ignore_null() expects a list argument")
    numeric_values = []
    for value in values:
        if is_missing_value(value):
            continue
        if not _is_number(value):
            raise ValueError("max_ignore_null() only supports numeric or null operands")
        numeric_values.append(value)
    if not numeric_values:
        return None
    return max(numeric_values)


def _safe_numeric_extreme_values(function_name, args):
    values = list(args[0]) if len(args) == 1 and isinstance(args[0], (list, tuple)) else list(args)
    if not values:
        raise ValueError(f"{function_name}() requires at least one numeric operand")
    for value in values:
        if not _is_number(value):
            raise ValueError(f"{function_name}() only supports numeric operands")
    return values


def _count_true(values):
    return _count_boolean_values(values, True, ignore_null=False)


def _count_false(values):
    return _count_boolean_values(values, False, ignore_null=False)


def _count_true_ignore_null(values):
    return _count_boolean_values(values, True, ignore_null=True)


def _count_false_ignore_null(values):
    return _count_boolean_values(values, False, ignore_null=True)


def _count_boolean_values(values, target, ignore_null=False):
    if not isinstance(values, (list, tuple)):
        raise ValueError("boolean count helpers expect a list argument")
    count = 0
    for value in values:
        if is_missing_value(value):
            if ignore_null:
                continue
            raise ValueError("boolean count helpers cannot count null values")
        if not isinstance(value, bool):
            raise ValueError("boolean count helpers only accept boolean values")
        if value is target:
            count += 1
    return count


ALLOWED_FUNCTIONS = {
    "abs": abs,
    "max": _safe_numeric_max,
    "min": _safe_numeric_min,
    "max_ignore_null": _safe_numeric_max_ignore_null,
    "round": round,
    "int": _safe_boolean_int,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "count_true": _count_true,
    "count_false": _count_false,
    "count_true_ignore_null": _count_true_ignore_null,
    "count_false_ignore_null": _count_false_ignore_null,
}

MAX_EXPRESSION_LENGTH = 2000
MAX_EXPRESSION_AST_NODES = 512
MAX_EXPRESSION_AST_DEPTH = 64
MAX_EVALUATED_SEQUENCE_LENGTH = 10000
MAX_EVALUATED_CONTAINER_ITEMS = 10000
MAX_EVALUATED_INTEGER_BITS = 4096
MAX_ABS_EXPONENT = 1024

UNIT_ALIASES = {
    "": "dimensionless",
    "dimensionless": "dimensionless",
    "none": "dimensionless",
    "null": "dimensionless",
    "unitless": "dimensionless",
    "scalar": "dimensionless",
    "1": "dimensionless",
    "fraction": "dimensionless",
    "ratio": "dimensionless",
    "factor": "dimensionless",
    "count": "dimensionless",
    "qty": "dimensionless",
    "quantity": "dimensionless",
    "unit": "dimensionless",
    "units": "dimensionless",
    "counts": "dimensionless",
    "boolean": "boolean",
    "bool": "boolean",
    "degc_abs": "C",
    "c_abs": "C",
    "absolute_degc": "C",
    "absolute_c": "C",
    "degf_abs": "F",
    "f_abs": "F",
    "absolute_degf": "F",
    "absolute_f": "F",
    "k_abs": "K_abs",
    "kelvin_abs": "K_abs",
    "absolute_k": "K_abs",
    "absolute_kelvin": "K_abs",
    "delta_c": "delta_C",
    "delta c": "delta_C",
    "delta_degc": "delta_C",
    "delta degc": "delta_C",
    "delta_deg_c": "delta_C",
    "delta deg c": "delta_C",
    "deltac": "delta_C",
    "delta_t_c": "delta_C",
    "delta t c": "delta_C",
    "delta_t_degc": "delta_C",
    "delta t degc": "delta_C",
    "deltat_c": "delta_C",
    "deltatc": "delta_C",
    "degc_delta": "delta_C",
    "c_delta": "C_delta",
    "c delta": "C_delta",
    "delta_k": "K_delta",
    "delta k": "K_delta",
    "delta_kelvin": "K_delta",
    "k_delta": "K_delta",
    "delta_f": "delta_F",
    "delta f": "delta_F",
    "delta_degf": "delta_F",
    "delta degf": "delta_F",
    "delta_deg_f": "delta_F",
    "delta deg f": "delta_F",
    "deltaf": "delta_F",
    "deltat_f": "delta_F",
    "delta_t_f": "delta_F",
    "delta t f": "delta_F",
    "delta_t_degf": "delta_F",
    "delta t degf": "delta_F",
    "delta_fahrenheit": "delta_F",
    "degf_delta": "delta_F",
    "f_delta": "F_delta",
    "f delta": "F_delta",
    "percent": "percent",
    "%": "percent",
    "percent/dimensionless": "percent",
    "%/dimensionless": "percent",
    "pct": "percent",
    "status": "status_string",
    "status_string": "status_string",
    "status string": "status_string",
    "string": "status_string",
    "str": "status_string",
    "label": "status_string",
    "text": "status_string",
    "name": "status_string",
    "label_string": "label_string",
    "label string": "label_string",
    "unit_expression": "unit_expression",
    "unit expression": "unit_expression",
    "pass_fail_unknown": "status_string",
    "pass fail unknown": "status_string",
    "PASS_FAIL_UNKNOWN".lower(): "status_string",
    "c": "C",
    "degc": "C",
    "degreec": "C",
    "degree c": "C",
    "degrees c": "C",
    "degrees_c": "C",
    "celsius": "C",
    "degree celsius": "C",
    "degrees celsius": "C",
    "°c": "C",
    "kg": "kg",
    "kg/m2": "kg/m^2",
    "kg/m^2": "kg/m^2",
    "kg_per_m2": "kg/m^2",
    "kg_per_m_2": "kg/m^2",
    "kg_per_sq_m": "kg/m^2",
    "kg_per_square_m": "kg/m^2",
    "kg_per_square_meter": "kg/m^2",
    "kg_per_square_meters": "kg/m^2",
    "kg_per_square_metre": "kg/m^2",
    "kg_per_square_metres": "kg/m^2",
    "kg/m3": "kg/m^3",
    "kg/m^3": "kg/m^3",
    "kg_per_m3": "kg/m^3",
    "kg_per_m_3": "kg/m^3",
    "kg_per_cubic_m": "kg/m^3",
    "kg_per_cubic_meter": "kg/m^3",
    "kg_per_cubic_metre": "kg/m^3",
    "kilogram_per_cubic_meter": "kg/m^3",
    "kilograms_per_cubic_meter": "kg/m^3",
    "kilogram_per_cubic_metre": "kg/m^3",
    "kilograms_per_cubic_metre": "kg/m^3",
    "kw": "kW",
    "kwh": "kWh",
    "wh": "Wh",
    "w h": "Wh",
    "watt-hour": "Wh",
    "watt-hours": "Wh",
    "watt_hour": "Wh",
    "watt_hours": "Wh",
    "kj": "kJ",
    "j": "J",
    "joule": "J",
    "joules": "J",
    "v": "V",
    "vdc": "V",
    "v dc": "V",
    "dcv": "V",
    "volt": "V",
    "volts": "V",
    "a": "A",
    "amp": "A",
    "amps": "A",
    "ampere": "A",
    "amperes": "A",
    "ah": "Ah",
    "a h": "Ah",
    "amp-hour": "Ah",
    "amp-hours": "Ah",
    "ampere-hour": "Ah",
    "ampere-hours": "Ah",
    "w": "W",
    "watt": "W",
    "watts": "W",
    "w/kg": "W/kg",
    "w_per_kg": "W/kg",
    "watt_per_kg": "W/kg",
    "watts_per_kg": "W/kg",
    "wh/kg": "Wh/kg",
    "wh_per_kg": "Wh/kg",
    "watt_hour_per_kg": "Wh/kg",
    "watt_hours_per_kg": "Wh/kg",
    "ohm": "ohm",
    "ohms": "ohm",
    "h": "h",
    "hr": "h",
    "hrs": "h",
    "hour": "h",
    "hours": "h",
    "s": "s",
    "sec": "s",
    "second": "s",
    "seconds": "s",
    "min": "min",
    "minute": "min",
    "minutes": "min",
    "l": "L",
    "liter": "L",
    "liters": "L",
    "litre": "L",
    "litres": "L",
    "m3": "m^3",
    "m^3": "m^3",
    "m2": "m^2",
    "m^2": "m^2",
    "m_2": "m^2",
    "sq_m": "m^2",
    "sqm": "m^2",
    "square_m": "m^2",
    "square_meter": "m^2",
    "square_meters": "m^2",
    "square_metre": "m^2",
    "square_metres": "m^2",
    "m": "m",
    "m/s": "m/s",
    "m_per_s": "m/s",
    "m/sec": "m/s",
    "m_per_sec": "m/s",
    "m/second": "m/s",
    "m_per_second": "m/s",
    "meter/s": "m/s",
    "meters/s": "m/s",
    "meter_per_second": "m/s",
    "meters_per_second": "m/s",
    "in": "in",
    "inch": "in",
    "inches": "in",
    "in2": "in^2",
    "in^2": "in^2",
    "in_2": "in^2",
    "in**2": "in^2",
    "inch2": "in^2",
    "inch^2": "in^2",
    "inch_2": "in^2",
    "inch**2": "in^2",
    "inches2": "in^2",
    "inches^2": "in^2",
    "inches_2": "in^2",
    "inches**2": "in^2",
    "sqin": "in^2",
    "sq_in": "in^2",
    "square_in": "in^2",
    "squareinch": "in^2",
    "squareinches": "in^2",
    "square_inch": "in^2",
    "square_inches": "in^2",
    "square inch": "in^2",
    "square inches": "in^2",
    "in3": "in^3",
    "in^3": "in^3",
    "in_3": "in^3",
    "in**3": "in^3",
    "cuin": "in^3",
    "cu_in": "in^3",
    "cu in": "in^3",
    "cubic_in": "in^3",
    "cubic inch": "in^3",
    "cubic inches": "in^3",
    "in3/gal": "in^3/gal",
    "in^3/gal": "in^3/gal",
    "in_3/gal": "in^3/gal",
    "in**3/gal": "in^3/gal",
    "cuin/gal": "in^3/gal",
    "cu_in/gal": "in^3/gal",
    "cu in/gal": "in^3/gal",
    "cubic_in/gal": "in^3/gal",
    "cubic inch/gal": "in^3/gal",
    "cubic inches/gal": "in^3/gal",
    "in3_per_gal": "in^3/gal",
    "in3 per gal": "in^3/gal",
    "in^3_per_gal": "in^3/gal",
    "in^3 per gal": "in^3/gal",
    "in_3_per_gal": "in^3/gal",
    "in**3_per_gal": "in^3/gal",
    "cuin_per_gal": "in^3/gal",
    "cu_in_per_gal": "in^3/gal",
    "cu in per gal": "in^3/gal",
    "cubic_in_per_gal": "in^3/gal",
    "cubic_inches_per_gal": "in^3/gal",
    "cubic inch per gal": "in^3/gal",
    "cubic inches per gal": "in^3/gal",
    "in3/gallon": "in^3/gal",
    "in^3/gallon": "in^3/gal",
    "cu in/gallon": "in^3/gal",
    "cubic inch/gallon": "in^3/gal",
    "cubic inches/gallon": "in^3/gal",
    "in3_per_gallon": "in^3/gal",
    "in3 per gallon": "in^3/gal",
    "in^3_per_gallon": "in^3/gal",
    "in^3 per gallon": "in^3/gal",
    "cuin_per_gallon": "in^3/gal",
    "cu_in_per_gallon": "in^3/gal",
    "cubic_in_per_gallon": "in^3/gal",
    "cubic_inches_per_gallon": "in^3/gal",
    "cu in per gallon": "in^3/gal",
    "cubic inch per gallon": "in^3/gal",
    "cubic inches per gallon": "in^3/gal",
    "in3/min": "in^3/min",
    "in^3/min": "in^3/min",
    "in_3/min": "in^3/min",
    "in**3/min": "in^3/min",
    "cuin/min": "in^3/min",
    "cu_in/min": "in^3/min",
    "cu in/min": "in^3/min",
    "cubic_in/min": "in^3/min",
    "cubic inch/min": "in^3/min",
    "cubic inches/min": "in^3/min",
    "in3_per_min": "in^3/min",
    "in3 per min": "in^3/min",
    "in^3_per_min": "in^3/min",
    "in^3 per min": "in^3/min",
    "cuin_per_min": "in^3/min",
    "cu_in_per_min": "in^3/min",
    "cu in per min": "in^3/min",
    "cubic_in_per_min": "in^3/min",
    "cubic_inches_per_min": "in^3/min",
    "cubic inch per min": "in^3/min",
    "cubic inches per min": "in^3/min",
    "in3/minute": "in^3/min",
    "in^3/minute": "in^3/min",
    "cu in/minute": "in^3/min",
    "cubic inch/minute": "in^3/min",
    "cubic inches/minute": "in^3/min",
    "in3_per_minute": "in^3/min",
    "in3 per minute": "in^3/min",
    "in^3_per_minute": "in^3/min",
    "in^3 per minute": "in^3/min",
    "cuin_per_minute": "in^3/min",
    "cu_in_per_minute": "in^3/min",
    "cubic_in_per_minute": "in^3/min",
    "cubic_inches_per_minute": "in^3/min",
    "cu in per minute": "in^3/min",
    "cubic inch per minute": "in^3/min",
    "cubic inches per minute": "in^3/min",
    "in/min": "in/min",
    "in_per_min": "in/min",
    "in per min": "in/min",
    "inch_per_min": "in/min",
    "inch per min": "in/min",
    "inches_per_min": "in/min",
    "inches per min": "in/min",
    "in/minute": "in/min",
    "in_per_minute": "in/min",
    "in per minute": "in/min",
    "inch_per_minute": "in/min",
    "inch per minute": "in/min",
    "inches_per_minute": "in/min",
    "inches per minute": "in/min",
    "in4": "in^4",
    "in^4": "in^4",
    "in_4": "in^4",
    "in**4": "in^4",
    "ft": "ft",
    "foot": "ft",
    "feet": "ft",
    "ft_head": "ft_head",
    "head_ft": "ft_head",
    "fthead": "ft_head",
    "headft": "ft_head",
    "ft_water": "ft_head",
    "ftwater": "ft_head",
    "ft_h2o": "ft_head",
    "fth2o": "ft_head",
    "ft h2o": "ft_head",
    "feet_h2o": "ft_head",
    "feet h2o": "ft_head",
    "ft of water": "ft_head",
    "ft_of_water": "ft_head",
    "foot of water": "ft_head",
    "foot_of_water": "ft_head",
    "feet of water": "ft_head",
    "feet_of_water": "ft_head",
    "ft water": "ft_head",
    "feet water": "ft_head",
    "ft_water/head": "ft_head",
    "ftwater/head": "ft_head",
    "ft_h2o/head": "ft_head",
    "fth2o/head": "ft_head",
    "ft2": "ft^2",
    "ft^2": "ft^2",
    "ft_2": "ft^2",
    "ft**2": "ft^2",
    "foot2": "ft^2",
    "foot^2": "ft^2",
    "foot_2": "ft^2",
    "foot**2": "ft^2",
    "feet2": "ft^2",
    "feet^2": "ft^2",
    "feet_2": "ft^2",
    "feet**2": "ft^2",
    "sqft": "ft^2",
    "sq_ft": "ft^2",
    "square_ft": "ft^2",
    "squarefoot": "ft^2",
    "squarefeet": "ft^2",
    "square_foot": "ft^2",
    "square_feet": "ft^2",
    "square foot": "ft^2",
    "square feet": "ft^2",
    "ft3": "ft^3",
    "ft^3": "ft^3",
    "ft_3": "ft^3",
    "ft**3": "ft^3",
    "cubic_ft": "ft^3",
    "cubic foot": "ft^3",
    "cubic feet": "ft^3",
    "cfm": "cfm",
    "ft3_per_min": "cfm",
    "ft3/min": "cfm",
    "ft^3_per_min": "cfm",
    "ft^3/min": "cfm",
    "ft**3_per_min": "cfm",
    "ft**3/min": "cfm",
    "cubic_ft_per_min": "cfm",
    "cubic_feet_per_min": "cfm",
    "cubic_feet_per_minute": "cfm",
    "cfs": "ft^3/s",
    "ft3_per_s": "ft^3/s",
    "ft3/s": "ft^3/s",
    "ft^3_per_s": "ft^3/s",
    "ft^3/s": "ft^3/s",
    "ft**3_per_s": "ft^3/s",
    "ft**3/s": "ft^3/s",
    "ft3_per_sec": "ft^3/s",
    "ft3/sec": "ft^3/s",
    "ft^3_per_sec": "ft^3/s",
    "ft^3/sec": "ft^3/s",
    "ft3_per_second": "ft^3/s",
    "ft3/second": "ft^3/s",
    "ft^3_per_second": "ft^3/s",
    "ft^3/second": "ft^3/s",
    "cubic_ft_per_s": "ft^3/s",
    "cubic_feet_per_s": "ft^3/s",
    "cubic_ft_per_sec": "ft^3/s",
    "cubic_feet_per_sec": "ft^3/s",
    "cubic_ft_per_second": "ft^3/s",
    "cubic_feet_per_second": "ft^3/s",
    "cubic foot per second": "ft^3/s",
    "cubic feet per second": "ft^3/s",
    "cycle": "cycle",
    "cycles": "cycle",
    "cycles_per_min": "cycle/min",
    "cycle_per_min": "cycle/min",
    "cycles/min": "cycle/min",
    "cycle/min": "cycle/min",
    "cycles_per_minute": "cycle/min",
    "cycle_per_minute": "cycle/min",
    "cpm": "cycle/min",
    "scf": "scf",
    "standard_cubic_foot": "scf",
    "standard_cubic_feet": "scf",
    "scf_per_cycle": "scf/cycle",
    "scf/cycle": "scf/cycle",
    "standard_cubic_feet_per_cycle": "scf/cycle",
    "scfm": "scfm",
    "scf_per_min": "scfm",
    "scf/min": "scfm",
    "standard_cubic_feet_per_minute": "scfm",
    "fpm": "fpm",
    "ft_per_min": "fpm",
    "ft/min": "fpm",
    "ft/minute": "fpm",
    "feet/min": "fpm",
    "feet/minute": "fpm",
    "feet_per_min": "fpm",
    "feet_per_minute": "fpm",
    "ft/s": "ft/s",
    "ft/sec": "ft/s",
    "ft/second": "ft/s",
    "ft_per_s": "ft/s",
    "ft_per_sec": "ft/s",
    "ft_per_second": "ft/s",
    "feet/s": "ft/s",
    "feet/sec": "ft/s",
    "feet/second": "ft/s",
    "feet_per_s": "ft/s",
    "feet_per_sec": "ft/s",
    "feet_per_second": "ft/s",
    "fps": "ft/s",
    "in/ft": "in/ft",
    "in_per_ft": "in/ft",
    "inch/ft": "in/ft",
    "inches/ft": "in/ft",
    "in/foot": "in/ft",
    "inch/foot": "in/ft",
    "inches/foot": "in/ft",
    "inch_per_ft": "in/ft",
    "inches_per_ft": "in/ft",
    "inch_per_foot": "in/ft",
    "inches_per_foot": "in/ft",
    "ft/in": "ft/in",
    "ft_per_in": "ft/in",
    "ft_per_inch": "ft/in",
    "ft_per_inches": "ft/in",
    "foot/in": "ft/in",
    "feet/in": "ft/in",
    "ft/inch": "ft/in",
    "ft/inches": "ft/in",
    "ft/foot": "dimensionless",
    "foot_per_in": "ft/in",
    "feet_per_in": "ft/in",
    "foot_per_inch": "ft/in",
    "feet_per_inch": "ft/in",
    "lbf": "lbf",
    "lb_f": "lbf",
    "lbforce": "lbf",
    "poundforce": "lbf",
    "pound-force": "lbf",
    "poundsforce": "lbf",
    "pounds-force": "lbf",
    "psi": "psi",
    "lbf/in2": "psi",
    "lbf/in^2": "psi",
    "lb/in2": "psi",
    "lb/in^2": "psi",
    "lbf_per_in2": "psi",
    "lbf_per_in^2": "psi",
    "psf": "psf",
    "lbf/ft2": "psf",
    "lbf/ft^2": "psf",
    "lbf_per_ft2": "psf",
    "lbf_per_ft^2": "psf",
    "lb/ft2": "psf",
    "lb/ft^2": "psf",
    "lb_per_ft2": "psf",
    "lb_per_ft^2": "psf",
    "pounds_per_square_foot": "psf",
    "pound_force_per_square_foot": "psf",
    "pounds_force_per_square_foot": "psf",
    "inh2o": "inH2O",
    "in_h2o": "inH2O",
    "in_h2_o": "inH2O",
    "inwc": "inH2O",
    "inch_water": "inH2O",
    "inches_water": "inH2O",
    "inch_water_column": "inH2O",
    "inches_water_column": "inH2O",
    "inches of water": "inH2O",
    "inches_of_water": "inH2O",
    "inches water column": "inH2O",
    "inches_of_water_column": "inH2O",
    "lbf_in": "lbf_in",
    "in_lbf": "lbf_in",
    "lb_in": "lbf_in",
    "in_lb": "lbf_in",
    "lbfin": "lbf_in",
    "inlbf": "lbf_in",
    "lbin": "lbf_in",
    "inlb": "lbf_in",
    "lbf-in": "lbf_in",
    "in-lbf": "lbf_in",
    "lb-in": "lbf_in",
    "in-lb": "lbf_in",
    "lbf*in": "lbf_in",
    "in*lbf": "lbf_in",
    "lb*in": "lbf_in",
    "in*lb": "lbf_in",
    "lbf_ft": "lbf*ft",
    "lbft": "lbf*ft",
    "lbfft": "lbf*ft",
    "ft_lbf": "lbf*ft",
    "lb_ft": "lbf*ft",
    "ft_lb": "lbf*ft",
    "lbf-ft": "lbf*ft",
    "ft-lbf": "lbf*ft",
    "lb-ft": "lbf*ft",
    "ft-lb": "lbf*ft",
    "lbf*ft": "lbf*ft",
    "ft*lbf": "lbf*ft",
    "lb*ft": "lbf*ft",
    "ft*lb": "lbf*ft",
    "n": "N",
    "newton": "N",
    "newtons": "N",
    "pa": "Pa",
    "pascal": "Pa",
    "pascals": "Pa",
    "n/m2": "Pa",
    "n/m^2": "Pa",
    "n_per_m2": "Pa",
    "n_per_m_2": "Pa",
    "newton_per_square_meter": "Pa",
    "newtons_per_square_meter": "Pa",
    "n/kg": "N/kg",
    "n_per_kg": "N/kg",
    "newton_per_kg": "N/kg",
    "newtons_per_kg": "N/kg",
    "newton_per_kilogram": "N/kg",
    "newtons_per_kilogram": "N/kg",
    "n_m": "N*m",
    "m_n": "N*m",
    "n-m": "N*m",
    "m-n": "N*m",
    "n*m": "N*m",
    "m*n": "N*m",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "lb/gal": "lb/gal",
    "lbs/gal": "lb/gal",
    "lb/gallon": "lb/gal",
    "lbs/gallon": "lb/gal",
    "lb_per_gal": "lb/gal",
    "lbs_per_gal": "lb/gal",
    "lb per gal": "lb/gal",
    "lbs per gal": "lb/gal",
    "lb_per_gallon": "lb/gal",
    "lbs_per_gallon": "lb/gal",
    "lb per gallon": "lb/gal",
    "lbs per gallon": "lb/gal",
    "lb/min": "lb/min",
    "lbs/min": "lb/min",
    "lb_per_min": "lb/min",
    "lbs_per_min": "lb/min",
    "lb/minute": "lb/min",
    "lbs/minute": "lb/min",
    "lb_per_minute": "lb/min",
    "lbs_per_minute": "lb/min",
    "lb/hr": "lb/hr",
    "lbs/hr": "lb/hr",
    "lb_per_hr": "lb/hr",
    "lbs_per_hr": "lb/hr",
    "lb/hour": "lb/hr",
    "lbs/hour": "lb/hr",
    "lb_per_hour": "lb/hr",
    "lbs_per_hour": "lb/hr",
    "gal": "gal",
    "gallon": "gal",
    "gallons": "gal",
    "gpm": "gpm",
    "gal_per_min": "gpm",
    "gal per min": "gpm",
    "gals_per_min": "gpm",
    "gals per min": "gpm",
    "gal/min": "gpm",
    "gals/min": "gpm",
    "gallon/min": "gpm",
    "gallons/min": "gpm",
    "gal/minute": "gpm",
    "gals/minute": "gpm",
    "gallon/minute": "gpm",
    "gallons/minute": "gpm",
    "gallon_per_min": "gpm",
    "gallon per min": "gpm",
    "gallons_per_min": "gpm",
    "gallons per min": "gpm",
    "gal_per_minute": "gpm",
    "gal per minute": "gpm",
    "gals_per_minute": "gpm",
    "gals per minute": "gpm",
    "gallon_per_minute": "gpm",
    "gallon per minute": "gpm",
    "gallons_per_minute": "gpm",
    "gallons per minute": "gpm",
    "hp": "hp",
    "horsepower": "hp",
    "bhp": "hp",
    "lb-ft*rpm/hp": "lbf*ft*rpm/hp",
    "lbft*rpm/hp": "lbf*ft*rpm/hp",
    "lbf-ft*rpm/hp": "lbf*ft*rpm/hp",
    "lbf_ft*rpm/hp": "lbf*ft*rpm/hp",
    "lbf*ft*rpm/hp": "lbf*ft*rpm/hp",
    "rpm": "rpm",
    "rev/min": "rpm",
    "rev_per_min": "rpm",
    "rev per min": "rpm",
    "revolution/min": "rpm",
    "revolutions/min": "rpm",
    "revolution_per_min": "rpm",
    "revolutions_per_min": "rpm",
    "revolutions per minute": "rpm",
    "rev/minute": "rpm",
    "revs/min": "rpm",
    "revs_per_min": "rpm",
    "r/min": "rpm",
    "sg": "dimensionless",
    "specific_gravity": "dimensionless",
    "fluid_specific_gravity": "dimensionless",
    "efficiency": "dimensionless",
    "ft_head_per_ft": "dimensionless",
    "head_ft_per_ft": "dimensionless",
    "ft_head/ft": "dimensionless",
    "ft/ft": "dimensionless",
    "ft/100ft": "dimensionless",
    "ft_per_100ft": "dimensionless",
    "ft per 100 ft": "dimensionless",
    "ft per 100 feet": "dimensionless",
    "feet per 100 ft": "dimensionless",
    "feet per 100 feet": "dimensionless",
    "ft_head_per_100ft": "dimensionless",
    "head_ft_per_100ft": "dimensionless",
    "ft_head/100ft": "dimensionless",
    "head_ft/100ft": "dimensionless",
    "f": "F",
    "degf": "F",
    "degreef": "F",
    "degree f": "F",
    "degrees f": "F",
    "degrees_f": "F",
    "Â°f": "F",
    "btu": "BTU",
    "btu/hr": "BTU/hr",
    "btuh": "BTU/hr",
    "btu/h": "BTU/hr",
    "btu_per_h": "BTU/hr",
    "btu_per_hr": "BTU/hr",
    "btu per hr": "BTU/hr",
    "btu_per_hour": "BTU/hr",
    "btu/hour": "BTU/hr",
    "btu per hour": "BTU/hr",
    "btu/lb/f": "BTU/lb/F",
    "btu/lb/degf": "BTU/lb/F",
    "btu/lb-f": "BTU/lb/F",
    "btu/lb-degf": "BTU/lb/F",
    "btu/(lb*f)": "BTU/lb/F",
    "btu/(lb*degf)": "BTU/lb/F",
    "btu/(lb*deltaf)": "BTU/lb/F",
    "btu/lb*f": "BTU/lb/F",
    "btu/lb*degf": "BTU/lb/F",
    "btu_per_lb_f": "BTU/lb/F",
    "btu_per_lb_deg_f": "BTU/lb/F",
    "btu_per_lb_degf": "BTU/lb/F",
    "btu_per_lbf": "BTU/lb/F",
    "btu_per_lbdeltaf": "BTU/lb/F",
    "btu_per_lb_deltaf": "BTU/lb/F",
    "btu_per_lb_delta_f": "BTU/lb/F",
    "btu/hr/gpm/f": "BTU/hr/gpm/F",
    "btu_per_hr_per_gpm_f": "BTU/hr/gpm/F",
    "btu_per_hour_per_gpm_f": "BTU/hr/gpm/F",
    "btu per hr per gpm f": "BTU/hr/gpm/F",
    "btu/hr/gpm/degf": "BTU/hr/gpm/F",
    "k": "K",
    "usd": "USD",
    "$": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "usd/year": "USD/year",
    "usd_per_year": "USD/year",
    "usd per year": "USD/year",
    "usd_per_yr": "USD/year",
    "usd/yr": "USD/year",
    "dollar/year": "USD/year",
    "dollar/yr": "USD/year",
    "dollar_per_year": "USD/year",
    "dollar per year": "USD/year",
    "dollar_per_yr": "USD/year",
    "dollars/year": "USD/year",
    "dollars/yr": "USD/year",
    "dollars_per_year": "USD/year",
    "dollars per year": "USD/year",
    "dollars_per_yr": "USD/year",
    "$/year": "USD/year",
    "$/yr": "USD/year",
    "usd/scfm/year": "USD/scfm/year",
    "usd/scfm-year": "USD/scfm/year",
    "usd/scfm/yr": "USD/scfm/year",
    "usd/scfm-yr": "USD/scfm/year",
    "usd/scfm*year": "USD/scfm/year",
    "usd_per_scfm_year": "USD/scfm/year",
    "usd_per_scfm_per_year": "USD/scfm/year",
    "usd_per_scfm_yr": "USD/scfm/year",
    "usd_per_scfm_per_yr": "USD/scfm/year",
    "usd per scfm year": "USD/scfm/year",
    "usd per scfm per year": "USD/scfm/year",
    "dollar/scfm/year": "USD/scfm/year",
    "dollar/scfm-year": "USD/scfm/year",
    "dollar/scfm/yr": "USD/scfm/year",
    "dollar/scfm-yr": "USD/scfm/year",
    "dollar_per_scfm_year": "USD/scfm/year",
    "dollar_per_scfm_per_year": "USD/scfm/year",
    "dollar_per_scfm_yr": "USD/scfm/year",
    "dollar_per_scfm_per_yr": "USD/scfm/year",
    "dollars/scfm/year": "USD/scfm/year",
    "dollars/scfm-year": "USD/scfm/year",
    "dollars/scfm/yr": "USD/scfm/year",
    "dollars/scfm-yr": "USD/scfm/year",
    "dollars_per_scfm_year": "USD/scfm/year",
    "dollars_per_scfm_per_year": "USD/scfm/year",
    "dollars_per_scfm_yr": "USD/scfm/year",
    "dollars_per_scfm_per_yr": "USD/scfm/year",
    "$/scfm/year": "USD/scfm/year",
    "$/scfm-year": "USD/scfm/year",
    "$/scfm/yr": "USD/scfm/year",
    "$/scfm-yr": "USD/scfm/year",
    "year": "year",
    "years": "year",
    "yr": "year",
    "yrs": "year",
    "y": "year",
    "ton": "ton",
    "tons": "ton",
    "kJ/kg/C".lower(): "kJ/kg/C",
    "kJ/kg*C".lower(): "kJ/kg/C",
    "kJ/(kg*C)".lower(): "kJ/kg/C",
    "kJ/kg·°C".lower(): "kJ/kg/C",
    "kJ/kg °C".lower(): "kJ/kg/C",
    "kJ/kg degC".lower(): "kJ/kg/C",
    "kJ per kg per C".lower(): "kJ/kg/C",
    "kJ/kg_C".lower(): "kJ/kg/C",
    "kJ/kg_degC".lower(): "kJ/kg/C",
    "kJ/kg*K".lower(): "kJ/kg/C",
    "kj/kwh": "kJ/kWh",
    "kg/c": "kg/C",
    "kg/degc": "kg/C",
    "kg/degreec": "kg/C",
    "c/w": "C/W",
    "degc/w": "C/W",
    "c_per_w": "C/W",
    "degc_per_w": "C/W",
    "cperw": "C/W",
    "degcperw": "C/W",
    "celsiusperw": "C/W",
    "w/c": "W/C",
    "w/degc": "W/C",
    "w_per_c": "W/C",
    "w_per_degc": "W/C",
    "w per c": "W/C",
    "w per degc": "W/C",
    "w/k": "W/K",
    "w_per_k": "W/K",
    "wperk": "W/K",
    "w per k": "W/K",
    "w_per_kelvin": "W/K",
    "w per kelvin": "W/K",
    "k/w": "K/W",
    "k_per_w": "K/W",
    "kperw": "K/W",
    "kelvinperw": "K/W",
    "ohm/ft": "ohm/ft",
    "ohms/ft": "ohm/ft",
    "ohm/foot": "ohm/ft",
    "ohms/foot": "ohm/ft",
    "ohm/feet": "ohm/ft",
    "ohms/feet": "ohm/ft",
    "ohm_per_ft": "ohm/ft",
    "ohms_per_ft": "ohm/ft",
    "ohm_per_foot": "ohm/ft",
    "ohms_per_foot": "ohm/ft",
    "ohm/1000ft": "ohm/1000ft",
    "ohms/1000ft": "ohm/1000ft",
    "ohm/1000feet": "ohm/1000ft",
    "ohms/1000feet": "ohm/1000ft",
    "ohm_per_1000ft": "ohm/1000ft",
    "ohms_per_1000ft": "ohm/1000ft",
    "ohm per 1000 ft": "ohm/1000ft",
    "ohms per 1000 ft": "ohm/1000ft",
    "ohm per 1000 feet": "ohm/1000ft",
    "ohms per 1000 feet": "ohm/1000ft",
    "ohmper1000ft": "ohm/1000ft",
    "ohmsper1000ft": "ohm/1000ft",
}

_MISSING_INPUT = object()


def process(mcm_request: dict) -> dict:
    baseline_result = _process_without_sensitivity(mcm_request)
    baseline_result = _attach_constraint_checks_result(mcm_request, baseline_result)
    baseline_result = _attach_sensitivity_result(mcm_request, baseline_result)
    return _attach_run_health_summary(mcm_request, baseline_result)


def _process_without_sensitivity(mcm_request: dict) -> dict:
    """
    Executes deterministic, stdlib-only computations for simple MCM requests.

    Unsupported or underconstrained requests return structured status objects
    instead of raising into the EAS worker.
    """

    try:
        validation = _validate_request(mcm_request)
        if validation:
            return validation

        _repair_activation1_schema_drift_before_input_extraction(mcm_request)
        _repair_list_subscripts_before_input_extraction(mcm_request)
        inputs = _extract_inputs(mcm_request)

        # Routing priority is intentionally conservative:
        # 1. explicit dependency-ordered equations from Activation 1,
        # 2. an explicitly requested known formula handler,
        # 3. legacy single-expression/simple-operation fallbacks.
        if _has_explicit_equation_plan(mcm_request):
            return _process_equation_plan(
                mcm_request,
                inputs,
                _equation_plan_router_diagnostics(mcm_request, inputs),
            )

        formula_result = _process_formula_handler(mcm_request, inputs, _has_equation_plan(mcm_request))
        if formula_result:
            return formula_result

        if _has_equation_plan(mcm_request):
            return _process_equation_plan(mcm_request, inputs)

        expression = _select_expression(mcm_request)

        if expression:
            return _process_expression(mcm_request, expression, inputs)

        operation = str(mcm_request.get("operation") or mcm_request.get("task_type") or "").strip().lower()
        if operation:
            return _process_operation(mcm_request, operation, inputs)

        return _base_result(
            mcm_request,
            status="unsupported",
            message="MCM request did not contain a supported direct expression or simple operation.",
            outputs={},
            diagnostics=[
                "Supported paths are direct arithmetic expression evaluation and simple operations over numeric inputs.",
                "Symbolic rearrangement, equation solving, unit conversion, and iterative solvers are not implemented in this pass.",
            ],
        )

    except Exception:
        logger.exception("MCM processing failed.")
        return _base_result(
            mcm_request if isinstance(mcm_request, dict) else {},
            status="error",
            message="MCM processing failed.",
            outputs={},
            diagnostics=["MCM caught an internal exception and returned a structured error."],
        )


def _validate_request(mcm_request):
    if not isinstance(mcm_request, dict):
        return {
            "module": "Synthetic_OS_MCM",
            "status": "error",
            "message": "mcm_request must be a dictionary.",
            "outputs": {},
            "diagnostics": ["Invalid input type."],
        }

    if not mcm_request:
        return _base_result(
            {},
            status="needs_human_review",
            message="MCM request is empty.",
            outputs={},
            diagnostics=["No computation fields were provided."],
        )

    required_missing = _required_computation_missing_variables(mcm_request)
    if required_missing:
        return _base_result(
            mcm_request,
            status="needs_human_review",
            message="MCM request is missing variables explicitly required for computation.",
            outputs={},
            diagnostics=[f"Required missing variables: {', '.join(required_missing)}"],
        )

    return None


def _required_computation_missing_variables(mcm_request):
    required = set()

    request_required = mcm_request.get("required_for_computation")
    if isinstance(request_required, list):
        required.update(str(item) for item in request_required)

    variables = mcm_request.get("variables")
    if isinstance(variables, dict):
        for name, value in variables.items():
            if isinstance(value, dict) and value.get("required_for_computation") is True:
                required.add(str(name))

    missing = []
    for name in sorted(required):
        value = None
        if isinstance(variables, dict) and isinstance(variables.get(name), dict):
            value = variables[name].get("value")
        if _known_input_value(value) is _MISSING_INPUT:
            missing.append(name)

    return missing


def _extract_inputs(mcm_request):
    inputs = {}

    raw_inputs = mcm_request.get("inputs")
    if isinstance(raw_inputs, dict):
        for key, value in raw_inputs.items():
            if isinstance(value, dict):
                known_value = _known_input_value_for_unit(value.get("value"), value.get("unit"))
            else:
                known_value = _known_input_value(value)
            if known_value is not _MISSING_INPUT:
                inputs[str(key)] = known_value

    raw_constants = mcm_request.get("constants")
    if isinstance(raw_constants, dict):
        for key, value in raw_constants.items():
            if isinstance(value, dict):
                known_value = _known_input_value_for_unit(value.get("value"), value.get("unit"))
            else:
                known_value = _known_input_value(value)
            if known_value is not _MISSING_INPUT:
                inputs[str(key)] = known_value

    variables = mcm_request.get("variables")
    if isinstance(variables, dict):
        for key, value in variables.items():
            raw_unit = None
            if isinstance(value, dict):
                raw_value = value.get("value")
                raw_unit = value.get("unit")
            else:
                raw_value = value

            known_value = _known_input_value_for_unit(raw_value, raw_unit)
            if known_value is not _MISSING_INPUT:
                inputs[str(key)] = known_value

    return inputs


def _declared_variable_names(mcm_request):
    variables = mcm_request.get("variables") if isinstance(mcm_request, dict) else None
    if not isinstance(variables, dict):
        return set()
    return {str(name) for name in variables}


def _nullable_missing_equation_output_names(mcm_request, equations):
    if normalize_eas_mode(mcm_request.get("mode") if isinstance(mcm_request, dict) else None) != "solve-problem":
        return set()
    nullable = set()
    for name in _expected_equation_output_names(equations):
        lowered = str(name or "").strip().lower()
        if lowered.startswith("selected_"):
            nullable.add(name)
    return nullable


def _has_equation_plan(mcm_request):
    equations = mcm_request.get("equations")
    if not isinstance(equations, list) or not equations:
        return False
    return any(_equation_expression(equation) for equation in equations)


def _has_explicit_equation_plan(mcm_request):
    equations = mcm_request.get("equations")
    variables = mcm_request.get("variables")
    solve_for = mcm_request.get("solve_for")
    return (
        isinstance(equations, list)
        and any(_equation_expression(equation) for equation in equations)
        and isinstance(variables, dict)
        and bool(variables)
        and isinstance(solve_for, list)
        and bool(solve_for)
    )


def preflight_and_repair_mcm_request(mcm_request, repair=True, strict=False):
    schema_normalization = _normalize_activation1_schema_drift(mcm_request, repair=repair)
    result = _preflight_equation_variable_references(mcm_request, repair=repair, strict=strict)
    if schema_normalization.get("diagnostics"):
        result["diagnostics"] = list(schema_normalization.get("diagnostics") or []) + list(result.get("diagnostics") or [])
    if schema_normalization.get("unresolved"):
        result["unresolved"] = list(schema_normalization.get("unresolved") or []) + list(result.get("unresolved") or [])
        result["ok"] = False
    if repair and result.get("diagnostics"):
        _append_schema_normalization_diagnostics(mcm_request, result["diagnostics"])
    return result


def preflight_failure_result(mcm_request, preflight):
    return _preflight_error_result(mcm_request, preflight)


def _repair_activation1_schema_drift_before_input_extraction(mcm_request):
    if not isinstance(mcm_request, dict):
        return
    result = _normalize_activation1_schema_drift(mcm_request, repair=True)
    diagnostics = result.get("diagnostics") or []
    if diagnostics:
        _append_schema_normalization_diagnostics(mcm_request, diagnostics)


def _repair_list_subscripts_before_input_extraction(mcm_request):
    if not isinstance(mcm_request, dict):
        return
    result = _normalize_list_subscript_variables(mcm_request, repair=True)
    diagnostics = result.get("diagnostics") or []
    if diagnostics:
        _append_schema_normalization_diagnostics(mcm_request, diagnostics)


def _append_schema_normalization_diagnostics(mcm_request, diagnostics):
    if not isinstance(mcm_request, dict) or not diagnostics:
        return
    existing = mcm_request.get("schema_normalization_diagnostics", [])
    if not isinstance(existing, list):
        existing = [str(existing)]
    for diagnostic in diagnostics:
        if diagnostic not in existing:
            existing.append(diagnostic)
    mcm_request["schema_normalization_diagnostics"] = existing


def _normalize_activation1_schema_drift(mcm_request, repair=True):
    if not isinstance(mcm_request, dict):
        return {"diagnostics": [], "unresolved": []}

    diagnostics = []
    unresolved = []
    _normalize_malformed_variable_value_entries(mcm_request, repair, diagnostics, unresolved)
    _normalize_hydraulic_231_conversion_factor_variables(mcm_request, repair, diagnostics)
    _normalize_equation_piecewise_default_syntax(mcm_request, repair, diagnostics)
    _normalize_selection_status_any_null_pattern(mcm_request, repair, diagnostics)
    _normalize_rhs_only_equations_from_context(mcm_request, repair, diagnostics, unresolved)
    _normalize_component_cost_aliases(mcm_request, repair, diagnostics)
    _normalize_composite_candidate_component_references(mcm_request, repair, diagnostics)
    _repair_cross_candidate_equation_references(mcm_request, repair, diagnostics, unresolved)
    _reconstruct_missing_candidate_local_criteria(mcm_request, repair, diagnostics)

    reference_map = _equation_name_to_lhs_reference_map(mcm_request)
    unique_name_to_lhs = reference_map.get("unique", {})
    ambiguous_names = reference_map.get("ambiguous", {})
    lhs_names = reference_map.get("lhs_names", set())

    for field in ("dependency_order", "solve_for", "requested_outputs"):
        _normalize_schema_reference_list_field(
            mcm_request,
            field,
            unique_name_to_lhs,
            ambiguous_names,
            lhs_names,
            diagnostics,
            unresolved,
            repair,
        )
    _normalize_schema_reference_string_field(
        mcm_request,
        "requested_output",
        unique_name_to_lhs,
        ambiguous_names,
        lhs_names,
        diagnostics,
        unresolved,
        repair,
    )

    return {"diagnostics": diagnostics, "unresolved": unresolved}


_VARIABLE_METADATA_KEYS = {
    "value",
    "unit",
    "description",
    "source",
    "source_reference",
    "source_references",
    "evidence",
    "evidence_map",
    "notes",
    "note",
    "required_for_computation",
    "derived",
    "computed",
    "formula",
    "expression",
    "equation",
    "confidence",
    "confidence_score",
    "traceability",
    "trace",
    "role",
    "type",
    "kind",
    "category",
    "bounds",
    "min",
    "max",
    "nominal",
    "nullable",
    "allow_null",
}


def _normalize_malformed_variable_value_entries(mcm_request, repair, diagnostics, unresolved):
    variables = mcm_request.get("variables") if isinstance(mcm_request, dict) else None
    if not isinstance(variables, dict):
        return

    equation_lhs_names = set(_infer_equation_lhs_reference_map(mcm_request.get("equations")).keys())
    rhs_references = _equation_rhs_reference_names(mcm_request.get("equations"))
    for name, variable in variables.items():
        if not isinstance(variable, dict) or "value" in variable:
            continue

        malformed_value = _single_unknown_scalar_variable_value(variable)
        if malformed_value is not None:
            key, value = malformed_value
            if repair:
                variable["value"] = value
                variable.pop(key, None)
            diagnostics.append(
                f"variable_value_key_repaired:{name}: moved malformed scalar key {key!r} to value."
            )
            continue

        if _variable_object_is_explicitly_derived(name, variable, equation_lhs_names):
            continue

        diagnostics.append(
            f"variable_value_missing:{name}: variable object has no value field and is not marked derived."
        )
        if str(name) in rhs_references:
            unresolved.append({
                "code": "variable_value_missing",
                "location": "variables",
                "expression": None,
                "variable": str(name),
                "known_names": [],
                "suggestion": None,
            })


def _normalize_hydraulic_231_conversion_factor_variables(mcm_request, repair, diagnostics):
    variables = mcm_request.get("variables") if isinstance(mcm_request, dict) else None
    if not isinstance(variables, dict):
        return

    for name, variable in variables.items():
        if not isinstance(variable, dict):
            continue
        corrected = _hydraulic_231_conversion_factor_unit_from_context(
            name,
            variable.get("unit"),
            variable.get("value"),
            variable,
        )
        if corrected != "in^3/gal":
            continue

        normalized_raw_unit = normalize_unit(variable.get("unit"))
        changed = (
            normalized_raw_unit != "in^3/gal"
            or variable.get("unit_kind") != "hydraulic_volume_conversion_factor"
        )
        if repair:
            variable["unit"] = "in^3/gal"
            variable["unit_kind"] = "hydraulic_volume_conversion_factor"
            note = "231 in^3 per gallon; used to convert in^3/min to gal/min"
            existing = str(variable.get("source_expression") or variable.get("normalization_note") or "")
            if note not in existing:
                variable.setdefault("source_expression", note)
        if changed:
            diagnostics.append(
                f"hydraulic_231_conversion_factor_unit_normalized:{name}: normalized unit to in^3/gal."
            )


def _single_unknown_scalar_variable_value(variable):
    candidates = []
    for key, value in variable.items():
        key_text = str(key)
        if key_text in _VARIABLE_METADATA_KEYS:
            continue
        if _is_repairable_variable_scalar_value(value):
            candidates.append((key, value))
    if len(candidates) == 1:
        return candidates[0]
    return None


def _is_repairable_variable_scalar_value(value):
    return isinstance(value, (str, int, float, bool))


def _variable_object_is_explicitly_derived(name, variable, equation_lhs_names):
    if str(name) in equation_lhs_names:
        return True
    for key in ("derived", "computed"):
        if variable.get(key) is True:
            return True
    for key in ("source", "role", "type", "kind"):
        text = str(variable.get(key) or "").strip().lower()
        if text in {"derived", "computed", "formula", "equation_output", "output"}:
            return True
    return any(variable.get(key) not in (None, "") for key in ("formula", "expression", "equation"))


def _equation_rhs_reference_names(equations):
    names = set()
    if not isinstance(equations, list):
        return names
    for equation in equations:
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        _lhs, rhs = parsed
        try:
            names.update(str(name) for name in _collect_names(rhs))
        except Exception:  # noqa: S112 - optional malformed expression is skipped
            continue
    return names


def _normalize_equation_piecewise_default_syntax(mcm_request, repair, diagnostics):
    equations = mcm_request.get("equations")
    if not isinstance(equations, list):
        return

    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        if not expression:
            continue
        normalized, changed = _normalize_piecewise_default_argument(expression)
        if not changed:
            continue
        if repair:
            if isinstance(equation, dict):
                equation["expression"] = normalized
            else:
                equations[index - 1] = normalized
        diagnostics.append(
            f"Normalized final piecewise else= default syntax to positional default in {_equation_name(equation, index)}."
        )


def _normalize_selection_status_any_null_pattern(mcm_request, repair, diagnostics):
    equations = mcm_request.get("equations")
    if not isinstance(equations, list):
        return

    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        normalized_rhs = _selection_status_any_null_replacement(lhs, rhs)
        if not normalized_rhs or normalized_rhs == rhs:
            continue
        normalized_expression = f"{lhs} = {normalized_rhs}"
        if repair:
            if isinstance(equation, dict):
                equation["expression"] = normalized_expression
            else:
                equations[index - 1] = normalized_expression
        diagnostics.append(
            f"Normalized sparse selection-status null check in {_equation_name(equation, index)} to test min_ignore_null(...) for no viable options."
        )


def _selection_status_any_null_replacement(lhs, rhs):
    lowered_lhs = str(lhs or "").strip().lower()
    if not lowered_lhs.endswith(("_selection_status_reason", "_recommendation_status_reason")):
        return None
    pattern = re.compile(
        r"^\s*if_?\s*\(\s*any_null\s*\(\s*(?P<scores>\[[^\]]*\])\s*\)\s*,\s*"
        r"(?P<no_viable>['\"]NO_VIABLE_OPTIONS?_FOUND['\"])\s*,\s*"
        r"(?P<viable>['\"]VIABLE_OPTIONS?_FOUND['\"])\s*\)\s*$",
        re.IGNORECASE,
    )
    match = pattern.match(str(rhs or ""))
    if not match:
        return None
    scores = match.group("scores")
    return f"if(is_null(min_ignore_null({scores})), {match.group('no_viable')}, {match.group('viable')})"


def _equation_name_to_lhs_reference_map(mcm_request):
    equations = mcm_request.get("equations")
    if not isinstance(equations, list):
        return {"unique": {}, "ambiguous": {}, "lhs_names": set()}

    by_name = {}
    lhs_names = set()
    for index, equation in enumerate(equations, start=1):
        if not isinstance(equation, dict):
            continue
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, _ = parsed
        lhs_names.add(lhs)
        raw_name = equation.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            continue
        name = raw_name.strip()
        by_name.setdefault(name, []).append({"lhs": lhs, "index": index})

    unique = {}
    ambiguous = {}
    for name, items in by_name.items():
        mapped_lhs = sorted({item.get("lhs") for item in items if item.get("lhs")})
        if len(mapped_lhs) == 1:
            unique[name] = mapped_lhs[0]
        elif len(mapped_lhs) > 1:
            ambiguous[name] = mapped_lhs
    return {"unique": unique, "ambiguous": ambiguous, "lhs_names": lhs_names}


def _normalize_schema_reference_list_field(
    mcm_request,
    field,
    unique_name_to_lhs,
    ambiguous_names,
    lhs_names,
    diagnostics,
    unresolved,
    repair,
):
    values = mcm_request.get(field)
    if not isinstance(values, list):
        return

    changed = False
    normalized_values = []
    for value in values:
        normalized, value_changed = _normalize_schema_reference_value(
            field,
            value,
            unique_name_to_lhs,
            ambiguous_names,
            lhs_names,
            diagnostics,
            unresolved,
        )
        normalized_values.append(normalized)
        changed = changed or value_changed

    if changed and repair:
        mcm_request[field] = normalized_values


def _normalize_schema_reference_string_field(
    mcm_request,
    field,
    unique_name_to_lhs,
    ambiguous_names,
    lhs_names,
    diagnostics,
    unresolved,
    repair,
):
    value = mcm_request.get(field)
    if not isinstance(value, str):
        return
    normalized, changed = _normalize_schema_reference_value(
        field,
        value,
        unique_name_to_lhs,
        ambiguous_names,
        lhs_names,
        diagnostics,
        unresolved,
    )
    if changed and repair:
        mcm_request[field] = normalized


def _normalize_schema_reference_value(
    field,
    value,
    unique_name_to_lhs,
    ambiguous_names,
    lhs_names,
    diagnostics,
    unresolved,
):
    text = str(value).strip()
    if not text or text in lhs_names:
        return value, False
    if text in ambiguous_names:
        message = (
            f"{field} references equation.name {text}, but that name maps ambiguously to equation LHS variables: "
            + ", ".join(ambiguous_names[text])
            + ". Use the intended equation LHS variable name."
        )
        diagnostics.append(message)
        unresolved.append({
            "equation": field,
            "expression": text,
            "variable": text,
            "suggestion": None,
            "suggested_missing_lhs": None,
            "known_variables_available": sorted(lhs_names),
            "message": message,
        })
        return value, False
    if text not in unique_name_to_lhs:
        return value, False

    lhs = unique_name_to_lhs[text]
    if lhs == text:
        return value, False
    diagnostics.append(
        f"Normalized {field} reference from equation.name {text} to parsed equation LHS {lhs}."
    )
    return lhs, True


def _normalize_rhs_only_equations_from_context(mcm_request, repair, diagnostics, unresolved):
    equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    if not isinstance(equations, list):
        return

    downstream_references = _downstream_equation_references(equations)
    request_targets = _request_traceability_targets(mcm_request)
    existing_lhs = _explicit_equation_lhs_names(equations)

    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        if not expression or _split_assignment(expression):
            continue
        if _contains_bare_assignment_operator(expression):
            continue
        rhs_error = _safe_rhs_expression_error(expression)
        if rhs_error:
            _append_structural_preflight_issue(
                unresolved,
                diagnostics,
                code="rhs_only_equation_unresolved",
                location=_equation_name(equation, index),
                expression=expression,
                variable=_equation_name(equation, index),
                message=(
                    "rhs_only_equation_unresolved: RHS-only equation could not be normalized because "
                    f"the expression is not safe: {rhs_error}."
                ),
            )
            continue

        allowed_targets = set(request_targets)
        if index - 1 < len(downstream_references):
            allowed_targets.update(downstream_references[index - 1])
        target_result = _infer_rhs_only_lhs_target(
            equation,
            expression,
            allowed_targets,
            existing_lhs,
        )
        target = target_result.get("target")
        if not target:
            _append_structural_preflight_issue(
                unresolved,
                diagnostics,
                code="rhs_only_equation_unresolved",
                location=_equation_name(equation, index),
                expression=expression,
                variable=_equation_name(equation, index),
                message=(
                    "rhs_only_equation_unresolved: RHS-only equation has no explicit LHS and no single "
                    f"safe traceable target could be inferred. {target_result.get('reason') or ''}".strip()
                ),
            )
            continue

        normalized = f"{target} = {expression}"
        if repair:
            if isinstance(equation, dict):
                equation["expression"] = normalized
            else:
                equations[index - 1] = normalized
        diagnostics.append(
            "rhs_only_equation_normalized: Normalized RHS-only equation to assignment "
            f"using traceable target {target}: {normalized}"
        )


def _downstream_equation_references(equations):
    if not isinstance(equations, list):
        return []
    downstream = [set() for _ in equations]
    future = set()
    for index in range(len(equations) - 1, -1, -1):
        downstream[index] = set(future)
        expression = _equation_expression(equations[index])
        if not expression:
            continue
        rhs = None
        parsed = _split_assignment(expression)
        if parsed:
            _, rhs = parsed
        elif not _contains_bare_assignment_operator(expression):
            rhs = expression
        if not rhs:
            continue
        try:
            future.update(_collect_names(rhs))
        except Exception:  # noqa: S112 - optional malformed expression is skipped
            continue
    return downstream


def _request_traceability_targets(mcm_request):
    targets = set()
    if not isinstance(mcm_request, dict):
        return targets
    for field in ("dependency_order", "solve_for", "requested_outputs"):
        value = mcm_request.get(field)
        if isinstance(value, list):
            for item in value:
                text = str(item).strip()
                if _is_safe_variable_name(text):
                    targets.add(text)
    requested_output = mcm_request.get("requested_output")
    if isinstance(requested_output, str) and _is_safe_variable_name(requested_output.strip()):
        targets.add(requested_output.strip())
    return targets


def _explicit_equation_lhs_names(equations):
    names = set()
    if not isinstance(equations, list):
        return names
    for equation in equations:
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if parsed:
            names.add(parsed[0])
    return names


def _infer_rhs_only_lhs_target(equation, expression, allowed_targets, existing_lhs):
    candidates = []
    field_candidates = _equation_safe_lhs_field_candidates(equation)
    for source, candidate in field_candidates:
        if candidate in allowed_targets and candidate not in existing_lhs and _rhs_expression_matches_target_shape(expression, candidate):
            candidates.append((candidate, f"equation.{source}"))

    if not candidates:
        for target in sorted(str(item) for item in allowed_targets):
            if target in existing_lhs or not _is_safe_variable_name(target):
                continue
            if not _rhs_expression_matches_target_shape(expression, target):
                continue
            if _rhs_only_target_matches_context(target, equation, expression):
                candidates.append((target, "traceability_context"))

    unique = {}
    for target, source in candidates:
        unique.setdefault(target, set()).add(source)
    if len(unique) == 1:
        target = next(iter(unique))
        return {"target": target, "source": ", ".join(sorted(unique[target]))}
    if len(unique) > 1:
        return {
            "target": None,
            "reason": "Multiple possible LHS targets were found: " + ", ".join(sorted(unique)) + ".",
        }
    return {"target": None, "reason": "No dependency_order, solve_for, or downstream reference uniquely matched the RHS-only equation."}


def _equation_safe_lhs_field_candidates(equation):
    if not isinstance(equation, dict):
        return []
    candidates = []
    for field in ("lhs", "output", "target", "result", "name"):
        raw_value = equation.get(field)
        if not isinstance(raw_value, str):
            continue
        candidate = raw_value.strip()
        if _is_safe_variable_name(candidate):
            candidates.append((field, candidate))
    return candidates


def _rhs_only_target_matches_context(target, equation, expression):
    target_identity = _candidate_identity_from_name(target)
    context_identities = _candidate_identities_from_text(
        " ".join(
            str(value)
            for value in (
                _equation_name(equation, 0),
                _equation_purpose(equation),
                expression,
            )
            if value
        )
    )
    if target_identity and context_identities and target_identity not in context_identities:
        return False

    target_criterion = _candidate_criterion_token(target)
    context_criteria = _criterion_tokens_from_text(
        " ".join(
            str(value)
            for value in (
                _equation_name(equation, 0),
                _equation_purpose(equation),
                expression,
            )
            if value
        )
    )
    if target_criterion and context_criteria and target_criterion not in context_criteria:
        return False
    if target_identity or target_criterion:
        return True
    lowered_target = str(target).lower()
    lowered_context = f"{_equation_name(equation, 0)} {_equation_purpose(equation)}".lower()
    return lowered_target in lowered_context


def _rhs_expression_matches_target_shape(expression, target):
    try:
        tree = ast.parse(_normalize_boolean_operators(expression), mode="eval")
    except SyntaxError:
        return False
    boolean_rhs = _rhs_node_is_boolean_like(tree.body)
    boolean_target = _target_name_expects_boolean(target)
    status_target = _target_name_expects_status(target)
    if boolean_target:
        return boolean_rhs
    if status_target:
        return True
    return not boolean_rhs


def _rhs_node_is_boolean_like(node):
    if isinstance(node, ast.Compare):
        return True
    if isinstance(node, ast.BoolOp):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return True
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return True
    if isinstance(node, ast.Name) and node.id in {"true", "false", "True", "False"}:
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in {"any_null", "is_null"}
    return False


def _target_name_expects_boolean(name):
    tokens = _name_tokens(name)
    token_set = set(tokens)
    lowered = str(name or "").lower()
    if _has_explicit_boolean_predicate_shape(tokens, token_set):
        return True
    if lowered.endswith(("_is_viable", "_is_valid", "_valid", "_ok", "_met")):
        return True
    if (
        lowered.endswith(("_required", "_enabled"))
        and not _has_unit_bearing_metric_token(lowered, token_set)
    ):
        return True
    if lowered.startswith(("has_", "is_", "can_")):
        return True
    return False


def _target_name_expects_status(name):
    tokens = set(_name_tokens(name))
    return bool(tokens.intersection({"status", "state", "label", "name"}))


def _normalize_component_cost_aliases(mcm_request, repair, diagnostics):
    equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    if not isinstance(equations, list):
        return

    alias_map = _component_cost_alias_map(mcm_request)
    if not alias_map:
        return

    renamed = []
    rewrites = []
    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        lhs_alias = alias_map.get(lhs)
        new_lhs = lhs_alias["canonical"] if lhs_alias and lhs_alias.get("primary") else lhs

        replacements = {}
        try:
            references = sorted(_collect_names(rhs))
        except Exception:
            references = []
        for reference in references:
            alias = alias_map.get(reference)
            if not alias:
                continue
            if not _component_cost_alias_rewrite_allowed(new_lhs, alias):
                continue
            replacements[reference] = alias["canonical"]

        if not lhs_alias and not replacements:
            continue

        new_rhs = _replace_expression_names(rhs, replacements) if replacements else rhs
        if repair:
            repaired_expression = f"{new_lhs} = {new_rhs}"
            if isinstance(equation, dict):
                equation["expression"] = repaired_expression
                if str(equation.get("name") or "").strip() == lhs:
                    equation["name"] = new_lhs
            else:
                equations[index - 1] = repaired_expression

        if lhs_alias and new_lhs != lhs:
            renamed.append(f"{lhs}->{new_lhs}")
        for old, new in sorted(replacements.items()):
            rewrites.append(f"{old}->{new}")

    if repair:
        _normalize_component_cost_reference_fields(mcm_request, alias_map)

    messages = []
    if renamed:
        messages.append("renamed " + ", ".join(sorted(set(renamed))))
    if rewrites:
        messages.append("rewrote " + ", ".join(sorted(set(rewrites))))
    if messages:
        diagnostics.append(
            "component_cost_alias_normalized: "
            + "; ".join(messages)
            + "."
        )


def _component_cost_alias_map(mcm_request):
    equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    if not isinstance(equations, list):
        return {}

    alias_map = {}
    first_source_by_canonical = {}
    for equation in equations:
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        pipe_alias = _pipe_only_installed_cost_alias(lhs, rhs)
        if not pipe_alias:
            continue
        canonical = pipe_alias["canonical"]
        first_source_by_canonical.setdefault(canonical, lhs)
        pipe_alias["primary"] = first_source_by_canonical[canonical] == lhs
        alias_map[lhs] = pipe_alias
    return alias_map


def _pipe_only_installed_cost_alias(lhs, rhs):
    lhs_identity = _candidate_identity_from_name(lhs)
    lhs_parts = _composite_candidate_identity_parts(lhs_identity)
    if not lhs_parts:
        return None
    if not _name_looks_like_installed_pipe_cost(lhs):
        return None
    if normalize_unit(_unit_from_name_suffix(lhs)) != "USD":
        return None

    try:
        references = sorted(_collect_names(rhs))
    except Exception:
        return None
    pipe = lhs_parts.get("pipe")
    if not _references_prove_pipe_only_installed_cost(references, pipe):
        return None

    return {
        "canonical": _canonical_pipe_installed_cost_name(pipe, lhs),
        "component": "pipe",
        "pipe": pipe,
        "source": lhs,
    }


def _name_looks_like_installed_pipe_cost(name):
    lowered = str(name or "").strip().lower()
    tokens = set(_name_tokens(name))
    return (
        "installed_pipe_cost" in lowered
        or "pipe_cost" in lowered
        or {"installed", "pipe", "cost"}.issubset(tokens)
    )


def _references_prove_pipe_only_installed_cost(references, pipe):
    if not references or not pipe:
        return False
    has_physical_length = False
    has_pipe_cost_rate = False
    for reference in references:
        components = _candidate_reference_components(reference)
        if components.get("pump"):
            return False
        if components.get("pipe") and components.get("pipe") != pipe:
            return False
        if _is_physical_installed_pipe_length_reference(reference):
            has_physical_length = True
            continue
        if _is_pipe_installed_cost_rate_reference(reference, pipe):
            has_pipe_cost_rate = True
            continue
        return False
    return has_physical_length and has_pipe_cost_rate


def _is_physical_installed_pipe_length_reference(name):
    lowered = str(name or "").strip().lower()
    tokens = set(_name_tokens(name))
    return (
        "physical_installed_pipe_length" in lowered
        or {"physical", "installed", "pipe", "length"}.issubset(tokens)
    )


def _is_pipe_installed_cost_rate_reference(name, pipe):
    components = _candidate_reference_components(name)
    if components.get("pipe") != pipe or components.get("pump"):
        return False
    tokens = set(_name_tokens(name))
    return (
        "cost" in tokens
        and "per" in tokens
        and bool(tokens.intersection({"ft", "foot", "feet"}))
    )


def _canonical_pipe_installed_cost_name(pipe, source_name):
    pipe_display = _candidate_component_display("pipe", pipe)
    return f"pipe_{pipe_display}_installed_cost_{_currency_suffix_from_name(source_name)}"


def _currency_suffix_from_name(name):
    match = re.search(r"(?:^|_)(USD|usd)(?:_|$)", str(name or ""))
    return match.group(1) if match else "usd"


def _component_cost_alias_rewrite_allowed(lhs, alias):
    canonical = alias.get("canonical") if isinstance(alias, dict) else None
    if not canonical:
        return False
    lhs_identity = _candidate_identity_from_name(lhs)
    if not lhs_identity:
        return True
    return _candidate_reference_allowed_by_composition(lhs_identity, canonical)


def _normalize_component_cost_reference_fields(mcm_request, alias_map):
    replacements = {
        source: alias.get("canonical")
        for source, alias in (alias_map or {}).items()
        if alias.get("canonical")
    }
    if not replacements:
        return
    for field in ("dependency_order", "solve_for", "requested_outputs"):
        value = mcm_request.get(field)
        if not isinstance(value, list):
            continue
        mcm_request[field] = [replacements.get(str(item), item) for item in value]

    requested_output = mcm_request.get("requested_output")
    if isinstance(requested_output, str) and requested_output in replacements:
        mcm_request["requested_output"] = replacements[requested_output]


def _repair_cross_candidate_equation_references(mcm_request, repair, diagnostics, unresolved):
    equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    if not isinstance(equations, list):
        return

    known_names = _preflight_all_known_names(mcm_request)
    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        lhs_identity = _candidate_identity_from_name(lhs)
        if not lhs_identity:
            continue
        if not _is_candidate_local_criteria_output(lhs) and not _is_composite_candidate_identity(lhs_identity):
            continue
        try:
            references = sorted(_collect_names(rhs))
        except Exception:  # noqa: S112 - optional malformed expression is skipped
            continue
        replacements = {}
        for reference in references:
            reference_identity = _candidate_identity_from_name(reference)
            if not reference_identity or reference_identity == lhs_identity:
                component_issue = _candidate_component_reference_issue(lhs_identity, reference)
                if component_issue:
                    _append_structural_preflight_issue(
                        unresolved,
                        diagnostics,
                        code="unsafe_cross_candidate_resolution_rejected",
                        location=_equation_name(equation, index),
                        expression=expression,
                        variable=reference,
                        message=component_issue,
                    )
                continue
            if _candidate_reference_allowed_by_composition(lhs_identity, reference):
                continue
            local_reference = _replace_candidate_identity_in_name(reference, reference_identity, lhs_identity)
            if (
                local_reference
                and local_reference != reference
                and (
                    local_reference in known_names
                    or _candidate_local_reconstruction(local_reference, equations, known_names)
                )
            ):
                replacements[reference] = local_reference
                diagnostics.append(
                    "unsafe_cross_candidate_resolution_rejected: Rejected cross-candidate reference "
                    f"{reference} in {lhs}; using local candidate reference {local_reference} instead."
                )
                continue
            component_issue = _candidate_component_reference_issue(lhs_identity, reference)
            if component_issue:
                _append_structural_preflight_issue(
                    unresolved,
                    diagnostics,
                    code="unsafe_cross_candidate_resolution_rejected",
                    location=_equation_name(equation, index),
                    expression=expression,
                    variable=reference,
                    message=component_issue,
                )
                continue
            _append_structural_preflight_issue(
                unresolved,
                diagnostics,
                code="unsafe_cross_candidate_resolution_rejected",
                location=_equation_name(equation, index),
                expression=expression,
                variable=reference,
                message=(
                    "unsafe_cross_candidate_resolution_rejected: Candidate-specific equation "
                    f"{lhs} references {reference}, which changes candidate identity from "
                    f"{_candidate_identity_display(lhs_identity)} to {_candidate_identity_display(reference_identity)}. "
                    "Human/schema correction is required unless a safe local target can be reconstructed."
                ),
            )
        if repair and replacements:
            repaired_rhs = _replace_expression_names(rhs, replacements)
            repaired_expression = f"{lhs} = {repaired_rhs}"
            if isinstance(equation, dict):
                equation["expression"] = repaired_expression
            else:
                equations[index - 1] = repaired_expression
            known_names.update(replacements.values())


def _normalize_composite_candidate_component_references(mcm_request, repair, diagnostics):
    equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    if not isinstance(equations, list):
        return

    known_names = _preflight_all_known_names(mcm_request)
    alias_sources = _existing_candidate_alias_sources(equations)
    insertions = []
    for index, equation in enumerate(equations):
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        lhs_identity = _candidate_identity_from_name(lhs)
        if not _is_composite_candidate_identity(lhs_identity):
            continue
        if not _is_candidate_all_criteria_output(lhs):
            continue
        try:
            references = sorted(_collect_names(rhs))
        except Exception:  # noqa: S112 - optional malformed expression is skipped
            continue

        replacements = {}
        new_alias_equations = []
        for reference in references:
            alias = _candidate_local_alias_for_component_reference(lhs_identity, reference)
            if not alias or alias == reference:
                continue
            if reference not in known_names:
                continue
            if alias in alias_sources and alias_sources[alias] != reference:
                continue
            replacements[reference] = alias
            if alias not in known_names:
                new_alias_equations.append({
                    "name": alias,
                    "expression": f"{alias} = {reference}",
                    "purpose": "Candidate-local alias for safe component-level criterion reuse.",
                })
                known_names.add(alias)
                alias_sources[alias] = reference

        if not replacements:
            continue
        repaired_rhs = _replace_expression_names(rhs, replacements)
        repaired_expression = f"{lhs} = {repaired_rhs}"
        if repair:
            if isinstance(equation, dict):
                equation["expression"] = repaired_expression
            else:
                equations[index] = repaired_expression
            insertions.append((index, new_alias_equations))
        diagnostics.append(
            "candidate_component_reference_normalized: Created candidate-local aliases for "
            f"{lhs}: {', '.join(f'{old}->{new}' for old, new in sorted(replacements.items()))}."
        )

    if repair and insertions:
        offset = 0
        for index, new_alias_equations in insertions:
            if not new_alias_equations:
                continue
            insert_at = index + offset
            equations[insert_at:insert_at] = new_alias_equations
            offset += len(new_alias_equations)


def _existing_candidate_alias_sources(equations):
    sources = {}
    for equation in equations or []:
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        try:
            references = list(_collect_names(rhs))
        except Exception:  # noqa: S112 - optional malformed expression is skipped
            continue
        if len(references) == 1:
            sources[lhs] = references[0]
    return sources


def _is_candidate_all_criteria_output(name):
    lowered = str(name or "").strip().lower()
    tokens = set(_name_tokens(name))
    return "all_criteria" in lowered or {"all", "criteria"}.issubset(tokens)


def _candidate_local_alias_for_component_reference(lhs_identity, reference):
    if not _is_composite_candidate_identity(lhs_identity):
        return None
    if not _candidate_reference_allowed_by_composition(lhs_identity, reference):
        return None
    if _candidate_identity_from_name(reference) == lhs_identity and _canonical_candidate_name_prefix(reference) == _candidate_identity_display(lhs_identity):
        return None
    criterion = _candidate_criterion_token(reference)
    if not criterion:
        return None
    if not _target_name_expects_boolean(reference):
        return None
    descriptor = _candidate_criterion_descriptor(criterion, reference)
    return f"config_{_candidate_identity_display(lhs_identity)}_{criterion.upper()}_{descriptor}_pass"


def _canonical_candidate_name_prefix(name):
    lowered = str(name or "").strip().lower()
    match = re.match(r"^(?:config|configuration)_([a-z0-9]+_p\d+)(?:_|$)", lowered)
    return _candidate_identity_display(match.group(1)) if match else None


def _candidate_criterion_descriptor(criterion, reference):
    lowered = str(reference or "").strip().lower()
    tokens = set(_name_tokens(reference))
    criterion = str(criterion or "").lower()
    if "velocity" in tokens or criterion == "c2":
        return "pipe_velocity"
    if "npsh" in tokens or criterion == "c4":
        return "npsh_margin"
    if "motor" in tokens or "loading" in tokens or "bhp" in tokens or criterion == "c5":
        return "motor_loading"
    if "head" in tokens or "tdh" in tokens or "pump_head" in lowered or criterion == "c3":
        return "pump_head_margin"
    if "flow" in tokens or criterion == "c1":
        return "flow"
    return "criterion"


def _candidate_component_reference_issue(lhs_identity, reference):
    lhs_parts = _composite_candidate_identity_parts(lhs_identity)
    if not lhs_parts:
        return None
    reference_parts = _candidate_reference_components(reference)
    if not reference_parts:
        return None

    mismatches = []
    for component in ("pipe", "pump"):
        reference_value = reference_parts.get(component)
        if reference_value and reference_value != lhs_parts.get(component):
            mismatches.append(
                f"{component} {_candidate_component_display(component, reference_value)}"
            )
    if not mismatches:
        return None

    expected = (
        f"pipe {_candidate_component_display('pipe', lhs_parts['pipe'])} and "
        f"pump {_candidate_component_display('pump', lhs_parts['pump'])}"
    )
    return (
        "unsafe_cross_candidate_resolution_rejected: Candidate-specific equation "
        f"for {_candidate_identity_display(lhs_identity)} references {reference}, whose "
        f"{' / '.join(mismatches)} component does not match expected {expected}."
    )


def _candidate_reference_allowed_by_composition(lhs_identity, reference):
    lhs_parts = _composite_candidate_identity_parts(lhs_identity)
    if not lhs_parts:
        return False
    reference_parts = _candidate_reference_components(reference)
    if not reference_parts:
        return False
    for component in ("pipe", "pump"):
        reference_value = reference_parts.get(component)
        if reference_value and reference_value != lhs_parts.get(component):
            return False
    return True


def _candidate_reference_components(name):
    tokens = _name_tokens(name)
    if not tokens:
        return {}

    components = {}
    for index, token in enumerate(tokens):
        first = tokens[index + 1] if index + 1 < len(tokens) else None
        second = tokens[index + 2] if index + 2 < len(tokens) else None
        third = tokens[index + 3] if index + 3 < len(tokens) else None

        if token == "pipe" and _is_candidate_letter_or_number(first):
            components.setdefault("pipe", first)
            continue

        if token == "pump" and _is_pump_candidate_token(first):
            components.setdefault("pump", first)
            continue

        if token == "option" and _is_candidate_letter_or_number(first):
            components.setdefault("pipe", first)
            if second == "pump" and _is_pump_candidate_token(third):
                components.setdefault("pump", third)
            elif _is_pump_candidate_token(second):
                components.setdefault("pump", second)
            continue

        if token in {"config", "configuration"} and _is_candidate_letter_or_number(first):
            components.setdefault("pipe", first)
            if _is_pump_candidate_token(second):
                components.setdefault("pump", second)
            elif second == "pump" and _is_pump_candidate_token(third):
                components.setdefault("pump", third)

    for index, token in enumerate(tokens[:-1]):
        next_token = tokens[index + 1]
        third = tokens[index + 2] if index + 2 < len(tokens) else None
        if _is_candidate_letter_or_number(token) and _is_pump_candidate_token(next_token):
            components.setdefault("pipe", token)
            components.setdefault("pump", next_token)
        elif _is_candidate_letter_or_number(token) and next_token == "pump" and _is_pump_candidate_token(third):
            components.setdefault("pipe", token)
            components.setdefault("pump", third)

    return components


def _is_composite_candidate_identity(identity):
    return bool(_composite_candidate_identity_parts(identity))


def _composite_candidate_identity_parts(identity):
    parts = str(identity or "").lower().split("_")
    if (
        len(parts) == 2
        and _is_candidate_letter_or_number(parts[0])
        and _is_pump_candidate_token(parts[1])
    ):
        return {"pipe": parts[0], "pump": parts[1]}
    return None


def _candidate_component_display(component, value):
    text = str(value or "")
    if component == "pump":
        return text.upper()
    return text.upper() if len(text) == 1 and text.isalpha() else text


def _reconstruct_missing_candidate_local_criteria(mcm_request, repair, diagnostics):
    equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    if not isinstance(equations, list):
        return

    known_names = _preflight_all_known_names(mcm_request)
    missing_references = _missing_equation_references(equations, known_names)
    for missing_name, first_reference_index in sorted(missing_references.items()):
        reconstruction = _candidate_local_reconstruction(missing_name, equations, known_names)
        if not reconstruction:
            continue
        if repair:
            insert_at = max(0, min(first_reference_index - 1, len(equations)))
            equations.insert(insert_at, {
                "name": missing_name,
                "expression": f"{missing_name} = {reconstruction['rhs']}",
                "purpose": "Reconstructed missing candidate-local criterion from sibling candidate pattern.",
            })
            known_names.add(missing_name)
        diagnostics.append(
            "candidate_local_criterion_reconstructed: Reconstructed "
            f"{missing_name} from sibling candidate criterion pattern."
        )


def _preflight_all_known_names(mcm_request):
    equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    known = _initial_preflight_known_names(mcm_request)
    known.update(_explicit_equation_lhs_names(equations))
    return known


def _missing_equation_references(equations, known_names):
    missing = {}
    available = set(known_names)
    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        try:
            references = sorted(_collect_names(rhs))
        except Exception:
            available.add(lhs)
            continue
        for reference in references:
            if reference not in available:
                missing.setdefault(reference, index)
        available.add(lhs)
    return missing


def _candidate_local_reconstruction(target, equations, known_names):
    if not _is_candidate_local_criteria_output(target):
        return None
    target_identity = _candidate_identity_from_name(target)
    target_criterion = _candidate_criterion_token(target)
    if not target_identity or not target_criterion:
        return None

    candidates = []
    for equation in equations:
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        if lhs == target:
            return None
        lhs_identity = _candidate_identity_from_name(lhs)
        if not lhs_identity or lhs_identity == target_identity:
            continue
        if _candidate_criterion_token(lhs) != target_criterion:
            continue
        if not _same_candidate_output_family(lhs, target):
            continue
        replaced_rhs = _replace_candidate_identity_in_expression(rhs, lhs_identity, target_identity)
        if replaced_rhs == rhs:
            continue
        if not _rhs_expression_matches_target_shape(replaced_rhs, target):
            continue
        try:
            references = _collect_names(replaced_rhs)
        except Exception:  # noqa: S112 - optional malformed expression is skipped
            continue
        missing = sorted(reference for reference in references if reference not in known_names and reference != target)
        if missing:
            continue
        candidates.append(replaced_rhs)

    unique_rhs = sorted(set(candidates))
    if len(unique_rhs) != 1:
        return None
    return {"rhs": unique_rhs[0]}


def _is_candidate_local_criteria_output(name):
    tokens = set(_name_tokens(name))
    if not _candidate_identity_from_name(name):
        return False
    return bool(tokens.intersection({"pass", "passed", "viable", "criteria", "criterion"}))


def _same_candidate_output_family(left, right):
    left_tokens = [token for token in _name_tokens(left) if token not in set(_candidate_identity_from_name(left).split("_"))]
    right_tokens = [token for token in _name_tokens(right) if token not in set(_candidate_identity_from_name(right).split("_"))]
    return left_tokens == right_tokens


def _replace_candidate_identity_in_expression(expression, source_identity, target_identity):
    source_display = _candidate_identity_display(source_identity)
    target_display = _candidate_identity_display(target_identity)
    if not source_display or not target_display:
        return expression
    pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(source_display)}(?![A-Za-z0-9])", re.IGNORECASE)
    return pattern.sub(target_display, expression)


def _replace_candidate_identity_in_name(name, source_identity, target_identity):
    return _replace_candidate_identity_in_expression(str(name), source_identity, target_identity)


def _candidate_identity_from_name(name):
    tokens = _name_tokens(name)
    marker_tokens = {"config", "configuration", "option", "concept", "candidate", "alternative"}
    for index, token in enumerate(tokens):
        if token not in marker_tokens or index + 1 >= len(tokens):
            continue
        first = tokens[index + 1]
        second = tokens[index + 2] if index + 2 < len(tokens) else None
        third = tokens[index + 3] if index + 3 < len(tokens) else None
        if second and _is_candidate_letter_or_number(first) and _is_pump_candidate_token(second):
            return f"{first}_{second}"
        if (
            second == "pump"
            and third
            and _is_candidate_letter_or_number(first)
            and _is_pump_candidate_token(third)
        ):
            return f"{first}_{third}"
        if token in {"option", "concept", "candidate", "alternative"} and _is_candidate_letter_or_number(first):
            return f"{token}_{first}"

    for index, token in enumerate(tokens[:-1]):
        if _is_candidate_letter_or_number(token) and _is_pump_candidate_token(tokens[index + 1]):
            return f"{token}_{tokens[index + 1]}"
        third = tokens[index + 2] if index + 2 < len(tokens) else None
        if _is_candidate_letter_or_number(token) and tokens[index + 1] == "pump" and _is_pump_candidate_token(third):
            return f"{token}_{third}"
    return None


def _candidate_identities_from_text(text):
    identities = set()
    for name in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(text or "")):
        identity = _candidate_identity_from_name(name)
        if identity:
            identities.add(identity)
    return identities


def _candidate_identity_display(identity):
    if not identity:
        return ""
    parts = str(identity).split("_")
    rendered = []
    for part in parts:
        if _is_pump_candidate_token(part):
            rendered.append(part.upper())
        elif len(part) == 1 and part.isalpha():
            rendered.append(part.upper())
        else:
            rendered.append(part)
    return "_".join(rendered)


def _is_candidate_letter_or_number(token):
    text = str(token or "").lower()
    return bool(re.fullmatch(r"[a-z]|\d+", text))


def _is_pump_candidate_token(token):
    return bool(re.fullmatch(r"p\d+", str(token or "").lower()))


def _candidate_criterion_token(name):
    for token in _name_tokens(name):
        if re.fullmatch(r"c\d+", token):
            return token
    return None


def _criterion_tokens_from_text(text):
    return {token for token in _name_tokens(text) if re.fullmatch(r"c\d+", token)}


def _name_tokens(text):
    return [token for token in re.split(r"[^a-z0-9]+", str(text or "").lower()) if token]


def _append_structural_preflight_issue(unresolved, diagnostics, *, code, location, expression, variable, message):
    unresolved.append({
        "code": code,
        "equation": location,
        "expression": expression,
        "variable": variable,
        "suggestion": None,
        "suggested_missing_lhs": None,
        "known_variables_available": [],
        "message": message,
    })
    diagnostics.append(message)


def _preflight_equation_variable_references(mcm_request, repair=True, strict=False):
    if not isinstance(mcm_request, dict):
        return {"ok": False, "diagnostics": ["mcm_request must be a dictionary."], "unresolved": []}

    equations = mcm_request.get("equations")
    variables = mcm_request.get("variables")
    if not isinstance(equations, list) or not isinstance(variables, dict):
        return {"ok": True, "diagnostics": [], "unresolved": []}

    diagnostics = []
    list_normalization = _normalize_list_subscript_variables(mcm_request, repair=repair)
    diagnostics.extend(list_normalization.get("diagnostics") or [])
    unresolved = []
    variable_meta = _extract_variable_metadata(mcm_request)
    known_names = _initial_preflight_known_names(mcm_request)
    known_names.update(_expected_equation_output_names(equations))
    known_units = {
        str(name): normalize_unit(meta.get("unit"))
        for name, meta in variable_meta.items()
    }
    known_units.update(_input_constant_preflight_units(mcm_request))
    equation_lhs_by_name = _infer_equation_lhs_reference_map(equations)

    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        if not expression:
            continue
        normalized_expression, normalization_diagnostic, _ = _normalize_equation_assignment(equation, expression)
        if normalization_diagnostic:
            diagnostics.append(normalization_diagnostic)
        if normalized_expression:
            expression = normalized_expression
        parsed = _split_assignment(expression)
        if not parsed:
            continue

        lhs, rhs = parsed
        try:
            references = sorted(_collect_names(rhs))
        except Exception:
            logger.exception("MCM preflight variable-reference validation failed.")
            diagnostics.append(
                f"Preflight skipped variable-reference validation for equation {index} "
                "because parsing failed."
            )
            known_names.add(lhs)
            known_units.setdefault(lhs, _unit_from_name_suffix(lhs))
            continue

        replacements = {}
        for reference in references:
            if reference in known_names:
                continue
            alias = _resolve_safe_variable_alias(reference, known_names, known_units)
            if alias:
                replacements[reference] = alias
                diagnostics.append(
                    f"Resolved undefined variable {reference} to {alias} using compatible unit "
                    f"{_alias_unit_label(reference, alias, known_units)}."
                )
                continue

            suggestion = _suggest_variable_name(reference, known_names)
            _append_preflight_unresolved(
                unresolved,
                diagnostics,
                location=_equation_name(equation, index),
                expression=expression,
                variable=reference,
                known_names=known_names,
                suggestion=suggestion,
                suggested_missing_lhs=_suggest_missing_lhs(reference, equation_lhs_by_name, index),
            )

        if repair and replacements:
            repaired_rhs = _replace_expression_names(rhs, replacements)
            repaired_expression = f"{lhs} = {repaired_rhs}"
            if isinstance(equation, dict):
                equation["expression"] = repaired_expression
            else:
                equations[index - 1] = repaired_expression
            expression = repaired_expression

        known_names.add(lhs)
        known_units.setdefault(lhs, _unit_from_name_suffix(lhs))

    if strict:
        _validate_requested_output_references(
            mcm_request,
            known_names,
            unresolved,
            diagnostics,
            equation_lhs_by_name,
        )
        _validate_dependency_order_references(
            mcm_request,
            known_names,
            unresolved,
            diagnostics,
            equation_lhs_by_name,
        )
        _validate_constraint_and_selection_references(
            mcm_request,
            known_names,
            unresolved,
            diagnostics,
            equation_lhs_by_name,
        )

    return {
        "ok": not unresolved,
        "diagnostics": diagnostics,
        "unresolved": unresolved,
    }


def _initial_preflight_known_names(mcm_request):
    known = set()
    for field in ("variables", "inputs", "constants"):
        raw = mcm_request.get(field) if isinstance(mcm_request, dict) else None
        if isinstance(raw, dict):
            known.update(str(name) for name in raw)
    return known


def _input_constant_preflight_units(mcm_request):
    units = {}
    for field in ("inputs", "constants"):
        raw = mcm_request.get(field) if isinstance(mcm_request, dict) else None
        if not isinstance(raw, dict):
            continue
        for name, value in raw.items():
            unit = None
            if isinstance(value, dict):
                unit = value.get("unit")
            if unit not in (None, ""):
                units[str(name)] = normalize_unit(unit)
                continue
            suffix_unit = _unit_from_name_suffix(name)
            if suffix_unit:
                units[str(name)] = normalize_unit(suffix_unit)
    return units


def _infer_equation_lhs_reference_map(equations):
    result = {}
    if not isinstance(equations, list):
        return result
    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if parsed:
            lhs, _ = parsed
            result.setdefault(lhs, []).append({
                "equation": _equation_name(equation, index),
                "index": index,
                "source": "expression_lhs",
            })
            continue
        if not isinstance(equation, dict):
            continue
        for field in ("lhs", "output", "target", "result", "name"):
            raw_value = equation.get(field)
            if not isinstance(raw_value, str):
                continue
            candidate = raw_value.strip()
            if _is_safe_variable_name(candidate):
                result.setdefault(candidate, []).append({
                    "equation": _equation_name(equation, index),
                    "index": index,
                    "source": f"equation.{field}",
                })
    return result


def _suggest_missing_lhs(reference, equation_lhs_by_name, current_index=None):
    matches = equation_lhs_by_name.get(str(reference)) or []
    if not matches:
        return None
    later = [item for item in matches if current_index is not None and item.get("index", 0) > current_index]
    if later:
        first = later[0]
        return (
            f"{reference} is defined later by {first.get('equation')}; move that equation before first use "
            "or define an earlier equation LHS."
        )
    first = matches[0]
    return (
        f"Check the equation for {reference}: {first.get('source')} indicates this may be the intended LHS, "
        "but it was not available at the reference point."
    )


def _append_preflight_unresolved(
    unresolved,
    diagnostics,
    *,
    location,
    expression,
    variable,
    known_names,
    suggestion=None,
    suggested_missing_lhs=None,
    code=None,
):
    known_sorted = sorted(str(name) for name in known_names)
    location_text = str(location or "")
    diagnostic_code = code or "undefined_dependency_variable"
    unsafe_candidate_suggestion = _candidate_suggestion_changes_identity(variable, suggestion)
    if unsafe_candidate_suggestion:
        diagnostic_code = "unsafe_cross_candidate_resolution_rejected"
    if location_text == "requested_output":
        message = f"Requested output is not traceable to an input or equation LHS: {variable}."
    elif location_text == "dependency_order":
        message = f"Dependency order references undefined variable {variable}."
    elif location_text.startswith("constraint") or "selection" in location_text or "metric" in location_text or "ranking" in location_text:
        message = f"Expression references undefined variable {variable}."
    else:
        message = f"Equation references undefined variable {variable}."
    if unsafe_candidate_suggestion:
        message += (
            f" unsafe_cross_candidate_resolution_rejected: Did not resolve to {suggestion} because "
            f"candidate identity would change from {_candidate_identity_display(unsafe_candidate_suggestion[0])} "
            f"to {_candidate_identity_display(unsafe_candidate_suggestion[1])}."
        )
    elif suggestion:
        message += f" Did you mean {suggestion}?"
    if suggested_missing_lhs:
        message += f" Suggested missing LHS: {suggested_missing_lhs}"
    message += " Known variables available at that point: " + _format_known_variables_for_message(known_sorted) + "."
    unresolved.append({
        "code": diagnostic_code,
        "equation": location,
        "expression": expression,
        "variable": variable,
        "suggestion": None if unsafe_candidate_suggestion else suggestion,
        "unsafe_suggestion": suggestion if unsafe_candidate_suggestion else None,
        "suggested_missing_lhs": suggested_missing_lhs,
        "known_variables_available": known_sorted,
        "message": message,
    })
    diagnostics.append(message)


def _format_known_variables_for_message(known_names, limit=60):
    if not known_names:
        return "(none)"
    shown = list(known_names[:limit])
    suffix = "" if len(known_names) <= limit else f", ... ({len(known_names)} total)"
    return ", ".join(shown) + suffix


def _candidate_suggestion_changes_identity(variable, suggestion):
    if not suggestion:
        return None
    variable_identity = _candidate_identity_from_name(variable)
    suggestion_identity = _candidate_identity_from_name(suggestion)
    if variable_identity and suggestion_identity and variable_identity != suggestion_identity:
        return variable_identity, suggestion_identity
    return None


def _validate_requested_output_references(mcm_request, known_names, unresolved, diagnostics, equation_lhs_by_name):
    requested = []
    solve_for = mcm_request.get("solve_for")
    if isinstance(solve_for, list):
        requested.extend(str(name) for name in solve_for if str(name).strip())
    requested_output = mcm_request.get("requested_output")
    if isinstance(requested_output, str) and requested_output.strip():
        requested.append(requested_output.strip())

    for output_name in requested:
        if output_name in known_names:
            continue
        _append_preflight_unresolved(
            unresolved,
            diagnostics,
            location="requested_output",
            expression=output_name,
            variable=output_name,
            known_names=known_names,
            suggestion=_suggest_variable_name(output_name, known_names),
            suggested_missing_lhs=_suggest_missing_lhs(output_name, equation_lhs_by_name),
        )


def _validate_dependency_order_references(mcm_request, known_names, unresolved, diagnostics, equation_lhs_by_name):
    dependency_order = mcm_request.get("dependency_order")
    if not isinstance(dependency_order, list):
        return
    for item in dependency_order:
        name = str(item).strip()
        if not name or name in known_names:
            continue
        _append_preflight_unresolved(
            unresolved,
            diagnostics,
            location="dependency_order",
            expression=name,
            variable=name,
            known_names=known_names,
            suggestion=_suggest_variable_name(name, known_names),
            suggested_missing_lhs=_suggest_missing_lhs(name, equation_lhs_by_name),
        )


def _validate_constraint_and_selection_references(mcm_request, known_names, unresolved, diagnostics, equation_lhs_by_name):
    for location, expression in _iter_preflight_reference_expressions(mcm_request):
        _trace_preflight_expression_references(
            location,
            expression,
            known_names,
            unresolved,
            diagnostics,
            equation_lhs_by_name,
        )


def _iter_preflight_reference_expressions(mcm_request):
    constraints = mcm_request.get("constraints")
    if isinstance(constraints, list):
        for index, constraint in enumerate(constraints, start=1):
            location = f"constraint_{index}"
            if isinstance(constraint, dict):
                for field in ("expression", "lhs", "rhs", "condition", "metric"):
                    value = constraint.get(field)
                    if isinstance(value, str) and value.strip():
                        yield f"{location}.{field}", value.strip()
            elif isinstance(constraint, str) and not _is_constraint_policy_note(constraint):
                yield location, constraint.strip()

    for field in (
        "rankings",
        "ranking",
        "candidate_selection_logic",
        "candidate_selection",
        "selection_logic",
        "report_metrics",
        "metrics",
    ):
        value = mcm_request.get(field)
        yield from _iter_preflight_field_expressions(field, value)


def _iter_preflight_field_expressions(location, value):
    if isinstance(value, str) and value.strip():
        yield location, value.strip()
    elif isinstance(value, list):
        for index, item in enumerate(value, start=1):
            yield from _iter_preflight_field_expressions(f"{location}_{index}", item)
    elif isinstance(value, dict):
        for key, item in value.items():
            child_location = f"{location}.{key}"
            if isinstance(item, str) and str(key).lower() in {
                "expression",
                "condition",
                "metric",
                "score",
                "ranking",
                "rank",
                "selector",
                "selection",
                "lhs",
                "rhs",
                "value",
            }:
                yield child_location, item.strip()
            elif isinstance(item, (dict, list)):
                yield from _iter_preflight_field_expressions(child_location, item)


def _trace_preflight_expression_references(
    location,
    expression,
    known_names,
    unresolved,
    diagnostics,
    equation_lhs_by_name,
):
    parsed = _split_assignment(expression)
    trace_expression = parsed[1] if parsed else expression
    try:
        references = sorted(_collect_names(trace_expression))
    except Exception:
        return
    for reference in references:
        if reference in known_names:
            continue
        _append_preflight_unresolved(
            unresolved,
            diagnostics,
            location=location,
            expression=expression,
            variable=reference,
            known_names=known_names,
            suggestion=_suggest_variable_name(reference, known_names),
            suggested_missing_lhs=_suggest_missing_lhs(reference, equation_lhs_by_name),
        )


def _normalize_list_subscript_variables(mcm_request, repair=True):
    if not repair or not isinstance(mcm_request, dict):
        return {"diagnostics": []}

    equations = mcm_request.get("equations")
    variables = mcm_request.get("variables")
    if not isinstance(equations, list) or not isinstance(variables, dict):
        return {"diagnostics": []}

    list_specs = _declared_list_variable_specs(variables)
    if not list_specs:
        return {"diagnostics": []}

    diagnostics = []
    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        if not expression:
            continue

        normalized = _rewrite_list_subscripts_in_expression(expression, list_specs, variables)
        if not normalized.get("rewritten"):
            diagnostics.extend(normalized.get("diagnostics") or [])
            continue

        new_expression = normalized["expression"]
        if isinstance(equation, dict):
            equation["expression"] = new_expression
        else:
            equations[index - 1] = new_expression

        for scalar_name, scalar_meta in normalized.get("created_variables", {}).items():
            if scalar_name not in variables:
                variables[scalar_name] = scalar_meta

        diagnostics.append(
            f"Normalized list subscript expression in equation {_equation_name(equation, index)} "
            "by expanding declared list options into scalar variables."
        )
        diagnostics.extend(normalized.get("diagnostics") or [])

    return {"diagnostics": diagnostics}


def _declared_list_variable_specs(variables):
    specs = {}
    for name, meta in variables.items():
        raw_value = meta.get("value") if isinstance(meta, dict) else meta
        if isinstance(raw_value, (list, tuple)) and _is_safe_variable_name(str(name)):
            specs[str(name)] = {
                "values": list(raw_value),
                "meta": meta if isinstance(meta, dict) else {"value": raw_value},
            }
    return specs


def _rewrite_list_subscripts_in_expression(expression, list_specs, variables):
    try:
        normalized_expression = _normalize_boolean_operators(expression)
        tree = ast.parse(normalized_expression, mode="exec")
    except SyntaxError:
        return {"rewritten": False, "diagnostics": []}

    normalizer = _ListSubscriptScalarizer(list_specs, variables)
    rewritten_tree = normalizer.visit(tree)
    if not normalizer.replacements:
        return {"rewritten": False, "diagnostics": normalizer.diagnostics}

    ast.fix_missing_locations(rewritten_tree)
    try:
        rewritten_expression = ast.unparse(rewritten_tree).strip()
    except Exception:
        return {
            "rewritten": False,
            "diagnostics": ["List subscript normalization was identified but could not be rendered safely."],
        }

    return {
        "rewritten": True,
        "expression": rewritten_expression,
        "created_variables": normalizer.created_variables,
        "diagnostics": normalizer.diagnostics,
    }


class _ListSubscriptScalarizer(ast.NodeTransformer):
    def __init__(self, list_specs, variables):
        self.list_specs = list_specs
        self.variables = variables
        self.replacements = {}
        self.created_variables = {}
        self.diagnostics = []
        self._reported = set()

    def visit_Subscript(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in self.list_specs:
            base_name = node.value.id
            index = _literal_list_subscript_index(node.slice)
            if index is None:
                self._diagnostic_once(
                    ("non_literal", base_name),
                    f"Left unsupported subscript {base_name}[...] unchanged because the index is not a literal non-negative integer.",
                )
                return self.generic_visit(node)

            values = self.list_specs[base_name]["values"]
            if index >= len(values):
                self._diagnostic_once(
                    ("out_of_range", base_name, index),
                    f"Left unsupported subscript {base_name}[{index}] unchanged because the index is out of range.",
                )
                return self.generic_visit(node)

            scalar_name = f"{base_name}_{index}"
            if not _is_safe_variable_name(scalar_name):
                self._diagnostic_once(
                    ("unsafe_scalar", scalar_name),
                    f"Left unsupported subscript {base_name}[{index}] unchanged because scalar name {scalar_name} is unsafe.",
                )
                return self.generic_visit(node)

            scalar_meta = _scalarized_list_variable_meta(
                base_name,
                index,
                self.list_specs[base_name]["meta"],
                values[index],
            )
            if scalar_name in self.variables and not _variable_meta_value_equivalent(self.variables[scalar_name], scalar_meta):
                self._diagnostic_once(
                    ("collision", scalar_name),
                    f"Left unsupported subscript {base_name}[{index}] unchanged because scalar variable {scalar_name} already exists with a different value.",
                )
                return self.generic_visit(node)

            self.replacements[(base_name, index)] = scalar_name
            self.created_variables.setdefault(scalar_name, scalar_meta)
            return ast.copy_location(ast.Name(id=scalar_name, ctx=ast.Load()), node)

        return self.generic_visit(node)

    def _diagnostic_once(self, key, message):
        if key in self._reported:
            return
        self._reported.add(key)
        self.diagnostics.append(message)


def _literal_list_subscript_index(node):
    if hasattr(ast, "Index") and isinstance(node, ast.Index):
        node = node.value
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return node.value if node.value >= 0 else None
    return None


def _scalarized_list_variable_meta(base_name, index, base_meta, element):
    if isinstance(element, dict):
        element_value = element.get("value")
        element_unit = element.get("unit")
        element_source = element.get("source")
        element_description = element.get("description")
    else:
        element_value = element
        element_unit = None
        element_source = None
        element_description = None

    unit = element_unit
    source = element_source
    if isinstance(base_meta, dict):
        unit = unit if unit not in (None, "") else base_meta.get("unit")
        source = source or base_meta.get("source")

    return {
        "value": element_value,
        "unit": unit if unit not in (None, "") else "dimensionless",
        "description": element_description or f"Scalarized list option {base_name}[{index}] for MCM-safe expression evaluation.",
        "source": source or "document-derived",
    }


def _variable_meta_value_equivalent(existing_meta, new_meta):
    existing_value = existing_meta.get("value") if isinstance(existing_meta, dict) else existing_meta
    existing_unit = existing_meta.get("unit") if isinstance(existing_meta, dict) else None
    new_value = new_meta.get("value") if isinstance(new_meta, dict) else new_meta
    new_unit = new_meta.get("unit") if isinstance(new_meta, dict) else None

    existing_known = _known_input_value_for_unit(existing_value, existing_unit)
    new_known = _known_input_value_for_unit(new_value, new_unit)
    if existing_known is _MISSING_INPUT or new_known is _MISSING_INPUT:
        return existing_value == new_value
    if _is_number(existing_known) and _is_number(new_known):
        return math.isclose(float(existing_known), float(new_known), rel_tol=1e-12, abs_tol=1e-12)
    return existing_known == new_known


def _replace_expression_names(expression, replacements):
    repaired = expression
    for old_name, new_name in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        repaired = re.sub(rf"\b{re.escape(old_name)}\b", new_name, repaired)
    return repaired


def _resolve_safe_variable_alias(reference, known_names, known_units):
    candidates = []
    reference_profile = _alias_name_profile(reference, None)
    for candidate in sorted(known_names):
        candidate_profile = _alias_name_profile(candidate, known_units.get(candidate))
        if _safe_alias_profiles_match(reference_profile, candidate_profile):
            candidates.append((candidate, candidate_profile))

    exact_candidates = [
        (candidate, profile)
        for candidate, profile in candidates
        if reference_profile.get("strict_semantic_set") == profile.get("strict_semantic_set")
    ]
    if len(exact_candidates) == 1:
        return exact_candidates[0][0]
    if len(exact_candidates) > 1:
        return None

    if len(candidates) != 1:
        return None
    return candidates[0][0]


def _alias_name_profile(name, known_unit):
    lowered = str(name or "").strip().lower()
    tokens = [token for token in re.split(r"[_\W]+", lowered) if token]
    option_prefix = _name_option_prefix(tokens)
    candidate_identity = _candidate_identity_from_name(name)
    unit = _unit_from_name_suffix(name)
    if not unit and known_unit:
        unit = normalize_unit(known_unit)
    strict_semantic_tokens = _alias_semantic_tokens(tokens, relaxed=False)
    semantic_tokens = _alias_semantic_tokens(tokens, relaxed=True)
    return {
        "name": str(name),
        "option_prefix": option_prefix,
        "candidate_identity": candidate_identity,
        "unit": normalize_unit(unit) if unit else None,
        "context_set": _alias_context_tokens(tokens),
        "strict_semantic_tokens": strict_semantic_tokens,
        "strict_semantic_set": set(strict_semantic_tokens),
        "semantic_tokens": semantic_tokens,
        "semantic_set": set(semantic_tokens),
    }


def _name_option_prefix(tokens):
    if len(tokens) >= 2 and tokens[0] in {"option", "concept", "candidate"}:
        return f"{tokens[0]}_{tokens[1]}"
    return None


def _alias_semantic_tokens(tokens, relaxed=False):
    unit_tokens = {
        "a", "amp", "amps", "ampere", "amperes",
        "c", "f", "k", "w", "kw", "v", "psi", "scfm", "cfm", "fpm", "gpm",
        "per", "deg", "delta", "dimensionless", "boolean", "string",
    }
    optional_context_tokens = {
        "current", "existing", "estimated", "calculated", "actual",
        "new", "effective", "maximum", "minimum", "max", "min",
        "allowed", "allowable", "required", "target", "value", "val",
    }
    semantic = []
    skip_next = False
    for index, token in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        if token in {"option", "concept", "candidate"} and index == 0 and len(tokens) >= 2:
            skip_next = True
            continue
        if token in unit_tokens:
            continue
        if relaxed and token in optional_context_tokens:
            continue
        semantic.append(token)
    return semantic


def _alias_context_tokens(tokens):
    context_tokens = {
        "current", "existing", "estimated", "calculated", "actual",
        "new", "effective", "maximum", "minimum", "max", "min",
        "allowed", "allowable", "required", "target",
    }
    return {token for token in tokens if token in context_tokens}


def _safe_alias_profiles_match(reference, candidate):
    ref_identity = reference.get("candidate_identity")
    candidate_identity = candidate.get("candidate_identity")
    if ref_identity or candidate_identity:
        if ref_identity != candidate_identity:
            return False

    ref_option = reference.get("option_prefix")
    candidate_option = candidate.get("option_prefix")
    if ref_option or candidate_option:
        if ref_option != candidate_option:
            return False

    limit_tokens = {"maximum", "minimum", "max", "min", "allowed", "allowable", "required", "target"}
    ref_limit_context = (reference.get("context_set") or set()).intersection(limit_tokens)
    candidate_limit_context = (candidate.get("context_set") or set()).intersection(limit_tokens)
    if ref_limit_context and not ref_limit_context.intersection(candidate_limit_context):
        return False
    if candidate_limit_context and not candidate_limit_context.intersection(ref_limit_context):
        return False

    ref_unit = reference.get("unit")
    candidate_unit = candidate.get("unit")
    if ref_unit and candidate_unit and not _units_validation_compatible(ref_unit, candidate_unit):
        return False

    ref_semantic = reference.get("semantic_set") or set()
    candidate_semantic = candidate.get("semantic_set") or set()
    if not ref_semantic or not candidate_semantic:
        return False
    if ref_semantic == candidate_semantic:
        return True
    return ref_semantic.issubset(candidate_semantic) and len(ref_semantic) >= 2


def _alias_unit_label(reference, alias, known_units):
    reference_unit = _unit_from_name_suffix(reference)
    alias_unit = known_units.get(alias) or _unit_from_name_suffix(alias)
    return _display_unit(reference_unit or alias_unit or "unknown")


def _suggest_variable_name(reference, known_names):
    matches = difflib.get_close_matches(str(reference), [str(name) for name in known_names], n=1, cutoff=0.72)
    return matches[0] if matches else None


def _preflight_error_result(mcm_request, preflight):
    diagnostics = list(preflight.get("diagnostics") or [])
    unresolved = preflight.get("unresolved") or []
    missing = sorted({item.get("variable") for item in unresolved if item.get("variable")})
    grouped = _group_preflight_diagnostics_by_code(unresolved)
    if grouped:
        diagnostics = _preflight_group_summary_lines(grouped) + diagnostics
    result = _base_result(
        mcm_request,
        status="needs_human_review",
        message="MCM request structure is malformed or unsafe; deterministic computation was blocked before execution.",
        outputs={},
        diagnostics=diagnostics or ["MCM request preflight found malformed or unsafe equation structure."],
        inputs_used={},
    )
    result["calculation_steps"] = []
    result["equations_executed"] = []
    result["equations_skipped"] = []
    result["equation_normalization_diagnostics"] = []
    result["missing_variables"] = missing
    result["missing_outputs"] = []
    result["unit_validation"] = []
    result["unit_warnings"] = []
    result["invalid_unit_outputs"] = []
    result["preflight_unresolved_variables"] = unresolved
    result["preflight_diagnostic_groups"] = grouped
    return result


def _group_preflight_diagnostics_by_code(unresolved):
    grouped = {}
    for item in unresolved or []:
        code = str(item.get("code") or "undefined_dependency_variable")
        grouped.setdefault(code, []).append(item)
        if code == "rhs_only_equation_unresolved":
            grouped.setdefault("missing_lhs_equation", []).append(item)
    return grouped


def _preflight_group_summary_lines(grouped):
    lines = []
    for code in (
        "missing_lhs_equation",
        "undefined_dependency_variable",
        "unsafe_cross_candidate_resolution_rejected",
        "rhs_only_equation_normalized",
        "rhs_only_equation_unresolved",
    ):
        items = grouped.get(code)
        if not items:
            continue
        variables = sorted({str(item.get("variable")) for item in items if item.get("variable")})
        suffix = ": " + ", ".join(variables) if variables else ""
        lines.append(f"preflight_group:{code}{suffix}")
    for code, items in sorted(grouped.items()):
        if code in {
            "missing_lhs_equation",
            "undefined_dependency_variable",
            "unsafe_cross_candidate_resolution_rejected",
            "rhs_only_equation_normalized",
            "rhs_only_equation_unresolved",
        }:
            continue
        variables = sorted({str(item.get("variable")) for item in items if item.get("variable")})
        suffix = ": " + ", ".join(variables) if variables else ""
        lines.append(f"preflight_group:{code}{suffix}")
    return lines


def _dependency_ordered_equations(mcm_request, equations):
    indexed = []
    lhs_positions = {}
    for index, equation in enumerate(equations or [], start=1):
        lhs, rhs = _normalized_equation_lhs_rhs(equation)
        position = len(indexed)
        indexed.append({
            "index": index,
            "equation": equation,
            "lhs": lhs,
            "rhs": rhs,
        })
        if lhs:
            lhs_positions.setdefault(lhs, []).append(position)

    if len(indexed) < 2:
        return [(entry["index"], entry["equation"]) for entry in indexed], []

    unique_lhs_positions = {
        lhs: positions[0]
        for lhs, positions in lhs_positions.items()
        if len(positions) == 1
    }
    dependency_order = _dependency_order_priority(mcm_request)
    dependencies = {}
    dependents = {}
    for position, entry in enumerate(indexed):
        rhs = entry.get("rhs")
        if not rhs:
            dependencies[position] = set()
            continue
        try:
            references = _collect_names(rhs)
        except Exception:
            dependencies[position] = set()
            continue
        entry_dependencies = {
            unique_lhs_positions[reference]
            for reference in references
            if reference in unique_lhs_positions and unique_lhs_positions[reference] != position
        }
        dependencies[position] = entry_dependencies
        for dependency in entry_dependencies:
            dependents.setdefault(dependency, set()).add(position)

    def sort_key(position):
        lhs = indexed[position].get("lhs")
        if lhs in dependency_order:
            return 0, dependency_order[lhs], indexed[position]["index"]
        return 1, indexed[position]["index"], indexed[position]["index"]

    ordered_positions = []
    emitted = set()
    ready = [position for position, deps in dependencies.items() if not deps]
    while ready:
        ready.sort(key=sort_key)
        position = ready.pop(0)
        if position in emitted:
            continue
        emitted.add(position)
        ordered_positions.append(position)
        for dependent in dependents.get(position, set()):
            dependencies[dependent].discard(position)
            if not dependencies[dependent]:
                ready.append(dependent)

    diagnostics = []
    if len(ordered_positions) != len(indexed):
        remaining = [position for position in range(len(indexed)) if position not in emitted]
        ordered_positions.extend(remaining)
        diagnostics.append(
            "Equation dependency ordering left cyclic or ambiguous equations in original order for normal missing-variable handling."
        )

    if ordered_positions != list(range(len(indexed))):
        diagnostics.append(
            "Reordered equations by RHS dependencies/dependency_order so computed-list and selector equations execute after their inputs."
        )

    return [(indexed[position]["index"], indexed[position]["equation"]) for position in ordered_positions], diagnostics


def _normalized_equation_lhs_rhs(equation):
    expression = _equation_expression(equation)
    if not expression:
        return None, None
    normalized_expression, _, _ = _normalize_equation_assignment(equation, expression)
    parsed = _split_assignment(normalized_expression or expression)
    if not parsed:
        return None, None
    return parsed


def _dependency_order_priority(mcm_request):
    dependency_order = mcm_request.get("dependency_order") if isinstance(mcm_request, dict) else None
    if not isinstance(dependency_order, list):
        return {}
    priority = {}
    for index, item in enumerate(dependency_order):
        name = str(item).strip()
        if name and name not in priority:
            priority[name] = index
    return priority


def _candidate_score_aggregation_diagnostics(mcm_request, env, equations, equation_for):
    placeholder_lists = _declared_all_null_list_variables(mcm_request)
    if not placeholder_lists:
        return []

    computed_scores = _computed_non_null_candidate_score_names(env, equation_for)
    if not computed_scores:
        return []

    equation_lhs_names = _expected_equation_output_names(equations)
    helper_uses = _selection_helper_placeholder_list_uses(equations, set(placeholder_lists))
    diagnostics = []
    for list_name in sorted(placeholder_lists):
        if list_name in equation_lhs_names:
            continue
        if list_name not in helper_uses:
            continue
        if not _is_all_null_list(env.get(list_name)):
            continue
        shown_scores = computed_scores[:8]
        suffix = "" if len(computed_scores) <= len(shown_scores) else f", ... ({len(computed_scores)} total)"
        diagnostics.append({
            "code": "candidate_score_list_not_populated",
            "status": "selection_aggregation_incomplete",
            "list_variable": list_name,
            "helper_functions": sorted(helper_uses.get(list_name) or []),
            "computed_candidate_scores": computed_scores,
            "message": (
                f"candidate_score_list_not_populated: {list_name} is an all-null static list used by "
                f"{', '.join(sorted(helper_uses.get(list_name) or []))}, but computed non-null candidate "
                f"score variables exist ({', '.join(shown_scores)}{suffix}). Define an explicit list "
                "equation from those score variables before selecting a best candidate."
            ),
        })
    return diagnostics


def _declared_all_null_list_variables(mcm_request):
    variables = mcm_request.get("variables") if isinstance(mcm_request, dict) else None
    if not isinstance(variables, dict):
        return {}
    placeholders = {}
    for name, meta in variables.items():
        raw_value = meta.get("value") if isinstance(meta, dict) else meta
        if not _is_all_null_list(raw_value):
            continue
        placeholders[str(name)] = {
            "description": str(meta.get("description") or "") if isinstance(meta, dict) else "",
        }
    return placeholders


def _selection_helper_placeholder_list_uses(equations, placeholder_names):
    helper_names = {
        "min_ignore_null",
        "max_ignore_null",
        "argmin_label_ignore_null",
        "argmax_label_ignore_null",
        "value_for_label_ignore_null",
    }
    uses = {}
    if not placeholder_names:
        return uses
    for equation in equations or []:
        lhs, rhs = _normalized_equation_lhs_rhs(equation)
        if not rhs:
            continue
        try:
            tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id not in helper_names:
                continue
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in placeholder_names:
                    uses.setdefault(arg.id, set()).add(node.func.id)
    return uses


def _computed_non_null_candidate_score_names(env, equation_for):
    names = []
    for name in sorted(equation_for):
        value = env.get(name)
        if is_missing_value(value):
            continue
        if _coerce_number(value) is None:
            continue
        if _looks_like_candidate_score_variable(name):
            names.append(name)
    return names


def _looks_like_candidate_score_variable(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return False
    tokens = {token for token in re.split(r"[^a-z0-9]+", lowered) if token}
    if not tokens.intersection({"candidate", "config", "configuration", "option", "concept", "alternative"}):
        return False
    if tokens.intersection({"best", "selected", "recommended", "overall"}):
        return False
    return "score" in tokens or "cost" in tokens


def _is_all_null_list(value):
    return isinstance(value, (list, tuple)) and bool(value) and all(is_missing_value(item) for item in value)


def _process_equation_plan(mcm_request, inputs, router_diagnostics=None):
    preflight = preflight_and_repair_mcm_request(mcm_request, repair=True)
    if not preflight.get("ok"):
        return _preflight_error_result(mcm_request, preflight)

    equations = mcm_request.get("equations") or []
    solve_for = mcm_request.get("solve_for")
    if not isinstance(solve_for, list):
        solve_for = []

    env = dict(inputs)
    declared_variables = _declared_variable_names(mcm_request) | _nullable_missing_equation_output_names(
        mcm_request,
        equations,
    )
    ordered_equations, equation_ordering_diagnostics = _dependency_ordered_equations(
        mcm_request,
        equations,
    )
    variable_meta = _extract_variable_metadata(mcm_request)
    if "any_unknown_required_input" not in env:
        env["any_unknown_required_input"] = False
        variable_meta["any_unknown_required_input"] = {
            "unit": "boolean",
            "unit_declared": True,
            "description": "Internal MCM flag: true when required source inputs are missing.",
            "source": "computed",
        }
    equation_for = {}
    steps = []
    executed = []
    skipped = []
    missing_variables = set()
    unsupported = []
    unit_validation = []
    unit_warnings = []
    invalid_unit_variables = set()
    equation_normalization_diagnostics = []

    for index, equation in ordered_equations:
        name = _equation_name(equation, index)
        expression = _equation_expression(equation)
        purpose = _equation_purpose(equation)

        if not expression:
            skipped.append({
                "equation": name,
                "reason": "Equation has no expression.",
            })
            continue

        normalized_expression, normalization_diagnostic, normalization_skip_reason = _normalize_equation_assignment(
            equation,
            expression,
        )
        if normalization_diagnostic:
            equation_normalization_diagnostics.append(normalization_diagnostic)
        if normalized_expression:
            expression = normalized_expression

        parsed = _split_assignment(expression)
        if not parsed:
            skipped.append({
                "equation": name,
                "expression": expression,
                "reason": normalization_skip_reason
                          or "Only equations of the form '<single_variable> = <safe_expression>' are supported.",
            })
            continue

        lhs, rhs = parsed

        inputs_used = sorted(_collect_names(rhs))
        unit_variables = _current_variable_units(variable_meta)
        unit_value = _evaluate_units_rhs(rhs, unit_variables)
        if not unit_value and _looks_like_unit_output(lhs):
            unit_value = _evaluate_unit_literal_rhs(rhs)

        if unit_value:
            unit_check = unit_value["unit_validation"]
            unit_check.update({
                "equation_name": name,
                "expression": expression,
                "lhs": lhs,
            })

            result = unit_value["value"]
            env[lhs] = result
            equation_for[lhs] = name
            variable_meta.setdefault(lhs, {})
            variable_meta[lhs]["source"] = "computed"
            variable_meta[lhs]["equation"] = name
            if not variable_meta[lhs].get("unit_declared"):
                variable_meta[lhs]["unit"] = "unit_expression"
            variable_meta[lhs]["unit_validation"] = unit_check

            unit_validation.append(unit_check)
            if unit_check.get("status") in {"unknown", "warning", "invalid"}:
                unit_warnings.append(unit_check.get("message", "Unit validation was inconclusive."))

            step = {
                "equation": name,
                "expression": expression,
                "lhs": lhs,
                "rhs": rhs,
                "inputs_used": {key: env[key] for key in inputs_used if key in env},
                "result": result,
                "purpose": purpose,
                "unit_validation": unit_check,
            }
            steps.append(step)
            executed.append(name)
            continue

        dimensional_check = _evaluate_dimensional_check_rhs(rhs, unit_variables)

        if dimensional_check:
            unit_check = dimensional_check["unit_validation"]
            unit_check.update({
                "equation_name": name,
                "expression": expression,
                "lhs": lhs,
            })

            result = dimensional_check["value"]
            env[lhs] = result
            equation_for[lhs] = name
            variable_meta.setdefault(lhs, {})
            variable_meta[lhs]["source"] = "computed"
            variable_meta[lhs]["equation"] = name
            variable_meta[lhs]["unit"] = "boolean"
            variable_meta[lhs]["unit_validation"] = unit_check

            unit_validation.append(unit_check)
            if unit_check.get("status") in {"unknown", "warning", "invalid"}:
                unit_warnings.append(unit_check.get("message", "Unit validation was inconclusive."))

            step = {
                "equation": name,
                "expression": expression,
                "lhs": lhs,
                "rhs": rhs,
                "inputs_used": {key: env[key] for key in inputs_used if key in env},
                "result": result,
                "purpose": purpose,
                "unit_validation": unit_check,
            }
            steps.append(step)
            executed.append(name)
            continue

        unit_check = validate_equation_units(lhs, rhs, unit_variables, names=env)
        unit_check.update({
            "equation_name": name,
            "expression": expression,
            "lhs": lhs,
        })

        invalid_dependencies = sorted(set(inputs_used).intersection(invalid_unit_variables))
        if invalid_dependencies and unit_check.get("status") != "valid":
            unit_check = {
                "equation_name": name,
                "expression": expression,
                "lhs": lhs,
                "lhs_expected_unit": unit_check.get("lhs_expected_unit"),
                "lhs_expected_unit_source": unit_check.get("lhs_expected_unit_source"),
                "lhs_expected_unit_raw": unit_check.get("lhs_expected_unit_raw"),
                "rhs_inferred_unit": unit_check.get("rhs_inferred_unit"),
                "status": "invalid",
                "severity": "warning",
                "message": "Equation depends on variables with invalid unit validation: "
                           + ", ".join(invalid_dependencies),
            }

        unit_validation.append(unit_check)

        try:
            result = _safe_eval(rhs, env, declared_variables)
        except KeyError as e:
            missing = str(e.args[0])
            missing_variables.add(missing)
            skipped.append({
                "equation": name,
                "expression": expression,
                "reason": f"Missing numeric variable: {missing}",
            })
            continue
        except Exception:
            logger.exception("MCM safe expression evaluation failed.")
            unsupported.append({
                "equation": name,
                "expression": expression,
                "reason": "Expression could not be evaluated safely.",
            })
            skipped.append({
                "equation": name,
                "expression": expression,
                "reason": "Unsupported expression.",
            })
            continue

        _apply_value_based_unit_validation(lhs, result, unit_check, variable_meta)
        if unit_check.get("status") in {"unknown", "warning", "invalid"}:
            unit_warnings.append(unit_check.get("message", "Unit validation was inconclusive."))
        if unit_check.get("status") == "invalid":
            invalid_unit_variables.add(lhs)

        env[lhs] = result
        equation_for[lhs] = name
        variable_meta.setdefault(lhs, {})
        variable_meta[lhs]["source"] = "computed"
        variable_meta[lhs]["equation"] = name
        variable_meta[lhs]["unit_validation"] = unit_check
        inferred_unit = unit_check.get("rhs_inferred_unit")
        if _should_assign_inferred_unit(lhs, variable_meta[lhs], inferred_unit):
            variable_meta[lhs]["unit"] = inferred_unit

        step = {
            "equation": name,
            "expression": expression,
            "lhs": lhs,
            "rhs": rhs,
            "inputs_used": {key: env[key] for key in inputs_used if key in env},
            "result": result,
            "purpose": purpose,
            "unit_validation": unit_check,
        }
        steps.append(step)
        executed.append(name)

    handled_constraint_result = post_process_layer6_constraints(
        mcm_request,
        env,
        variable_meta,
        equation_for,
        steps,
        unit_validation,
    )
    handled_constraint_outputs = handled_constraint_result.get("outputs", set())
    if handled_constraint_outputs:
        skipped = [
            item for item in skipped
            if _skipped_lhs(item.get("expression")) not in handled_constraint_outputs
        ]
        unsupported = [
            item for item in unsupported
            if _skipped_lhs(item.get("expression")) not in handled_constraint_outputs
        ]
        unit_validation = [
            item for item in unit_validation
            if not (
                item.get("lhs") in handled_constraint_outputs
                and item.get("status") in {"unknown", "warning", "invalid"}
            )
        ]
        unit_warnings = [
            item.get("message", "Unit validation was inconclusive.")
            for item in unit_validation
            if item.get("status") in {"unknown", "warning", "invalid"}
        ]
        missing_variables.difference_update(handled_constraint_result.get("missing_variables", set()))
        missing_variables.difference_update(handled_constraint_result.get("ignored_variables", set()))
        invalid_unit_variables.difference_update(handled_constraint_outputs)

    derived_selection_outputs = _derive_solve_problem_selection_outputs(
        mcm_request,
        env,
        variable_meta,
        equation_for,
    )

    outputs = {}
    missing_outputs = []
    for name in solve_for:
        output_name = str(name)
        if output_name in env:
            outputs[output_name] = _build_output(output_name, env[output_name], variable_meta, equation_for)
        else:
            missing_outputs.append(output_name)

    if not solve_for:
        for name in equation_for:
            outputs[name] = _build_output(name, env[name], variable_meta, equation_for)

    for name in derived_selection_outputs:
        if name in env and name not in outputs:
            outputs[name] = _build_output(name, env[name], variable_meta, equation_for)

    aggregation_diagnostics = _candidate_score_aggregation_diagnostics(
        mcm_request,
        env,
        equations,
        equation_for,
    )

    diagnostics = []
    schema_diagnostics = mcm_request.get("schema_normalization_diagnostics")
    if isinstance(schema_diagnostics, list):
        diagnostics.extend(str(item) for item in schema_diagnostics)
    diagnostics.extend(list(router_diagnostics or []))
    diagnostics.extend(equation_ordering_diagnostics)
    diagnostics.extend(item.get("message") for item in aggregation_diagnostics if item.get("message"))
    diagnostics.extend([
        f"Equations executed: {len(executed)}",
        f"Equations skipped: {len(skipped)}",
    ])

    if executed:
        diagnostics.append("Executed equation names: " + ", ".join(executed))
    if equation_normalization_diagnostics:
        diagnostics.extend(equation_normalization_diagnostics)
    if skipped:
        diagnostics.append("Skipped equations: " + "; ".join(
            f"{item.get('equation')}: {item.get('reason')}" for item in skipped
        ))
    if missing_variables:
        diagnostics.append("Missing variables: " + ", ".join(sorted(missing_variables)))
    if unsupported:
        diagnostics.append("Unsupported expressions: " + "; ".join(
            f"{item.get('equation')}: {item.get('reason')}" for item in unsupported
        ))
    if missing_outputs:
        diagnostics.append("Missing requested outputs: " + ", ".join(missing_outputs))
    if unit_warnings:
        diagnostics.append("Unit validation warnings: " + "; ".join(unit_warnings))
    advisory_missing = mcm_request.get("missing_variables")
    if isinstance(advisory_missing, list) and advisory_missing:
        diagnostics.append("Advisory missing variables not required by executed equations: " + ", ".join(
            str(item) for item in advisory_missing
        ))

    invalid_requested_outputs = sorted(set(str(name) for name in solve_for).intersection(invalid_unit_variables))
    criterion_statuses = _collect_numbered_status_criteria(env, mcm_request)
    criterion_status_policy_block = _criterion_status_policy_block(
        criterion_statuses,
        env,
        mcm_request,
        outputs,
    )

    if missing_variables:
        status = "needs_human_review"
        message = "MCM equation plan is missing required numeric inputs."
    elif aggregation_diagnostics:
        status = "needs_human_review"
        message = "MCM candidate score aggregation is incomplete; no-viable selection cannot be certified."
    elif criterion_status_policy_block:
        status = "needs_human_review"
        message = criterion_status_policy_block
    elif invalid_requested_outputs and len(invalid_requested_outputs) == len(solve_for):
        status = "needs_human_review"
        message = "MCM computed requested outputs, but unit validation found invalid requested output units."
    elif invalid_requested_outputs:
        status = "partial"
        message = "MCM computed outputs, but unit validation found invalid units for some requested outputs."
    elif not executed and skipped:
        status = "unsupported"
        message = "MCM equation plan did not contain any safely executable assignment equations."
    elif missing_outputs and outputs:
        status = "partial"
        message = "MCM equation plan computed some requested outputs, but not all."
    elif missing_outputs:
        status = "needs_human_review"
        message = "MCM equation plan did not compute requested outputs."
    elif skipped:
        status = "partial"
        message = "MCM computed requested outputs, but one or more equations were skipped."
    else:
        status = "computed"
        message = "MCM completed deterministic dependency-ordered equation execution."

    result = _base_result(
        mcm_request,
        status=status,
        message=message,
        outputs=outputs,
        diagnostics=diagnostics,
        inputs_used=inputs,
    )
    result["calculation_steps"] = steps
    result["equations_executed"] = executed
    result["equations_skipped"] = skipped
    result["equation_normalization_diagnostics"] = equation_normalization_diagnostics
    result["missing_variables"] = sorted(missing_variables)
    result["missing_outputs"] = missing_outputs
    result["unit_validation"] = unit_validation
    result["unit_warnings"] = unit_warnings
    result["invalid_unit_outputs"] = invalid_requested_outputs
    result["selection_aggregation_diagnostics"] = aggregation_diagnostics
    result["_constraint_env"] = dict(env)
    result["_constraint_units"] = _current_variable_units(variable_meta)
    return result


def _derive_solve_problem_selection_outputs(mcm_request, env, variable_meta, equation_for):
    if normalize_eas_mode(mcm_request.get("mode") if isinstance(mcm_request, dict) else None) != "solve-problem":
        return []

    exposed = []

    def expose(name):
        if name in env and name not in exposed:
            exposed.append(name)

    def publish(name, value, unit, description):
        if is_missing_value(value):
            return
        if name not in env or is_missing_value(env.get(name)):
            env[name] = value
            meta = variable_meta.setdefault(name, {})
            meta["source"] = "computed"
            meta.setdefault("unit", unit)
            meta.setdefault("description", description)
            equation_for.setdefault(name, "derive_minimum_acceptable_selection")
        expose(name)

    selected_conductor = _first_env_value(env, (
        "selected_conductor_AWG",
        "selected_conductor_awg",
    ))
    selected_power_supply = _first_env_value(env, (
        "selected_power_supply_A",
        "selected_power_supply_rating_A",
        "selected_ps_rating_A",
        "selected_ps_A",
        "selected_ps_amps",
        "selected_power_supply_amps",
    ))
    selected_fuse = _first_env_value(env, (
        "selected_fuse_A",
        "selected_fuse_rating_A",
        "selected_fuse_amps",
    ))

    conductor_candidates = _selection_component_candidates("conductor", mcm_request, env)
    power_supply_candidates = _selection_component_candidates("power_supply", mcm_request, env)
    fuse_candidates = _selection_component_candidates("fuse", mcm_request, env)

    if is_missing_value(selected_conductor):
        selected_conductor = _first_passing_selection_value("conductor", conductor_candidates)
    if is_missing_value(selected_power_supply):
        selected_power_supply = _first_passing_selection_value("power_supply", power_supply_candidates)
    if is_missing_value(selected_fuse):
        selected_fuse = _first_passing_selection_value("fuse", fuse_candidates)

    publish(
        "selected_conductor_AWG",
        selected_conductor,
        "dimensionless",
        "Canonical selected conductor AWG derived from minimum-acceptable option criteria.",
    )
    publish(
        "selected_power_supply_A",
        selected_power_supply,
        "A",
        "Canonical selected power supply rating derived from minimum-acceptable option criteria.",
    )
    publish(
        "selected_fuse_A",
        selected_fuse,
        "A",
        "Canonical selected fuse rating derived from minimum-acceptable option criteria.",
    )

    conductor_pass = _derive_component_selection_pass(
        env,
        selected_conductor,
        conductor_candidates,
        (
            "conductor_selection_pass",
            "overall_conductor_selection_pass",
        ),
    )
    power_supply_pass = _derive_component_selection_pass(
        env,
        selected_power_supply,
        power_supply_candidates,
        (
            "power_supply_selection_pass",
            "ps_selection_pass",
            "overall_power_supply_selection_pass",
            "overall_ps_selection_pass",
        ),
    )
    fuse_pass = _derive_component_selection_pass(
        env,
        selected_fuse,
        fuse_candidates,
        (
            "fuse_selection_pass",
            "overall_fuse_selection_pass",
        ),
    )

    publish(
        "conductor_selection_pass",
        conductor_pass,
        "boolean",
        "Canonical selected conductor pass flag.",
    )
    publish(
        "power_supply_selection_pass",
        power_supply_pass,
        "boolean",
        "Canonical selected power supply pass flag.",
    )
    publish(
        "fuse_selection_pass",
        fuse_pass,
        "boolean",
        "Canonical selected fuse pass flag.",
    )

    component_flags = (conductor_pass, power_supply_pass, fuse_pass)
    overall_release = _first_env_status(env, (
        "overall_release_status",
        "overall_design_pass",
        "selected_design_pass",
        "overall_selection_pass",
    ))
    if overall_release is None:
        if any(value is False for value in component_flags):
            overall_release = "FAIL"
        elif all(value is True for value in component_flags):
            overall_release = "PASS"
    publish(
        "overall_release_status",
        overall_release,
        "status_string",
        "Overall release status derived from selected component pass flags.",
    )

    selected_solution = _selection_composite_solution_label({
        "selected_conductor_AWG": selected_conductor,
        "selected_power_supply_A": selected_power_supply,
        "selected_fuse_A": selected_fuse,
    })
    publish(
        "selected_solution",
        selected_solution,
        "status_string",
        "Canonical selected solve-problem solution summary.",
    )

    selected_solution_pass = _first_env_bool(env, ("selected_solution_pass",))
    if selected_solution_pass is None:
        if selected_solution and all(value is True for value in component_flags):
            selected_solution_pass = True
        elif any(value is False for value in component_flags):
            selected_solution_pass = False
    publish(
        "selected_solution_pass",
        selected_solution_pass,
        "boolean",
        "Canonical selected solve-problem pass flag.",
    )

    selection_status = _first_env_value(env, ("selection_status",))
    if is_missing_value(selection_status):
        if selected_solution and selected_solution_pass is True:
            selection_status = "selection_pass"
        elif selected_solution and selected_solution_pass is False:
            selection_status = "selected_option_failed_criteria"
        elif any(candidates for candidates in (conductor_candidates, power_supply_candidates, fuse_candidates)):
            selection_status = "selection_no_viable_option"
    publish(
        "selection_status",
        selection_status,
        "status_string",
        "Canonical solve-problem selection status.",
    )

    return exposed


def _selection_component_candidates(kind, mcm_request, env):
    expression_by_lhs = _equation_expression_by_lhs(mcm_request)
    order = _selection_name_order(mcm_request, env)
    candidates = []
    for name, raw_value in env.items():
        status = _constraint_status_from_output(raw_value)
        if status.get("passes") not in {True, False}:
            continue
        if not _is_selection_option_criterion_name(kind, name):
            continue
        option_value = _selection_option_value(kind, name, expression_by_lhs.get(str(name)), env)
        if is_missing_value(option_value):
            continue
        candidates.append({
            "name": str(name),
            "value": option_value,
            "passes": status.get("passes"),
            "order": order.get(str(name), len(order)),
        })
    return candidates


def _equation_expression_by_lhs(mcm_request):
    expressions = {}
    equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    if not isinstance(equations, list):
        return expressions
    for equation in equations:
        expression = _equation_expression(equation)
        if not expression:
            continue
        normalized, _, _ = _normalize_equation_assignment(equation, expression)
        parsed = _split_assignment(normalized or expression)
        if parsed:
            expressions[parsed[0]] = normalized or expression
    return expressions


def _selection_name_order(mcm_request, env):
    ordered = []
    equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    if isinstance(equations, list):
        for equation in equations:
            expression = _equation_expression(equation)
            parsed = _split_assignment(expression) if expression else None
            if parsed:
                ordered.append(parsed[0])
    dependency_order = mcm_request.get("dependency_order") if isinstance(mcm_request, dict) else None
    if isinstance(dependency_order, list):
        for item in dependency_order:
            text = str(item or "").strip()
            parsed = _split_assignment(text)
            ordered.append(parsed[0] if parsed else text)
    ordered.extend(str(name) for name in env)
    order = {}
    for index, name in enumerate(ordered):
        order.setdefault(str(name), index)
    return order


def _is_selection_option_criterion_name(kind, name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return False
    if "selected" in lowered or "selection" in lowered or lowered.startswith("overall_"):
        return False
    if not (lowered.endswith("_pass") or lowered.endswith("_check") or "_pass_" in lowered):
        return False
    tokens = _selection_name_tokens(lowered)
    if kind == "conductor":
        return "awg" in tokens or "conductor" in tokens
    if kind == "power_supply":
        return (
            ("power" in tokens and "supply" in tokens)
            or "ps" in tokens
            or "power_supply" in lowered
        )
    if kind == "fuse":
        return "fuse" in tokens
    return False


def _selection_option_value(kind, name, expression, env):
    if kind == "conductor":
        value = _selection_value_from_name(kind, name)
        if not is_missing_value(value):
            return value
        return _selection_option_value_from_expression(kind, expression, env)

    value = _selection_option_value_from_expression(kind, expression, env)
    if not is_missing_value(value):
        return value
    value = _selection_value_from_name(kind, name)
    if not is_missing_value(value):
        return value
    return _selection_indexed_option_value(kind, name, env)


def _selection_option_value_from_expression(kind, expression, env):
    if not isinstance(expression, str) or not expression.strip():
        return None
    parsed = _split_assignment(expression)
    rhs = parsed[1] if parsed else expression
    try:
        names = sorted(_collect_names(rhs))
    except Exception:
        return None
    for candidate in names:
        if not _is_selection_option_variable_name(kind, candidate):
            continue
        value = env.get(candidate)
        if _is_number(value):
            return value
    return None


def _is_selection_option_variable_name(kind, name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return False
    tokens = _selection_name_tokens(lowered)
    excluded = {
        "required",
        "requirement",
        "min",
        "minimum",
        "max",
        "maximum",
        "allowed",
        "allowable",
        "load",
        "demand",
        "drop",
        "voltage",
        "present",
        "pass",
        "check",
        "selected",
    }
    if tokens.intersection(excluded):
        return False
    if kind == "conductor":
        return ("conductor" in tokens or "awg" in tokens) and "awg" in tokens
    if kind == "power_supply":
        return (
            (("power" in tokens and "supply" in tokens) or "ps" in tokens or "power_supply" in lowered)
            and bool(tokens.intersection({"available", "capacity", "rating", "amps", "amp", "a"}))
        )
    if kind == "fuse":
        return (
            "fuse" in tokens
            and bool(tokens.intersection({"available", "capacity", "rating", "amps", "amp", "a"}))
        )
    return False


def _selection_value_from_name(kind, name):
    lowered = str(name or "").strip().lower()
    if kind == "conductor":
        for pattern in (
            r"(?<!\d)(\d+(?:[._]\d+)?)_?awg(?![a-z])",
            r"(?<![a-z])awg_?(\d+(?:[._]\d+)?)(?!\d)",
        ):
            match = re.search(pattern, lowered)
            if match:
                return _selection_number_token(match.group(1))
        return None

    match = re.search(
        r"(?<!\d)(\d+(?:[._]\d+)?)_?(?:a|amp|amps|ampere|amperes)(?![a-z])",
        lowered,
    )
    if match:
        return _selection_number_token(match.group(1))
    return None


def _selection_indexed_option_value(kind, name, env):
    match = re.search(r"(?:^|_)(\d+)(?=_(?:pass|check)|$)", str(name or "").strip().lower())
    if not match:
        return None
    index = match.group(1)
    suffix = f"_{index}"
    matches = []
    for candidate, value in env.items():
        candidate_name = str(candidate)
        if not candidate_name.lower().endswith(suffix):
            continue
        if not _is_selection_option_variable_name(kind, candidate_name):
            continue
        if _is_number(value):
            matches.append((candidate_name, value))
    if len(matches) == 1:
        return matches[0][1]
    return None


def _selection_number_token(value):
    try:
        return float(str(value).replace("_", "."))
    except (TypeError, ValueError):
        return None


def _first_passing_selection_value(kind, candidates):
    passing = [item for item in candidates if item.get("passes") is True]
    if not passing:
        return None
    if kind == "conductor":
        return sorted(
            passing,
            key=lambda item: (-float(item.get("value")), item.get("order", 0)),
        )[0].get("value")
    return sorted(
        passing,
        key=lambda item: (float(item.get("value")), item.get("order", 0)),
    )[0].get("value")


def _derive_component_selection_pass(env, selected_value, candidates, aliases):
    explicit = _first_env_bool(env, aliases)
    if explicit is not None and not is_missing_value(selected_value):
        return explicit
    if is_missing_value(selected_value):
        if candidates and all(item.get("passes") is False for item in candidates):
            return False
        return None
    for item in candidates:
        value = item.get("value")
        if _is_number(value) and _is_number(selected_value):
            if math.isclose(float(value), float(selected_value), rel_tol=1e-12, abs_tol=1e-12):
                return True if item.get("passes") is True else False if item.get("passes") is False else None
        elif value == selected_value:
            return True if item.get("passes") is True else False if item.get("passes") is False else None
    return explicit


def _first_env_value(env, names):
    for name in names:
        value = env.get(name)
        if not is_missing_value(value):
            return value
    return None


def _first_env_bool(env, names):
    for name in names:
        if name not in env:
            continue
        status = _constraint_status_from_output(env.get(name))
        if status.get("recognized") and status.get("passes") is not None:
            return status.get("passes")
    return None


def _first_env_status(env, names):
    for name in names:
        if name not in env:
            continue
        status = _constraint_status_from_output(env.get(name))
        if not status.get("recognized"):
            continue
        if status.get("passes") is True:
            return "PASS"
        if status.get("passes") is False:
            return "FAIL"
    return None


def _selection_name_tokens(name):
    return {token for token in re.split(r"[^a-z0-9]+", str(name or "").lower()) if token}


def _expected_equation_output_names(equations):
    expected = set()
    if not isinstance(equations, list):
        return expected
    for equation in equations:
        expression = _equation_expression(equation)
        if not expression:
            continue
        normalized_expression, _, _ = _normalize_equation_assignment(equation, expression)
        parsed = _split_assignment(normalized_expression or expression)
        if parsed:
            expected.add(parsed[0])
    return expected


def post_process_layer6_constraints(mcm_request, env, variable_meta, equation_for, steps, unit_validation):
    solve_for = mcm_request.get("solve_for")
    if not isinstance(solve_for, list):
        solve_for = []
    requested = {str(name) for name in solve_for}
    target_outputs = {
        "bath_surface_temperature_constraint_status",
        "bath_surface_temperature_margin_C",
        "surface_temperature_constraint_status",
        "surface_temperature_constraint_pass",
        "any_known_constraint_fail",
        "any_constraint_unknown",
        "overall_constraint_status",
        "release_status",
        "overall_release_status",
        "result_status",
        "overall_result_status",
        "overall_selection_status",
        "overall_status",
        "final_status",
    }
    aggregate_status_requested = {name for name in requested if _is_aggregate_status_output(name)}
    if not requested.intersection(target_outputs) and not aggregate_status_requested:
        return {"outputs": set(), "missing_variables": set()}

    handled = set()
    handled_missing = set()
    ignored_variables = set()

    missing_comparator_outputs = _inject_missing_constraint_pass_outputs(
        mcm_request,
        requested,
        env,
        variable_meta,
        equation_for,
        steps,
        unit_validation,
    )
    handled.update(missing_comparator_outputs.get("outputs", set()))
    handled_missing.update(missing_comparator_outputs.get("missing_variables", set()))

    margin_outputs = _inject_missing_constraint_margin_outputs(
        mcm_request,
        requested,
        env,
        variable_meta,
        equation_for,
        steps,
        unit_validation,
    )
    handled.update(margin_outputs.get("outputs", set()))
    handled_missing.update(margin_outputs.get("missing_variables", set()))

    checks = _constraint_checks_for_env(mcm_request, env, variable_meta)
    if "surface_temperature_constraint_pass" in requested and env.get("surface_temperature_constraint_pass") == "unknown":
        _ensure_unknown_surface_constraint_check(checks, env, variable_meta)
    if (
        "bath_surface_temperature_constraint_status" in requested
        or "bath_surface_temperature_margin_C" in requested
        or env.get("bath_surface_temperature_constraint_status") == "unknown"
    ):
        _ensure_unknown_surface_constraint_check(checks, env, variable_meta)

    for status_output in ("surface_temperature_constraint_status", "bath_surface_temperature_constraint_status"):
        if status_output not in requested:
            continue
        surface_check = _find_constraint_check(
            checks,
            {
                "bath_surface_temperature_C",
                "surface_temperature_C",
                "max_safe_surface_temperature_C",
                "max_surface_temperature_C",
            },
        )
        status = _constraint_status_value(surface_check)
        reason = surface_check.get("message") if surface_check else "Surface-temperature constraint was not available."
        _store_computed_env_output(
            env,
            variable_meta,
            equation_for,
            steps,
            unit_validation,
            status_output,
            status,
            "pass_fail_unknown",
            status_output,
            "constraint status from bath surface temperature check",
            reason,
        )
        if status == "unknown" and surface_check:
            missing = sorted(_missing_names_from_constraint_check(surface_check))
            variable_meta[status_output]["status"] = "unknown"
            variable_meta[status_output]["missing_inputs"] = list(missing)
            variable_meta[status_output]["description"] = (
                "Surface-temperature constraint could not be evaluated because required input data is missing."
            )
        handled.add(status_output)

    any_known_fail, any_unknown, overall = compute_overall_constraint_status(checks)
    if "any_known_constraint_fail" in requested:
        _store_computed_env_output(
            env,
            variable_meta,
            equation_for,
            steps,
            unit_validation,
            "any_known_constraint_fail",
            any_known_fail,
            "boolean",
            "any_known_constraint_fail",
            "any evaluated constraint failed",
            "True when at least one known constraint failed.",
        )
        handled.add("any_known_constraint_fail")
    if "any_constraint_unknown" in requested:
        _store_computed_env_output(
            env,
            variable_meta,
            equation_for,
            steps,
            unit_validation,
            "any_constraint_unknown",
            any_unknown,
            "boolean",
            "any_constraint_unknown",
            "any documented engineering constraint is unknown",
            "True when at least one constraint could not be evaluated.",
        )
        handled.add("any_constraint_unknown")
    if "overall_constraint_status" in requested:
        _store_computed_env_output(
            env,
            variable_meta,
            equation_for,
            steps,
            unit_validation,
            "overall_constraint_status",
            overall,
            "pass_fail_unknown",
            "overall_constraint_status",
            "fail if any known fail, else unknown if any unknown, else pass",
            "Overall deterministic constraint status.",
        )
        handled.add("overall_constraint_status")

    for aggregate_status_output in sorted(
        aggregate_status_requested.union({
            "release_status",
            "overall_release_status",
            "result_status",
            "overall_result_status",
            "overall_selection_status",
            "overall_status",
            "final_status",
        })
    ):
        if aggregate_status_output not in requested or aggregate_status_output in env:
            continue
        release_status = _derive_overall_release_status(env, mcm_request)
        if release_status is not None:
            _store_computed_env_output(
                env,
                variable_meta,
                equation_for,
                steps,
                unit_validation,
                aggregate_status_output,
                release_status,
                "status_string",
                aggregate_status_output,
                "derived from evaluated Cn_pass criteria",
                "Release status derived from deterministic constraint criteria.",
            )
            handled.add(aggregate_status_output)

    for expression in _handled_skipped_expressions(mcm_request, handled):
        ignored_variables.update(_collect_names(expression))

    return {
        "outputs": handled,
        "missing_variables": handled_missing,
        "ignored_variables": ignored_variables,
    }


def _inject_missing_constraint_pass_outputs(mcm_request, requested, env, variable_meta, equation_for, steps, unit_validation):
    equations = mcm_request.get("equations")
    if not isinstance(equations, list):
        return {"outputs": set(), "missing_variables": set()}

    handled = set()
    handled_missing = set()
    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        if lhs not in requested and not _is_layer6_surface_constraint_lhs(lhs):
            continue
        if not (lhs.endswith("_constraint_pass") or _is_layer6_surface_constraint_lhs(lhs)):
            continue
        spec = _constraint_spec_from_assignment_rhs(equation, index, lhs, rhs)
        if not spec:
            continue
        check = _evaluate_constraint_spec(spec, env, _current_variable_units(variable_meta))
        if check.get("severity") != "unknown":
            continue
        missing = _missing_inputs_from_constraint_check(check)
        handled_missing.update(missing)
        _store_computed_env_output(
            env,
            variable_meta,
            equation_for,
            steps,
            unit_validation,
            lhs,
            None if lhs.startswith("bath_surface_temperature_") else "unknown",
            "pass_fail_unknown",
            _equation_name(equation, index),
            rhs,
            "Constraint cannot be evaluated because required inputs are missing; result is unknown, not pass.",
        )
        variable_meta[lhs]["status"] = "unknown"
        variable_meta[lhs]["result_status"] = "unknown"
        variable_meta[lhs]["missing_inputs"] = list(missing)
        variable_meta[lhs]["description"] = (
            "Constraint could not be evaluated because required input data is missing."
        )
        variable_meta[lhs]["unit_validation"].update({
            "rhs_inferred_unit": "pass_fail_unknown",
            "status": "valid",
            "severity": "info",
            "message": "Missing-input comparator constraint represented as unknown.",
        })
        handled.add(lhs)
    return {"outputs": handled, "missing_variables": handled_missing}


def _is_layer6_surface_constraint_lhs(lhs):
    return isinstance(lhs, str) and "surface_temperature_constraint" in lhs


def _derive_overall_release_status(env, mcm_request=None):
    status_criteria = _collect_numbered_status_criteria(env, mcm_request)
    if status_criteria:
        max_index = max(status_criteria)
        values = [status_criteria.get(index) for index in range(1, max_index + 1)]
        if any(value is None for value in values):
            return None
        if any(value == "UNKNOWN" for value in values):
            return "UNKNOWN"
        return "PASS" if all(value == "PASS" for value in values) else "FAIL"

    criteria = _collect_numbered_pass_criteria(env, mcm_request)
    if not criteria:
        return None

    max_index = max(criteria)
    if 1 not in criteria:
        return None

    values = [criteria.get(index) for index in range(1, max_index + 1)]
    if any(is_missing_value(value) for value in values):
        return "UNKNOWN"
    if any(not isinstance(value, bool) for value in values):
        return None
    return "PASS" if all(values) else "FAIL"


def _collect_numbered_pass_criteria(env, mcm_request=None):
    criteria = {}
    for name, value in env.items():
        if _is_candidate_specific_criterion_output(name):
            continue
        index = _criterion_output_index(name)
        if index is not None and isinstance(value, bool):
            criteria[index] = value

    variables = mcm_request.get("variables") if isinstance(mcm_request, dict) else None
    if isinstance(variables, dict):
        for name, meta in variables.items():
            if _is_candidate_specific_criterion_output(name):
                continue
            index = _criterion_output_index(name)
            if index is None:
                continue
            if index in criteria:
                continue
            raw_value = meta.get("value") if isinstance(meta, dict) else meta
            known_value = _known_input_value(raw_value)
            if isinstance(known_value, bool):
                criteria[index] = known_value

    return criteria


def _collect_numbered_status_criteria(env, mcm_request=None):
    criteria = {}
    for name, value in env.items():
        if _is_candidate_specific_criterion_output(name):
            continue
        index = _criterion_output_index(name)
        if index is not None:
            status_value = _constraint_status_from_output(value)
            if status_value.get("recognized"):
                criteria[index] = status_value.get("status")

    variables = mcm_request.get("variables") if isinstance(mcm_request, dict) else None
    if isinstance(variables, dict):
        for name, meta in variables.items():
            if _is_candidate_specific_criterion_output(name):
                continue
            index = _criterion_output_index(name)
            if index is None:
                continue
            if index in criteria:
                continue
            raw_value = meta.get("value") if isinstance(meta, dict) else meta
            status_value = _constraint_status_from_output(raw_value)
            if status_value.get("recognized"):
                criteria[index] = status_value.get("status")

    return criteria


def _criterion_status_policy_block(criteria, env, mcm_request=None, outputs=None):
    if not criteria:
        return None
    use_recommendation_policy = _use_suggest_improvements_recommendation_status_policy(
        mcm_request,
        outputs,
    )
    max_index = max(criteria)
    values = [criteria.get(index) for index in range(1, max_index + 1)]
    if any(value is None for value in values):
        missing_indices = [index for index in range(1, max_index + 1) if criteria.get(index) is None]
        if not use_recommendation_policy and not _solve_problem_selection_allows_sparse_criteria(
            mcm_request,
            env,
            outputs,
            values,
            missing_indices,
        ):
            return "MCM criterion status outputs are incomplete or unknown."
        values = [value for value in values if value is not None]
    if any(value not in {"PASS", "FAIL"} for value in values):
        return "MCM criterion status outputs include UNKNOWN results."
    if use_recommendation_policy:
        return None

    release_value = _resolve_canonical_overall_status(env=env, outputs=outputs)
    if release_value is None:
        release_value = _derive_overall_release_status(env, mcm_request)
    if release_value not in {"PASS", "FAIL"}:
        return "MCM criterion status outputs are complete, but release status is not computed or derivable."
    return None


def _resolve_canonical_overall_status(env=None, outputs=None):
    for container in (outputs, env):
        if not isinstance(container, dict):
            continue
        for name in _overall_status_alias_names():
            value = None
            if container is outputs:
                output = _case_insensitive_dict_get(container, name)
                value = _output_value(output)
            else:
                marker = _case_insensitive_dict_get(container, name, missing=_MISSING_INPUT)
                if marker is not _MISSING_INPUT:
                    value = marker
            status = _normalize_status_value(value)
            if status is not None:
                return status
        for name, raw_value in container.items():
            if not _is_aggregate_status_output(name):
                continue
            value = _output_value(raw_value) if container is outputs else raw_value
            status = _normalize_status_value(value)
            if status is not None:
                return status
    return None


def _case_insensitive_dict_get(container, name, missing=None):
    if not isinstance(container, dict):
        return missing
    if name in container:
        return container.get(name)
    lowered = str(name or "").strip().lower()
    for key, value in container.items():
        if str(key or "").strip().lower() == lowered:
            return value
    return missing


def _overall_status_alias_names():
    return (
        "overall_release_status",
        "overall_result_status",
        "overall_selection_status",
        "overall_recommendation_status",
        "release_status",
        "result_status",
        "final_status",
        "overall_status",
        "overall_release_status_string",
        "overall_result_status_string",
        "overall_selection_status_string",
        "overall_recommendation_status_string",
        "release_status_string",
        "result_status_string",
        "final_status_string",
        "overall_status_string",
    )


def _solve_problem_selection_allows_sparse_criteria(mcm_request, env, outputs, values, missing_indices=None):
    if normalize_eas_mode(mcm_request.get("mode") if isinstance(mcm_request, dict) else None) != "solve-problem":
        return False
    known_values = [value for value in values if value is not None]
    if not known_values or any(value not in {"PASS", "FAIL"} for value in known_values):
        return False
    release_value = _solve_problem_release_status_value(env, outputs)
    if release_value not in {"PASS", "FAIL"}:
        return False
    if not _solve_problem_has_selection_workflow_signal(env, outputs):
        return False
    if all(value == "PASS" for value in known_values) and _solve_problem_selected_solution_passes(env, outputs) is True:
        return True
    return _missing_criteria_are_candidate_scoped(missing_indices or [], env, outputs)


def _missing_criteria_are_candidate_scoped(missing_indices, env, outputs):
    missing = {int(index) for index in missing_indices or [] if index is not None}
    if not missing:
        return True
    present = set()
    for container in (env, outputs):
        if not isinstance(container, dict):
            continue
        for name in container:
            index = _criterion_output_index(name)
            if index in missing and _is_candidate_specific_criterion_output(name):
                present.add(index)
    return missing.issubset(present)


def _solve_problem_has_selection_workflow_signal(env, outputs):
    if _solve_problem_selected_solution_passes(env, outputs) is True:
        return True
    release_value = _solve_problem_release_status_value(env, outputs)
    if release_value not in {"PASS", "FAIL"}:
        return False
    for name in (
        "selected_solution_pass",
        "selection_status",
        "overall_selection_status",
        "selected_config_label",
        "selected_configuration_label",
        "selected_option_name",
        "selected_option_label",
        "selected_candidate_name",
    ):
        value = None
        if isinstance(env, dict) and name in env:
            value = env.get(name)
        elif isinstance(outputs, dict):
            value = _output_value(outputs.get(name))
        if not is_missing_value(value):
            return True
    if isinstance(outputs, dict):
        for name, output in outputs.items():
            if _is_generic_selected_solution_output_name(str(name or "").strip().lower()):
                if not is_missing_value(_output_value(output)):
                    return True
    return False


def _solve_problem_selected_solution_passes(env, outputs):
    for name in (
        "selected_solution_pass",
        "overall_selected_solution_pass",
        "selection_pass",
        "overall_selection_pass",
    ):
        value = None
        if isinstance(env, dict) and name in env:
            value = env.get(name)
        elif isinstance(outputs, dict):
            value = _output_value(outputs.get(name))
        if value is True:
            return True
        if value is False:
            return False

    status_value = None
    if isinstance(env, dict):
        status_value = env.get("selection_status") or env.get("overall_selection_status")
    if is_missing_value(status_value) and isinstance(outputs, dict):
        status_value = _health_output_value(outputs, ("selection_status", "overall_selection_status"))
    return _selection_status_pass_from_value(status_value) is True


def _solve_problem_release_status_value(env, outputs):
    return _resolve_canonical_overall_status(env=env, outputs=outputs)


def _use_suggest_improvements_recommendation_status_policy(mcm_request, outputs):
    if not isinstance(mcm_request, dict) or not isinstance(outputs, dict):
        return False
    mode = normalize_eas_mode(mcm_request.get("mode"))
    if mode != "suggest-improvements":
        return False
    return any(
        _is_computed_recommendation_output(name, output)
        for name, output in outputs.items()
    )


def _is_computed_recommendation_output(name, output):
    if not isinstance(output, dict) or output.get("source") != "computed":
        return False
    value = output.get("value")
    if is_missing_value(value):
        return False
    lowered = str(name or "").strip().lower()
    return (
        lowered in {
            "recommended_option",
            "recommended_option_name",
            "recommended_concept",
            "recommended_concept_name",
            "recommendation_status",
            "overall_recommendation_status",
        }
        or lowered.startswith("recommended_")
        or lowered.endswith("_recommendation_status")
        or lowered.endswith("_recommended_option")
        or lowered.endswith("_recommended_option_name")
    )


def _criterion_output_index(name):
    text = str(name or "").strip()
    if not text:
        return None
    lowered = text.lower()
    if _is_aggregate_status_output(lowered):
        return None
    match = re.search(r"(?:^|_)c([1-9]\d*)(?=_|$)", lowered)
    if not match:
        return None
    return int(match.group(1))


def _is_candidate_specific_criterion_output(name):
    if not _criterion_output_index(name):
        return False
    if _candidate_identity_from_name(name):
        return True

    tokens = _name_tokens(name)
    criterion_index = None
    for index, token in enumerate(tokens):
        if re.fullmatch(r"c[1-9]\d*", token):
            criterion_index = index
            break
    if criterion_index is None:
        return False

    if criterion_index > 0 and _looks_like_candidate_label_token(tokens[criterion_index - 1]):
        return True
    if (
        criterion_index + 1 < len(tokens)
        and _looks_like_candidate_label_token(tokens[criterion_index + 1])
    ):
        return True
    return False


def _looks_like_candidate_label_token(token):
    text = str(token or "").lower()
    if (len(text) == 1 and "a" <= text <= "z") or text.isdecimal():
        return True
    if text.startswith("p") and text[1:].isdecimal():
        return True
    unit_suffixes = (
        "in",
        "inch",
        "inches",
        "awg",
        "a",
        "amp",
        "amps",
        "hp",
        "kw",
        "w",
        "ft",
        "mm",
        "cm",
        "m",
    )
    return any(
        text.endswith(suffix) and text[: -len(suffix)].isdecimal()
        for suffix in unit_suffixes
    )


def _is_aggregate_status_output(name):
    lowered = str(name or "").strip().lower()
    candidates = {lowered}
    for suffix in ("_string", "_pass_fail_unknown"):
        if lowered.endswith(suffix):
            candidates.add(lowered[: -len(suffix)])
    aggregate_names = {
        "release_status",
        "overall_release_status",
        "result_status",
        "overall_result_status",
        "overall_selection_status",
        "overall_recommendation_status",
        "final_status",
        "overall_pass",
        "overall_result",
        "overall_status",
    }
    return any(candidate in aggregate_names for candidate in candidates)


def _inject_missing_constraint_margin_outputs(mcm_request, requested, env, variable_meta, equation_for, steps, unit_validation):
    equations = mcm_request.get("equations")
    if not isinstance(equations, list):
        return {"outputs": set(), "missing_variables": set()}

    handled = set()
    handled_missing = set()
    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        if lhs not in requested and not _is_layer6_surface_margin_lhs(lhs):
            continue
        if not _looks_like_constraint_margin_output(lhs):
            continue
        parsed_margin = _parse_subtraction_margin_rhs(rhs)
        if not parsed_margin:
            continue
        left, right = parsed_margin
        missing = [name for name in (left, right) if is_missing_value(env.get(name))]
        if not missing:
            continue
        handled_missing.update(missing)
        unit = _surface_temperature_unit(variable_meta) if "surface_temperature" in lhs else _unit_for_margin_lhs(lhs, variable_meta)
        _store_unknown_margin_output(
            env,
            variable_meta,
            equation_for,
            steps,
            unit_validation,
            lhs,
            unit,
            _equation_name(equation, index),
            rhs,
            missing,
        )
        handled.add(lhs)
    return {"outputs": handled, "missing_variables": handled_missing}


def _looks_like_constraint_margin_output(name):
    return isinstance(name, str) and name.endswith(("_margin_C", "_margin"))


def _is_layer6_surface_margin_lhs(lhs):
    return isinstance(lhs, str) and "surface_temperature_margin" in lhs


def _parse_subtraction_margin_rhs(rhs):
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return None
    node = tree.body
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Sub):
        return None
    left = _simple_constraint_operand(node.left)
    right = _simple_constraint_operand(node.right)
    if not isinstance(left, str) or not isinstance(right, str):
        return None
    return left, right


def _unit_for_margin_lhs(lhs, variable_meta):
    meta = variable_meta.get(lhs, {})
    if meta.get("unit"):
        return meta.get("unit")
    return None


def _surface_temperature_unit(variable_meta):
    for name in ("bath_surface_temperature_C", "max_safe_surface_temperature_C", "surface_temperature_C"):
        unit = variable_meta.get(name, {}).get("unit")
        if unit:
            return unit
    return "C"


def _store_unknown_margin_output(env, variable_meta, equation_for, steps, unit_validation, name, unit, equation, expression, missing):
    env[name] = None
    equation_for[name] = equation
    variable_meta.setdefault(name, {})
    variable_meta[name]["source"] = "not_computed_missing_inputs"
    variable_meta[name]["equation"] = equation
    variable_meta[name]["unit"] = normalize_unit(unit)
    variable_meta[name]["status"] = "unknown"
    variable_meta[name]["missing_inputs"] = list(missing)
    message = (
        "Constraint margin could not be evaluated because required inputs are missing: "
        + ", ".join(missing)
        + "."
    )
    unit_check = {
        "equation_name": equation,
        "expression": expression,
        "lhs": name,
        "lhs_expected_unit": normalize_unit(unit),
        "rhs_inferred_unit": normalize_unit(unit),
        "status": "valid",
        "severity": "info",
        "message": message,
    }
    variable_meta[name]["unit_validation"] = unit_check
    unit_validation.append(unit_check)
    steps.append({
        "equation": equation,
        "expression": expression,
        "lhs": name,
        "rhs": expression,
        "inputs_used": {},
        "result": None,
        "purpose": message,
        "unit_validation": unit_check,
    })


def _constraint_spec_from_assignment_rhs(equation, index, lhs, rhs):
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return None
    node = tree.body
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
        return None
    comparator = _comparator_symbol(node.ops[0])
    if not comparator:
        return None
    return {
        "name": _equation_name(equation, index),
        "lhs": _simple_constraint_operand(node.left),
        "comparator": comparator,
        "rhs": _simple_constraint_operand(node.comparators[0]),
        "source": "equation",
        "expression": rhs,
        "description": _equation_purpose(equation),
        "boolean_output": lhs,
    }


def _handled_skipped_expressions(mcm_request, handled_outputs):
    if not handled_outputs:
        return []
    equations = mcm_request.get("equations")
    if not isinstance(equations, list):
        return []
    expressions = []
    for equation in equations:
        expression = _equation_expression(equation)
        parsed = _split_assignment(expression) if expression else None
        if not parsed:
            continue
        lhs, rhs = parsed
        if lhs in handled_outputs:
            expressions.append(rhs)
    return expressions


def _missing_names_from_constraint_check(check):
    return set(_missing_inputs_from_constraint_check(check))


def _missing_inputs_from_constraint_check(check):
    message = str(check.get("message") or "")
    names = set(re.findall(r"\b[A-Za-z_]\w*\b", message))
    ordered = []
    for candidate in (str(check.get("lhs")), str(check.get("rhs"))):
        if candidate in names and candidate not in ordered:
            ordered.append(candidate)
    return ordered


def _constraint_checks_for_env(mcm_request, env, variable_meta):
    outputs = {}
    for name, value in env.items():
        meta = variable_meta.get(name, {})
        outputs[name] = {
            "value": value,
            "unit": meta.get("unit"),
            "source": meta.get("source"),
        }
    return check_constraints(mcm_request, outputs).get("checks", [])


def _ensure_unknown_surface_constraint_check(checks, env, variable_meta):
    existing = _find_constraint_check(
        checks,
        {
            "bath_surface_temperature_C",
            "surface_temperature_C",
            "max_safe_surface_temperature_C",
            "max_surface_temperature_C",
        },
    )
    if existing:
        return
    missing = [
        name for name in ("bath_surface_temperature_C", "max_safe_surface_temperature_C")
        if is_missing_value(env.get(name))
    ]
    checks.append({
        "name": "surface_temperature_constraint",
        "expression": "bath_surface_temperature_C <= max_safe_surface_temperature_C",
        "lhs": "bath_surface_temperature_C",
        "lhs_value": None,
        "lhs_unit": "C",
        "comparator": "<=",
        "rhs": "max_safe_surface_temperature_C",
        "rhs_value": None,
        "rhs_unit": "C",
        "passes": None,
        "margin": None,
        "margin_unit": None,
        "margin_percent": None,
        "severity": "unknown",
        "message": "Constraint references unavailable values: " + ", ".join(missing) + ".",
        "source": "equation",
        "description": "Surface-temperature constraint could not be evaluated.",
        "unit_validation": None,
    })


def compute_overall_constraint_status(constraint_results):
    any_known_fail = any(check.get("passes") is False for check in constraint_results)
    any_unknown = any(check.get("passes") is None for check in constraint_results)
    if any_known_fail:
        overall = "fail"
    elif any_unknown:
        overall = "unknown"
    else:
        overall = "pass"
    return any_known_fail, any_unknown, overall


def _find_constraint_check(checks, names):
    for check in checks:
        lhs = str(check.get("lhs") or "")
        rhs = str(check.get("rhs") or "")
        expression = str(check.get("expression") or "")
        if lhs in names or rhs in names or any(name in expression for name in names):
            return check
    return None


def _constraint_status_value(check):
    if not check or check.get("passes") is None:
        return "unknown"
    return "pass" if check.get("passes") else "fail"


def _store_computed_env_output(env, variable_meta, equation_for, steps, unit_validation, name, value, unit, equation, expression, purpose):
    env[name] = value
    equation_for[name] = equation
    variable_meta.setdefault(name, {})
    variable_meta[name]["source"] = "computed"
    variable_meta[name]["equation"] = equation
    variable_meta[name]["unit"] = normalize_unit(unit)
    unit_check = {
        "equation_name": equation,
        "expression": expression,
        "lhs": name,
        "lhs_expected_unit": normalize_unit(unit),
        "rhs_inferred_unit": normalize_unit(unit),
        "status": "valid",
        "severity": "info",
        "message": f"Deterministic Layer 6 constraint summary output assigned unit {normalize_unit(unit)}.",
    }
    variable_meta[name]["unit_validation"] = unit_check
    unit_validation.append(unit_check)
    steps.append({
        "equation": equation,
        "expression": expression,
        "lhs": name,
        "rhs": expression,
        "inputs_used": {},
        "result": value,
        "purpose": purpose,
        "unit_validation": unit_check,
    })


def _skipped_lhs(expression):
    if not isinstance(expression, str) or "=" not in expression:
        return None
    lhs, _ = expression.split("=", 1)
    lhs = lhs.strip()
    return lhs if _is_safe_variable_name(lhs) else None


_TEXTUAL_STATUS_NAME_TOKENS = {"str", "string", "label", "name", "reason", "message", "description"}

_VALUE_AGGREGATION_NAME_TOKENS = {
    "val",
    "vals",
    "value",
    "values",
    "score",
    "scores",
    "cost",
    "costs",
    "price",
    "prices",
    "rating",
    "ratings",
    "size",
    "sizes",
    "diameter",
    "diameters",
}

_VALUE_AGGREGATION_NAME_SUFFIXES = (
    "_val",
    "_vals",
    "_value",
    "_values",
    "_value_list",
    "_values_list",
    "_candidate_value",
    "_candidate_values",
    "_candidate_values_list",
    "_option_value",
    "_option_values",
    "_option_values_list",
    "_score",
    "_scores",
    "_cost",
    "_costs",
    "_rating",
    "_ratings",
    "_size",
    "_sizes",
    "_diameter",
    "_diameters",
    "_diameter_values",
    "_diameters_values",
)

_KNOWN_STATUS_LITERAL_TOKENS = {
    "pass",
    "fail",
    "unknown",
    "viable_options_found",
    "viable_option_found",
    "viable_solutions_found",
    "viable_solution_found",
    "no_viable_options_found",
    "no_viable_option_found",
    "no_viable_solutions_found",
    "no_viable_solution_found",
    "computed",
    "computed_clean",
    "computed_with_warnings",
    "partial",
    "unsupported",
    "needs_human_review",
    "error",
    "selection_pass",
    "selection_no_viable_option",
    "pass_configuration_selected",
    "no_viable_configuration",
}


def _is_known_status_literal_value(value):
    if not isinstance(value, str):
        return False
    token = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return bool(token) and token in _KNOWN_STATUS_LITERAL_TOKENS


def _string_literal_unit(value):
    return "status_string" if _is_known_status_literal_value(value) else "label_string"


def _canonical_text_unit(unit):
    text = str(unit or "").strip()
    lowered = re.sub(r"[\s_]+", "_", text.lower()).strip("_")
    if lowered in {"string", "str", "text"}:
        return "string"
    if lowered in {"label", "name", "label_string"}:
        return "label_string"
    return normalize_unit(unit)


def _is_textual_unit(unit):
    normalized = _canonical_text_unit(unit)
    return normalized in {"string", "label_string", "status_string", "pass_fail_unknown"}


def _is_status_text_unit(unit):
    normalized = _canonical_text_unit(unit)
    return normalized in {"status_string", "pass_fail_unknown"}


def _common_textual_unit(units):
    normalized_units = [_canonical_text_unit(unit) for unit in units if unit is not None]
    if not normalized_units or not all(_is_textual_unit(unit) for unit in normalized_units):
        return None
    if all(_is_status_text_unit(unit) for unit in normalized_units):
        return "status_string"
    return "label_string"


def _status_name_unit_override(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return None
    tokens = [token for token in re.split(r"[_\W]+", lowered) if token]
    token_set = set(tokens)

    if lowered.endswith("_count") or token_set.intersection({"count", "complexity"}):
        return None
    if lowered.endswith(("_str", "_string", "_label", "_name", "_reason", "_message", "_description")) or token_set.intersection(_TEXTUAL_STATUS_NAME_TOKENS):
        return "status_string"
    if _looks_like_boolean_status_name(lowered, tokens, token_set):
        return "boolean"
    if _name_prefers_value_aggregation(lowered, token_set):
        return None

    if "status" in token_set:
        return "status_string"

    return None


def _looks_like_boolean_status_name(lowered, tokens, token_set):
    if _has_unit_bearing_metric_token(lowered, token_set) and not _has_explicit_boolean_predicate_shape(tokens, token_set):
        return False
    if _name_prefers_value_aggregation(lowered, token_set) and not _has_explicit_boolean_predicate_shape(tokens, token_set):
        return False

    if "overall_pass" in lowered:
        return True
    if _has_explicit_boolean_predicate_shape(tokens, token_set):
        return True
    return False


def _has_explicit_boolean_predicate_shape(tokens, token_set):
    if not tokens:
        return False
    joined = "_".join(tokens)
    if tokens[0] in {"is", "has", "can"}:
        return True
    if token_set.intersection({"criterion", "criteria"}) and token_set.intersection({
        "pass",
        "passes",
        "passed",
        "fail",
        "fails",
        "failed",
    }):
        return True
    if tokens[-1] == "viable" and "among" in token_set:
        return False
    if tokens[-1] in {"required", "enabled"} and _has_unit_bearing_metric_token(joined, token_set):
        return False
    if tokens[-1] in {
        "pass",
        "passes",
        "passed",
        "fail",
        "fails",
        "failed",
        "viable",
        "valid",
        "ok",
        "required",
        "enabled",
        "met",
    }:
        return True
    for index, token in enumerate(tokens[:-1]):
        if token == "is" and tokens[index + 1] in {"viable", "valid", "required", "enabled"}:
            return True
    return "overall_pass" in joined


def _name_prefers_value_aggregation(lowered, token_set):
    lowered = str(lowered or "").strip().lower()
    if lowered.endswith(_VALUE_AGGREGATION_NAME_SUFFIXES):
        return True
    return bool(token_set.intersection(_VALUE_AGGREGATION_NAME_TOKENS))


def _has_unit_bearing_metric_token(lowered, token_set):
    phrase_markers = {
        "purge_air",
        "pressure_drop",
    }
    if any(marker in lowered for marker in phrase_markers):
        return True
    metric_tokens = {
        "flow",
        "airflow",
        "pressure",
        "dewpoint",
        "temperature",
        "velocity",
        "area",
        "diameter",
        "diameters",
        "head",
        "current",
        "voltage",
        "power",
        "hp",
        "bhp",
        "torque",
        "load",
        "score",
        "scores",
        "cost",
        "costs",
        "rating",
        "ratings",
        "size",
        "sizes",
        "weight",
        "mass",
    }
    return bool(token_set.intersection(metric_tokens))


_HYDRAULIC_HEAD_CONTEXT_TOKENS = {
    "head",
    "tdh",
    "npsh",
    "npsha",
    "npshr",
}

_HYDRAULIC_HEAD_CONTEXT_PHRASES = (
    "static_elevation_head",
    "elevation_head",
    "static_head",
    "friction_head",
    "friction_loss",
    "friction_gradient",
    "equipment_loss",
    "head_loss",
    "total_dynamic_head",
    "pump_head",
    "required_pump_head",
    "rated_head",
    "available_npsh",
    "required_npsh",
    "npsh_margin",
)

_GEOMETRIC_LENGTH_CONTEXT_TOKENS = {
    "area",
    "diameter",
    "diam",
    "id",
    "inside",
    "length",
    "radius",
}

_GEOMETRIC_LENGTH_CONTEXT_PHRASES = (
    "pipe_length",
    "equivalent_pipe_length",
    "physical_installed_pipe_length",
    "installed_pipe_length",
    "pipe_inside_diameter",
    "inside_diameter",
)


def _hydraulic_head_unit_from_name(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return None
    if not _name_has_hydraulic_head_context(lowered):
        return None
    if _name_has_geometry_length_context(lowered) and not _name_has_hydraulic_head_context(lowered):
        return None
    tokens = [token for token in re.split(r"[_\W]+", lowered) if token]
    if tokens and tokens[-1] in {"ft", "feet", "head", "water", "h2o"}:
        return "ft_head"
    if lowered.endswith(("_ft", "_feet", "_ft_head", "_head_ft", "_ft_water", "_ft_h2o")):
        return "ft_head"
    return None


def _name_has_hydraulic_head_context(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return False
    compact = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    tokens = {token for token in re.split(r"[_\W]+", lowered) if token}
    if tokens.intersection(_HYDRAULIC_HEAD_CONTEXT_TOKENS):
        return True
    return any(phrase in compact for phrase in _HYDRAULIC_HEAD_CONTEXT_PHRASES)


def _name_has_geometry_length_context(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return False
    compact = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    tokens = {token for token in re.split(r"[_\W]+", lowered) if token}
    if any(phrase in compact for phrase in _GEOMETRIC_LENGTH_CONTEXT_PHRASES):
        return True
    if tokens.intersection({"diameter", "diam", "radius", "area"}):
        return True
    if "length" in tokens and not _name_has_hydraulic_head_context(lowered):
        return True
    return False


def _unit_from_name_suffix(name):
    lowered = str(name or "").strip().lower()
    tokens = [token for token in re.split(r"[_\W]+", lowered) if token]
    token_set = set(tokens)
    terminal_physical_unit = _compound_unit_from_name_suffix(lowered) or _terminal_physical_unit_from_name_tokens(tokens)
    explicit_boolean_shape = _has_explicit_boolean_predicate_shape(tokens, token_set)
    status_unit = (
        _explicit_status_name_unit_override(lowered, tokens, token_set)
        if explicit_boolean_shape or not terminal_physical_unit
        else None
    )
    if status_unit:
        return status_unit

    if lowered in {"sg", "specific_gravity"} or lowered.endswith(("_sg", "_specific_gravity")):
        return "dimensionless"
    compound_unit = terminal_physical_unit if _compound_unit_from_name_suffix(lowered) else None
    if compound_unit:
        return compound_unit
    percent_descriptor_unit = _physical_unit_from_percent_descriptor_name(lowered, tokens)
    if percent_descriptor_unit:
        return percent_descriptor_unit
    dimensionless_modifier_unit = _dimensionless_modifier_unit_from_name(lowered, token_set)
    if dimensionless_modifier_unit:
        return dimensionless_modifier_unit
    dominant_physical_unit = _dominant_physical_unit_from_name_tokens(lowered, tokens, token_set)
    if dominant_physical_unit:
        return dominant_physical_unit
    pump_power_unit = _pump_power_unit_from_name(lowered, tokens, token_set)
    if pump_power_unit:
        return pump_power_unit
    hydraulic_head_unit = _hydraulic_head_unit_from_name(lowered)
    if hydraulic_head_unit:
        return hydraulic_head_unit
    temperature_interval_unit = _temperature_interval_unit_from_name(lowered, tokens, token_set)
    if temperature_interval_unit:
        return temperature_interval_unit
    temperature_unit = _temperature_unit_from_name_suffix(lowered, tokens, token_set)
    if temperature_unit:
        return temperature_unit
    resistance_per_length_unit = _resistance_per_length_unit_from_name(lowered, token_set)
    if resistance_per_length_unit:
        return resistance_per_length_unit
    if lowered.endswith(("_ohm_per_ft", "_ohms_per_ft", "_ohm_per_foot", "_ohms_per_foot")):
        return "ohm/ft"
    if lowered.endswith((
        "_ohm_per_1000ft",
        "_ohms_per_1000ft",
        "_ohm_per_1000_ft",
        "_ohms_per_1000_ft",
        "_ohm_per_1000_feet",
        "_ohms_per_1000_feet",
    )):
        return "ohm/1000ft"
    if lowered.endswith((
        "_in3_per_min",
        "_in3_per_minute",
        "_in_3_per_min",
        "_in_3_per_minute",
        "_in_cubed_per_min",
        "_in_cubed_per_minute",
        "_cubic_in_per_min",
        "_cubic_in_per_minute",
        "_cubic_inches_per_min",
        "_cubic_inches_per_minute",
    )):
        return "in^3/min"
    if lowered.endswith(("_in_per_min", "_inch_per_min", "_inches_per_min", "_in_per_minute", "_inch_per_minute", "_inches_per_minute")):
        return "in/min"
    if lowered.endswith((
        "_cfs",
        "_ft3_per_s",
        "_ft3_per_sec",
        "_ft3_per_second",
        "_ft_3_per_s",
        "_ft_3_per_sec",
        "_ft_3_per_second",
        "_cubic_ft_per_s",
        "_cubic_ft_per_sec",
        "_cubic_ft_per_second",
        "_cubic_feet_per_s",
        "_cubic_feet_per_sec",
        "_cubic_feet_per_second",
    )):
        return "ft^3/s"
    if lowered.endswith(("_ft_per_s", "_ft_per_sec", "_ft_per_second", "_feet_per_s", "_feet_per_sec", "_feet_per_second")):
        return "ft/s"
    if lowered.endswith(("_m_per_s", "_m_per_sec", "_m_per_second", "_meters_per_s", "_meters_per_sec", "_meters_per_second")):
        return "m/s"
    if lowered.endswith(("_kg_per_m3", "_kg_per_m_3", "_kg_per_cubic_m", "_kg_per_cubic_meter", "_kg_per_cubic_metre")):
        return "kg/m^3"
    if lowered.endswith(("_m2", "_m_2", "_sq_m", "_square_m", "_square_meter", "_square_meters", "_square_metre", "_square_metres")):
        return "m^2"
    if lowered.endswith("_pa"):
        return "Pa"
    if lowered.endswith("_n"):
        return "N"
    if lowered.endswith(("_lbf_per_ft2", "_lbf_per_ft_2", "_lb_per_ft2", "_lb_per_ft_2", "_psf")):
        return "psf"
    if lowered in {"in_per_ft", "inches_per_ft", "inch_per_ft", "in_per_foot", "inches_per_foot", "inch_per_foot"}:
        return "in/ft"
    if lowered.endswith(("_usd_per_scfm_year", "_usd_per_scfm_per_year", "_usd_per_scfm_yr", "_usd_per_scfm_per_yr")):
        return "USD/scfm/year"
    if lowered.endswith(("_dollars_per_scfm_year", "_dollars_per_scfm_per_year", "_dollars_per_scfm_yr", "_dollars_per_scfm_per_yr")):
        return "USD/scfm/year"
    if lowered.endswith(("_usd_per_year", "_usd_per_yr", "_dollars_per_year", "_dollars_per_yr")):
        return "USD/year"
    annualized_cost_unit = _annualized_cost_unit_from_name(lowered, token_set)
    if annualized_cost_unit:
        return annualized_cost_unit
    if lowered.endswith((
        "_ft_head_per_ft",
        "_head_ft_per_ft",
        "_ft_per_ft",
        "_ft_per_100ft",
        "_ft_per_100_ft",
        "_feet_per_100ft",
        "_feet_per_100_ft",
        "_ft_head_per_100ft",
        "_ft_head_per_100_ft",
        "_head_ft_per_100ft",
        "_head_ft_per_100_ft",
    )):
        return "dimensionless"
    if any(marker in lowered for marker in ("_area_sqft", "_area_sq_ft", "_area_square_ft", "_sqft_", "_sq_ft_", "_square_ft_")):
        return "ft^2"
    if any(marker in lowered for marker in ("_area_in2", "_area_in_2", "_area_sq_in", "_sqin_", "_sq_in_", "_square_in_")):
        return "in^2"
    suffix_units = [
        ("_moment_in_lbf", "lbf_in"),
        ("_moment_lbf_in", "lbf_in"),
        ("_in_lbf", "lbf_in"),
        ("_lbf_in", "lbf_in"),
        ("_in_lb", "lbf_in"),
        ("_lb_in", "lbf_in"),
        ("_moment_ft_lbf", "lbf*ft"),
        ("_moment_lbf_ft", "lbf*ft"),
        ("_moment_lbft", "lbf*ft"),
        ("_ft_lbf", "lbf*ft"),
        ("_lbf_ft", "lbf*ft"),
        ("_lbft", "lbf*ft"),
        ("_ft_lb", "lbf*ft"),
        ("_lb_ft", "lbf*ft"),
        ("_n_m", "N*m"),
        ("_pa", "Pa"),
        ("_m_2", "m^2"),
        ("_m2", "m^2"),
        ("_sq_m", "m^2"),
        ("_square_m", "m^2"),
        ("_kg_per_m3", "kg/m^3"),
        ("_kg_per_m_3", "kg/m^3"),
        ("_sq_ft", "ft^2"),
        ("_square_ft", "ft^2"),
        ("_sqft", "ft^2"),
        ("_ft_3", "ft^3"),
        ("_ft3", "ft^3"),
        ("_cfs", "ft^3/s"),
        ("_ft_2", "ft^2"),
        ("_ft2", "ft^2"),
        ("_scfm", "scfm"),
        ("_inh2o", "inH2O"),
        ("_in_h2o", "inH2O"),
        ("_inwc", "inH2O"),
        ("_sq_in", "in^2"),
        ("_square_in", "in^2"),
        ("_sqin", "in^2"),
        ("_in_4", "in^4"),
        ("_in4", "in^4"),
        ("_in_3", "in^3"),
        ("_in3", "in^3"),
        ("_in_2", "in^2"),
        ("_in2", "in^2"),
        ("_ft_per_s", "ft/s"),
        ("_fps", "ft/s"),
        ("_m_per_s", "m/s"),
        ("_psf", "psf"),
        ("_fpm", "fpm"),
        ("_cfm", "cfm"),
        ("_btu_per_hr_per_gpm_f", "BTU/hr/gpm/F"),
        ("_btu_per_hour_per_gpm_f", "BTU/hr/gpm/F"),
        ("_btu_per_hr", "BTU/hr"),
        ("_btu_per_hour", "BTU/hr"),
        ("_boolean", "boolean"),
        ("_string", "status_string"),
        ("_percent", "percent"),
        ("_pct", "percent"),
        ("_dimensionless", "dimensionless"),
        ("_factor", "dimensionless"),
        ("_ratio", "dimensionless"),
        ("_unit", "dimensionless"),
        ("_qty", "dimensionless"),
        ("_count", "dimensionless"),
        ("_ohms", "ohm"),
        ("_ohm", "ohm"),
        ("_minutes", "min"),
        ("_min", "min"),
        ("_years", "year"),
        ("_year", "year"),
        ("_yrs", "year"),
        ("_yr", "year"),
        ("_hr", "h"),
        ("_h", "h"),
        ("_usd", "USD"),
        ("_cost_usd", "USD"),
        ("_cost", "USD"),
        ("_price", "USD"),
        ("_budget", "USD"),
        ("_ah", "Ah"),
        ("_wh", "Wh"),
        ("_n", "N"),
        ("_lbf", "lbf"),
        ("_psi", "psi"),
        ("_in", "in"),
        ("_gpm", "gpm"),
        ("_hp", "hp"),
        ("_bhp", "hp"),
        ("_rpm", "rpm"),
        ("_a", "A"),
        ("_v", "V"),
        ("_w", "W"),
        ("_f", "F"),
        ("_ft", "ft"),
    ]
    for suffix, unit in suffix_units:
        if lowered.endswith(suffix):
            return unit

    if _efficiency_name_is_dimensionless(lowered, token_set):
        return "dimensionless"
    if _aerodynamic_coefficient_name_is_dimensionless(lowered, token_set):
        return "dimensionless"

    status_unit = _status_name_unit_override(name)
    if status_unit:
        return status_unit

    if any(marker in lowered for marker in ("velocity", "speed", "airflow", "flow")):
        return None
    compact = lowered.replace("_", "")
    if _has_numeric_unit_suffix(compact, "in"):
        return "in"
    if _has_numeric_unit_suffix(compact, "ft"):
        return "ft"
    return None


def _has_numeric_unit_suffix(text, suffix):
    if not text.endswith(suffix):
        return False
    stem = text[: -len(suffix)]
    return bool(stem) and stem[-1].isdecimal()


def _compound_unit_from_name_suffix(lowered):
    compound_suffixes = [
        (
            (
                "_kg_per_m2",
                "_kg_per_m_2",
                "_kg_per_sq_m",
                "_kg_per_square_m",
                "_kg_per_square_meter",
                "_kg_per_square_meters",
                "_kg_per_square_metre",
                "_kg_per_square_metres",
                "_kilogram_per_m2",
                "_kilograms_per_m2",
                "_kilogram_per_m_2",
                "_kilograms_per_m_2",
                "_kilogram_per_square_meter",
                "_kilograms_per_square_meter",
                "_kilogram_per_square_metre",
                "_kilograms_per_square_metre",
            ),
            "kg/m^2",
        ),
        (
            (
                "_n_per_m2",
                "_n_per_m_2",
                "_n_per_sq_m",
                "_n_per_square_m",
                "_n_per_square_meter",
                "_n_per_square_meters",
                "_n_per_square_metre",
                "_n_per_square_metres",
                "_newton_per_m2",
                "_newtons_per_m2",
                "_newton_per_m_2",
                "_newtons_per_m_2",
                "_newton_per_square_meter",
                "_newtons_per_square_meter",
                "_newton_per_square_metre",
                "_newtons_per_square_metre",
            ),
            "Pa",
        ),
        (("_w_per_kg", "_watt_per_kg", "_watts_per_kg", "_w_per_kilogram", "_watt_per_kilogram", "_watts_per_kilogram"), "W/kg"),
        (
            (
                "_wh_per_kg",
                "_w_h_per_kg",
                "_watt_hour_per_kg",
                "_watt_hours_per_kg",
                "_wh_per_kilogram",
                "_watt_hour_per_kilogram",
                "_watt_hours_per_kilogram",
            ),
            "Wh/kg",
        ),
        (("_n_per_kg", "_newton_per_kg", "_newtons_per_kg", "_n_per_kilogram", "_newton_per_kilogram", "_newtons_per_kilogram"), "N/kg"),
        (("_kg_per_m3", "_kg_per_m_3", "_kg_per_cubic_m", "_kg_per_cubic_meter", "_kg_per_cubic_metre"), "kg/m^3"),
        (("_m_per_s", "_m_per_sec", "_m_per_second", "_meters_per_s", "_meters_per_sec", "_meters_per_second"), "m/s"),
        (("_ft_per_min", "_ft_per_minute", "_feet_per_min", "_feet_per_minute"), "fpm"),
        (("_w_per_c", "_w_per_degc", "_w_per_deg_c", "_w_per_celsius", "_w_per_degree_c", "_w_per_degrees_c"), "W/C"),
        (("_w_per_k", "_w_per_kelvin"), "W/K"),
        (("_c_per_w", "_degc_per_w", "_deg_c_per_w", "_celsius_per_w", "_degree_c_per_w", "_degrees_c_per_w"), "C/W"),
        (("_kj_per_kg_c", "_kj_per_kg_degc", "_kj_per_kg_deg_c", "_kj_per_kg_celsius"), "kJ/kg/C"),
        (("_kg_per_c", "_kg_per_degc", "_kg_per_deg_c", "_kg_per_celsius"), "kg/C"),
        (("_lb_per_gal", "_lbs_per_gal", "_lb_per_gallon", "_lbs_per_gallon"), "lb/gal"),
        (
            (
                "_btu_per_lbf",
                "_btu_per_lb_f",
                "_btu_per_lb_degf",
                "_btu_per_lb_deg_f",
                "_btu_per_lb_deltaf",
                "_btu_per_lb_delta_f",
                "_btu_per_lb_fahrenheit",
            ),
            "BTU/lb/F",
        ),
    ]
    matches = []
    for suffixes, unit in compound_suffixes:
        if lowered.endswith(suffixes):
            matched_suffix = max(
                (suffix for suffix in suffixes if lowered.endswith(suffix)),
                key=len,
            )
            matches.append((len(matched_suffix), unit))
    if matches:
        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]
    return None


def _terminal_physical_unit_from_name_tokens(tokens):
    if not tokens:
        return None
    return _physical_unit_from_name_token_sequence([tokens[-1]])


def _physical_unit_from_percent_descriptor_name(lowered, tokens):
    percent_tokens = {"percent", "pct", "percentage"}
    if not tokens or not percent_tokens.intersection(tokens):
        return None

    reduced_tokens = [
        token
        for token in tokens
        if token not in percent_tokens
        and token not in {"of", "at"}
        and not re.fullmatch(r"\d+(?:\.\d+)?", token)
    ]
    if not reduced_tokens:
        return None

    reduced_lowered = "_".join(reduced_tokens)
    compound_unit = _compound_unit_from_name_suffix(reduced_lowered)
    if _is_physical_percent_descriptor_unit(compound_unit):
        return compound_unit

    unit = _physical_unit_from_name_token_sequence(reduced_tokens)
    if _is_physical_percent_descriptor_unit(unit):
        return unit
    return None


def _physical_unit_from_name_token_sequence(tokens):
    unit_sequences = [
        (("btu", "per", "hr", "per", "gpm", "f"), "BTU/hr/gpm/F"),
        (("btu", "per", "hour", "per", "gpm", "f"), "BTU/hr/gpm/F"),
        (("btu", "per", "hr"), "BTU/hr"),
        (("btu", "per", "hour"), "BTU/hr"),
        (("ft", "per", "min"), "fpm"),
        (("ft", "per", "minute"), "fpm"),
        (("feet", "per", "min"), "fpm"),
        (("feet", "per", "minute"), "fpm"),
        (("ft", "per", "s"), "ft/s"),
        (("ft", "per", "sec"), "ft/s"),
        (("ft", "per", "second"), "ft/s"),
        (("feet", "per", "s"), "ft/s"),
        (("feet", "per", "sec"), "ft/s"),
        (("feet", "per", "second"), "ft/s"),
        (("m", "per", "s"), "m/s"),
        (("m", "per", "sec"), "m/s"),
        (("m", "per", "second"), "m/s"),
        (("meter", "per", "second"), "m/s"),
        (("meters", "per", "second"), "m/s"),
        (("lbf", "per", "ft2"), "psf"),
        (("lbf", "per", "ft", "2"), "psf"),
        (("lb", "per", "ft2"), "psf"),
        (("lb", "per", "ft", "2"), "psf"),
        (("lbf", "ft"), "lbf*ft"),
        (("lb", "ft"), "lbf*ft"),
        (("ft", "lbf"), "lbf*ft"),
        (("ft", "lb"), "lbf*ft"),
        (("lbf", "in"), "lbf_in"),
        (("lb", "in"), "lbf_in"),
        (("in", "lbf"), "lbf_in"),
        (("in", "lb"), "lbf_in"),
        (("lb", "per", "gal"), "lb/gal"),
        (("lb", "per", "gallon"), "lb/gal"),
    ]
    for end in range(len(tokens), 0, -1):
        for sequence, unit in unit_sequences:
            start = end - len(sequence)
            if start >= 0 and tuple(tokens[start:end]) == sequence:
                return unit

    single_token_units = {
        "hp": "hp",
        "bhp": "hp",
        "rpm": "rpm",
        "fpm": "fpm",
        "fps": "ft/s",
        "cfs": "ft^3/s",
        "psf": "psf",
        "cfm": "cfm",
        "scfm": "scfm",
        "gpm": "gpm",
        "psi": "psi",
        "lbf": "lbf",
        "lbft": "lbf*ft",
        "lbfft": "lbf*ft",
        "lb": "lb",
        "ft": "ft",
        "in": "in",
        "a": "A",
        "amp": "A",
        "amps": "A",
        "v": "V",
        "volt": "V",
        "volts": "V",
        "w": "W",
        "kw": "kW",
        "btu": "BTU",
    }
    for token in reversed(tokens):
        unit = single_token_units.get(token)
        if unit:
            return unit
    return None


def _dominant_physical_unit_from_name_tokens(lowered, tokens, token_set):
    if not tokens:
        return None
    if _has_torque_unit_token(tokens):
        return "lbf*ft"
    if _has_gpm_flow_unit_token(lowered, tokens, token_set):
        return "gpm"
    if _has_fpm_unit_token(tokens):
        return "fpm"
    if _has_clear_hp_result_marker(lowered, token_set):
        return "hp"
    return None


def _has_torque_unit_token(tokens):
    if {"lbft", "lbfft"}.intersection(tokens):
        return True
    torque_sequences = {
        ("lbf", "ft"),
        ("lb", "ft"),
        ("ft", "lbf"),
        ("ft", "lb"),
    }
    return _has_token_sequence(tokens, torque_sequences)


def _has_fpm_unit_token(tokens):
    if "fpm" in tokens:
        return True
    speed_sequences = {
        ("ft", "per", "min"),
        ("ft", "per", "minute"),
        ("feet", "per", "min"),
        ("feet", "per", "minute"),
    }
    return _has_token_sequence(tokens, speed_sequences)


def _has_gpm_flow_unit_token(lowered, tokens, token_set):
    if "gpm" not in token_set:
        return False
    if lowered.endswith("_gpm"):
        return True
    flow_markers = {
        "flow",
        "flows",
        "flowrate",
        "rate",
        "capacity",
        "leakage",
        "drain",
        "loss",
        "bypass",
        "discharge",
        "supply",
        "return",
    }
    if token_set.intersection(flow_markers):
        return True
    return _has_token_sequence(tokens, {("pump", "gpm"), ("gpm", "pump")})


def _has_clear_hp_result_marker(lowered, token_set):
    if not {"hp", "bhp"}.intersection(token_set):
        return False
    descriptor_markers = (
        "_at_rated_hp",
        "_from_rated_hp",
        "_rated_hp_basis",
        "_rated_power_hp_basis",
        "_hp_basis",
        "_hp_sizing",
    )
    if any(marker in lowered for marker in descriptor_markers):
        return False
    result_markers = (
        "_hp_required",
        "_required_hp",
        "_rated_hp",
        "_rated_power_hp",
        "_hp_with_margin",
        "_hp_available",
        "_available_hp",
    )
    return lowered.endswith(("_hp", "_bhp")) or any(marker in lowered for marker in result_markers)


def _pump_power_unit_from_name(lowered, tokens, token_set):
    if not lowered or not tokens:
        return None
    if _pump_power_name_excluded_as_dimensionless(lowered, tokens, token_set):
        return None

    compact = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    compact_no_sep = compact.replace("_", "")
    if any(
        marker in compact
        for marker in (
            "brake_hp",
            "brake_horsepower",
            "brake_power_hp",
            "calculated_brake_horsepower",
            "pump_brake_horsepower",
        )
    ):
        return "hp"
    if "bhp" in token_set:
        return "hp"

    has_motor_power_unit = bool(token_set.intersection({"hp", "bhp", "horsepower"}))
    if "motor" in token_set and has_motor_power_unit:
        motor_hp_markers = {
            "allowable",
            "available",
            "capacity",
            "max",
            "maximum",
            "motor",
            "nameplate",
            "rated",
            "rating",
        }
        if token_set.intersection(motor_hp_markers) or "pumpmotorhp" in compact_no_sep:
            return "hp"

    return None


def _pump_power_name_excluded_as_dimensionless(lowered, tokens, token_set):
    if "torque" in token_set or _has_torque_unit_token(tokens):
        return True
    if _looks_like_dimensionless_margin_modifier(lowered, token_set):
        return True
    if tokens[-1] in {"factor", "fraction", "ratio", "percent", "pct", "utilization", "loading"}:
        return True
    if lowered.endswith(("_factor", "_fraction", "_ratio", "_percent", "_pct", "_utilization", "_loading")):
        return True
    return False


def _has_token_sequence(tokens, sequences):
    token_tuple = tuple(tokens)
    for sequence in sequences:
        length = len(sequence)
        if length == 0 or length > len(token_tuple):
            continue
        for start in range(0, len(token_tuple) - length + 1):
            if token_tuple[start:start + length] == sequence:
                return True
    return False


def _is_physical_percent_descriptor_unit(unit):
    return unit not in {None, "dimensionless", "percent", "boolean", "unit_expression"} and not _is_textual_unit(unit)


def _dimensionless_modifier_unit_from_name(lowered, token_set):
    if _looks_like_dimensionless_margin_modifier(lowered, token_set):
        return "dimensionless"
    return None


def _looks_like_dimensionless_margin_modifier(lowered, token_set):
    if "margin" not in token_set:
        return False
    if lowered.startswith(("required_design_margin", "design_margin", "safety_margin")):
        return True
    if lowered.endswith(("_design_margin_factor", "_safety_margin_factor", "_margin_factor")):
        return True
    return False


def _temperature_interval_unit_from_name(name_or_lowered, tokens=None, token_set=None):
    lowered = str(name_or_lowered or "").strip().lower()
    if not lowered:
        return None
    tokens = tokens if tokens is not None else [token for token in re.split(r"[_\W]+", lowered) if token]
    token_set = token_set if token_set is not None else set(tokens)
    if not tokens:
        return None
    if token_set.intersection({"resistance", "conductance", "coefficient"}):
        return None

    compact = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    has_celsius_suffix = tokens[-1] in {"c", "degc", "celsius"} or compact.endswith((
        "_delta_c",
        "_delta_deg_c",
        "_delta_degc",
        "_delta_t_c",
        "_delta_t_deg_c",
        "_delta_t_degc",
        "_deltat_c",
        "_deltat_degc",
        "_rise_c",
        "_temperature_rise_c",
        "_temp_rise_c",
        "_delta_temperature_c",
        "_temperature_delta_c",
        "_temperature_difference_c",
        "_temp_difference_c",
        "_temperature_excess_c",
        "_temp_excess_c",
        "_temperature_margin_c",
        "_temp_margin_c",
        "_thermal_margin_c",
        "_deadband_c",
        "_deadband_degc",
        "_control_deadband_c",
        "_control_deadband_degc",
        "_allowable_delta_c",
        "_allowable_delta_degc",
        "_allowed_delta_c",
        "_allowed_delta_degc",
        "_differential_c",
        "_difference_c",
        "_excess_c",
    ))
    has_fahrenheit_suffix = tokens[-1] in {"f", "degf", "fahrenheit"} or compact.endswith((
        "_delta_f",
        "_delta_deg_f",
        "_delta_degf",
        "_delta_t_f",
        "_delta_t_deg_f",
        "_delta_t_degf",
        "_deltat_f",
        "_deltat_degf",
        "_rise_f",
        "_temperature_rise_f",
        "_temp_rise_f",
        "_delta_temperature_f",
        "_temperature_delta_f",
        "_temperature_difference_f",
        "_temp_difference_f",
        "_temperature_excess_f",
        "_temp_excess_f",
        "_temperature_margin_f",
        "_temp_margin_f",
        "_thermal_margin_f",
        "_deadband_f",
        "_deadband_degf",
        "_control_deadband_f",
        "_control_deadband_degf",
        "_allowable_delta_f",
        "_allowable_delta_degf",
        "_allowed_delta_f",
        "_allowed_delta_degf",
        "_differential_f",
        "_difference_f",
        "_excess_f",
    ))
    has_kelvin_suffix = tokens[-1] in {"k", "kelvin"}

    has_interval_marker = (
        _temperature_interval_marker_in_text(compact, token_set)
    )
    if not has_interval_marker:
        return None
    if has_fahrenheit_suffix:
        return "delta_F"
    if has_celsius_suffix or has_kelvin_suffix:
        return "delta_C"
    if compact.endswith((
        "temperature_rise",
        "temp_rise",
        "delta_t",
        "deltat",
        "delta_temperature",
        "temperature_delta",
        "temperature_difference",
        "temp_difference",
        "temperature_excess",
        "temp_excess",
        "temperature_margin",
        "temp_margin",
        "thermal_margin",
        "deadband",
        "control_deadband",
        "allowable_delta",
        "allowed_delta",
        "differential",
        "difference",
        "excess",
    )):
        return "delta_C"
    return None


def _temperature_interval_marker_in_text(compact, token_set):
    return (
        "temperature_rise" in compact
        or "temp_rise" in compact
        or "delta_t" in compact
        or "deltat" in compact
        or "delta_temp" in compact
        or "delta_temperature" in compact
        or "temp_delta" in compact
        or "temperature_delta" in compact
        or "temperature_difference" in compact
        or "temp_difference" in compact
        or "temperature_excess" in compact
        or "temp_excess" in compact
        or "temperature_margin" in compact
        or "temp_margin" in compact
        or "thermal_margin" in compact
        or "control_deadband" in compact
        or "deadband" in token_set
        or "differential" in token_set
        or "difference" in token_set
        or "excess" in token_set
        or ({"temperature", "rise"}.issubset(token_set))
        or ({"temp", "rise"}.issubset(token_set))
        or ({"delta", "t"}.issubset(token_set))
        or ({"delta", "temp"}.issubset(token_set))
        or ({"delta", "temperature"}.issubset(token_set))
        or ({"temp", "delta"}.issubset(token_set))
        or ({"temperature", "delta"}.issubset(token_set))
        or ({"temperature", "difference"}.issubset(token_set))
        or ({"temp", "difference"}.issubset(token_set))
        or ({"temperature", "excess"}.issubset(token_set))
        or ({"temp", "excess"}.issubset(token_set))
        or ({"temperature", "margin"}.issubset(token_set))
        or ({"temp", "margin"}.issubset(token_set))
        or ({"thermal", "margin"}.issubset(token_set))
        or ({"allowable", "delta"}.issubset(token_set))
        or ({"allowed", "delta"}.issubset(token_set))
        or ({"control", "deadband"}.issubset(token_set))
    )


def _temperature_unit_from_name_suffix(lowered, tokens, token_set):
    if not tokens:
        return None
    terminal_unit = tokens[-1]
    temperature_tokens = {"temp", "temperature", "dewpoint"}
    if terminal_unit in {"f", "degf", "fahrenheit"} and token_set.intersection(temperature_tokens):
        return "F"
    if terminal_unit in {"degf", "fahrenheit"}:
        return "F"
    if terminal_unit not in {"c", "degc", "celsius"}:
        if token_set.intersection({"f", "degf", "fahrenheit"}):
            return None
        if token_set.intersection(temperature_tokens):
            return "C"
        if "margin" in token_set and token_set.intersection({"thermal", "temperature", "temp", "dewpoint", "delta"}):
            return "C"
        return None
    if terminal_unit in {"degc", "celsius"}:
        return "C"
    if lowered in {"temp_c", "temperature_c", "delta_t_c"} or lowered.endswith((
        "_temp_c",
        "_temperature_c",
        "_internal_temp_c",
        "_internal_temperature_c",
        "_predicted_temp_c",
        "_predicted_temperature_c",
        "_predicted_internal_temp_c",
        "_predicted_internal_temperature_c",
        "_ambient_temp_c",
        "_ambient_temperature_c",
        "_dewpoint_margin_c",
        "_dew_point_margin_c",
        "_delta_t_c",
    )):
        return "C"
    if token_set.intersection({"temp", "temperature", "dewpoint"}):
        return "C"
    if "margin" in token_set and token_set.intersection({"thermal", "temperature", "temp", "dewpoint", "delta"}):
        return "C"
    return None


def _efficiency_name_is_dimensionless(lowered, token_set):
    if "efficiency" not in token_set:
        return False
    if _compound_unit_from_name_suffix(lowered):
        return False
    if _temperature_unit_from_name_suffix(lowered, [token for token in re.split(r"[_\W]+", lowered) if token], token_set):
        return False
    return True


def _aerodynamic_coefficient_name_is_dimensionless(lowered, token_set):
    if "coefficient" not in token_set and not token_set.intersection({"cl", "clmax", "cd", "cdi", "cd0"}):
        return False
    compact = re.sub(r"[^a-z0-9]+", "_", str(lowered or "")).strip("_")
    if token_set.intersection({"lift", "drag", "induced", "zero", "cl", "clmax", "cd", "cdi", "cd0"}):
        return True
    return any(marker in compact for marker in ("lift_coefficient", "drag_coefficient", "clmax", "cd0"))


def _resistance_per_length_unit_from_name(lowered, token_set):
    if not lowered or "resistance" not in token_set:
        return None
    per_thousand_foot_markers = (
        "_per_1000ft",
        "_per_1000_ft",
        "_per_1000feet",
        "_per_1000_feet",
        "_ohm_per_1000ft",
        "_ohms_per_1000ft",
        "_ohm_per_1000_ft",
        "_ohms_per_1000_ft",
        "_ohm_per_1000feet",
        "_ohms_per_1000feet",
        "_ohm_per_1000_feet",
        "_ohms_per_1000_feet",
    )
    if lowered.endswith(per_thousand_foot_markers):
        return "ohm/1000ft"
    per_foot_markers = (
        "_per_ft",
        "_per_foot",
        "_per_feet",
        "_ohm_per_ft",
        "_ohms_per_ft",
        "_ohm_per_foot",
        "_ohms_per_foot",
    )
    if lowered.endswith(per_foot_markers):
        return "ohm/ft"
    return None


def _explicit_status_name_unit_override(lowered, tokens, token_set):
    if lowered.endswith("_count") or token_set.intersection({"count", "complexity"}):
        return None
    if lowered.endswith(("_str", "_string", "_label", "_name", "_reason", "_message", "_description")) or token_set.intersection(_TEXTUAL_STATUS_NAME_TOKENS):
        return "status_string"
    if _looks_like_boolean_status_name(lowered, tokens, token_set):
        return "boolean"
    if _name_prefers_value_aggregation(lowered, token_set):
        return None
    if "status" in token_set:
        return "status_string"
    return None


def _declared_variable_unit(name, raw_unit, value=None, metadata=None):
    lowered = str(name or "").strip().lower()
    tokens = [token for token in re.split(r"[_\W]+", lowered) if token]
    token_set = set(tokens)
    normalized_raw_unit = normalize_unit(raw_unit)
    metadata_temperature_unit = _temperature_unit_from_metadata(name, raw_unit, metadata)
    if metadata_temperature_unit:
        return metadata_temperature_unit
    temperature_interval_unit = _temperature_interval_unit_from_name(lowered, tokens, token_set)
    if temperature_interval_unit and normalized_raw_unit in {"C", "F", "K", "delta_C", "delta_F", "C_delta", "F_delta", "K_delta"}:
        return temperature_interval_unit
    pump_power_unit = _pump_power_unit_from_name(lowered, tokens, token_set)
    if pump_power_unit and normalized_raw_unit in {"dimensionless", "percent"}:
        return pump_power_unit
    annualized_cost_unit = _annualized_cost_unit_from_name(
        lowered,
        token_set,
    )
    if annualized_cost_unit and normalized_raw_unit in {"USD", "dimensionless", "percent"}:
        return annualized_cost_unit
    corrected = _hydraulic_gpm_cfs_conversion_factor_unit_from_context(name, raw_unit, value)
    if corrected:
        return corrected
    corrected = _hydraulic_231_conversion_factor_unit_from_context(name, raw_unit, value, metadata)
    if corrected:
        return corrected
    return normalized_raw_unit


def _temperature_unit_from_metadata(name, raw_unit, metadata=None):
    if not isinstance(metadata, dict):
        return None
    normalized_raw_unit = normalize_unit(raw_unit)
    if normalized_raw_unit not in {"C", "F", "K", "K_abs", "delta_C", "delta_F", "C_delta", "F_delta", "K_delta"}:
        return None

    kind_text = " ".join(
        str(metadata.get(key) or "")
        for key in ("unit_kind", "quantity_kind", "kind", "type", "role")
    )
    description_text = str(metadata.get("description") or "")
    combined_text = " ".join(part for part in (str(name or ""), kind_text, description_text) if part).lower()
    compact = re.sub(r"[^a-z0-9]+", "_", combined_text).strip("_")
    token_set = {token for token in re.split(r"[^a-z0-9]+", combined_text) if token}

    if _metadata_declares_absolute_temperature(compact, token_set):
        return "K_abs" if normalized_raw_unit == "K_abs" else normalized_raw_unit
    if _metadata_declares_temperature_interval(compact, token_set):
        return _temperature_delta_unit_for_declared_unit(normalized_raw_unit)
    return None


def _metadata_declares_absolute_temperature(compact, token_set):
    return (
        "temperature_absolute" in compact
        or "absolute_temperature" in compact
        or "temp_absolute" in compact
        or {"absolute", "temperature"}.issubset(token_set)
        or {"absolute", "temp"}.issubset(token_set)
    )


def _metadata_declares_temperature_interval(compact, token_set):
    return (
        "temperature_interval" in compact
        or "temp_interval" in compact
        or "temperature_delta" in compact
        or "temp_delta" in compact
        or "temperature_difference" in compact
        or "temp_difference" in compact
        or "temperature_difference" in compact
        or _temperature_interval_marker_in_text(compact, token_set)
        or {"temperature", "interval"}.issubset(token_set)
        or {"temp", "interval"}.issubset(token_set)
    )


def _temperature_delta_unit_for_declared_unit(unit):
    normalized = normalize_unit(unit)
    if normalized in {"F", "delta_F", "F_delta"}:
        return "delta_F"
    if normalized in {"K", "K_delta"}:
        return "K_delta"
    if normalized == "K_abs":
        return "K_delta"
    return "delta_C"


def _inferred_variable_unit_from_context(name, value=None):
    lowered = str(name or "").strip().lower()
    tokens = [token for token in re.split(r"[_\W]+", lowered) if token]
    token_set = set(tokens)
    pump_power_unit = _pump_power_unit_from_name(lowered, tokens, token_set)
    if pump_power_unit:
        return pump_power_unit
    annualized_cost_unit = _annualized_cost_unit_from_name(
        lowered,
        token_set,
    )
    if annualized_cost_unit:
        return annualized_cost_unit
    context_unit = _hydraulic_gpm_cfs_conversion_factor_unit_from_context(name, None, value)
    if context_unit:
        return context_unit
    return _hydraulic_231_conversion_factor_unit_from_context(name, None, value)


def _annualized_cost_unit_from_name(lowered, token_set):
    if not lowered:
        return None
    excluded_tokens = {"installed", "installation", "install", "capital", "capex", "upfront", "purchase", "one", "time"}
    if token_set.intersection(excluded_tokens) or "one_time" in lowered:
        return None
    annual_markers = {"annual", "annualized", "yearly", "year", "years", "yr", "yrs"}
    cost_markers = {"cost", "costs", "savings", "saving", "reduction", "expense", "expenses", "opex"}
    if not token_set.intersection(annual_markers) or not token_set.intersection(cost_markers):
        return None
    if "per_scfm" in lowered or "scfm" in token_set:
        return "USD/scfm/year"
    return "USD/year"


def _hydraulic_231_conversion_factor_unit_from_context(name, raw_unit=None, value=None, metadata=None):
    if not _looks_like_hydraulic_231_conversion_factor(name, metadata):
        return None
    if not _is_231_like_value(value):
        return None

    normalized = normalize_unit(raw_unit)
    if raw_unit in (None, "") or normalized in {"dimensionless", "percent", "min", "in^3/gal"}:
        return "in^3/gal"
    if _is_misdeclared_hydraulic_231_factor_unit(raw_unit, normalized):
        return "in^3/gal"

    dims = _unit_dimensions(normalized)
    if dims in (
        {"in": 3.0, "gal": -1.0},
        {"in": 3.0, "gal": -1.0, "s": 1.0},
        {"in": 3.0, "gal": -1.0, "s": -1.0},
    ):
        return "in^3/gal"
    return None


def _looks_like_hydraulic_231_conversion_factor(name, metadata=None):
    if _looks_like_gpm_to_cubic_inches_per_minute_factor_name(name):
        return True
    if _looks_like_standard_hydraulic_231_factor_name(name):
        return True
    return _metadata_declares_hydraulic_231_factor(name, metadata)


def _looks_like_standard_hydraulic_231_factor_name(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return False
    tokens = [token for token in re.split(r"[^a-z0-9]+", lowered) if token]
    token_set = set(tokens)
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    has_factor = bool(token_set.intersection({"factor", "conversion", "constant"})) or "conversionfactor" in compact
    has_231 = "231" in token_set or compact.endswith("231") or "231" in compact
    if has_231 and has_factor and bool(token_set.intersection({"flow", "hydraulic", "gpm", "gal", "gallon", "volume"})):
        return True
    return compact in {
        "flowconversionfactor231",
        "hydraulicflowconversionfactor231",
        "standardhydraulicfactor231",
        "standardhydraulicconversionfactor231",
    }


def _metadata_declares_hydraulic_231_factor(name, metadata=None):
    if not isinstance(metadata, dict):
        return False
    combined = " ".join(
        str(metadata.get(key) or "")
        for key in ("unit_kind", "quantity_kind", "kind", "type", "role", "description", "source_expression", "normalization_note")
    )
    text = f"{name or ''} {combined}".lower()
    compact = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    token_set = {token for token in re.split(r"[^a-z0-9]+", text) if token}
    if "hydraulic_volume_conversion_factor" in compact:
        return True
    if "231" not in token_set and "231" not in compact:
        return False
    return (
        "in_3_per_gallon" in compact
        or "in3_per_gallon" in compact
        or "cubic_inches_per_gallon" in compact
        or "cubic_in_per_gallon" in compact
        or "in_3_min_to_gpm" in compact
        or "in3_min_to_gpm" in compact
        or "in_2_in_min_to_gpm" in compact
        or "in2_in_min_to_gpm" in compact
        or {"cubic", "inches", "gallon"}.issubset(token_set)
        or {"convert", "gpm"}.issubset(token_set)
        or {"conversion", "gpm"}.issubset(token_set)
    )


def _is_misdeclared_hydraulic_231_factor_unit(raw_unit, normalized=None):
    normalized = normalize_unit(raw_unit) if normalized is None else normalize_unit(normalized)
    if normalized in {"in^3/gpm", "in^3/gal/min", "in^3/gal/minute", "in^3/(gal*min)"}:
        return True
    compact = re.sub(r"[^a-z0-9^*/]+", "", str(raw_unit or "").strip().lower())
    return compact in {
        "in3/gpm",
        "in^3/gpm",
        "in**3/gpm",
        "in3/gal/min",
        "in^3/gal/min",
        "in**3/gal/min",
        "in3/(gal*min)",
        "in^3/(gal*min)",
        "in**3/(gal*min)",
        "cuin/gpm",
        "cu_in/gpm",
        "cubicin/gpm",
        "cubicinches/gpm",
        "cubicin/gal/min",
        "cubicinches/gal/min",
    }


def _hydraulic_gpm_cfs_conversion_factor_unit_from_context(name, raw_unit=None, value=None):
    if not _looks_like_gpm_cfs_conversion_factor_name(name):
        return None
    if not _is_448_831_like_value(value):
        return None

    normalized = normalize_unit(raw_unit)
    if raw_unit in (None, "") or normalized in {"dimensionless", "percent"}:
        return "dimensionless"
    if _is_gpm_per_cfs_conversion_factor_unit(raw_unit, normalized):
        return "dimensionless"
    return None


def _is_gpm_per_cfs_conversion_factor_unit(raw_unit, normalized=None):
    normalized = normalize_unit(raw_unit) if normalized is None else normalize_unit(normalized)
    compact = re.sub(r"[^a-z0-9^*/]+", "", str(raw_unit or "").strip().lower())
    if compact in {
        "gpm*s/ft^3",
        "gpmsec/ft^3",
        "gpmsecond/ft^3",
        "gpmseconds/ft^3",
        "gpm/(ft^3/s)",
        "gpm/cfs",
    }:
        return True
    dims = _unit_dimensions(normalized)
    return dims == {"gal": 1.0, "m": -3.0}


def _looks_like_gpm_to_cubic_inches_per_minute_factor_name(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return False
    tokens = [token for token in re.split(r"[^a-z0-9]+", lowered) if token]
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    if "gpm" not in compact:
        return False
    if not any(marker in compact for marker in ("in3", "cuin", "cubicin", "cubicinch", "cubicinches")):
        return False
    if not (
        {"min", "minute", "minutes"}.intersection(tokens)
        or any(marker in compact for marker in ("permin", "perminute"))
    ):
        return False
    return "factor" in compact or "conversion" in compact


def _looks_like_gpm_cfs_conversion_factor_name(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return False
    tokens = [token for token in re.split(r"[^a-z0-9]+", lowered) if token]
    token_set = set(tokens)
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    has_cfs = "cfs" in token_set or "cfs" in compact
    if "gpm" not in token_set and "gpm" not in compact:
        return False
    if not has_cfs:
        return False
    return (
        "to" in token_set
        or "per" in token_set
        or "conversion" in token_set
        or "factor" in token_set
        or "gpmtocfs" in compact
        or "gpmpercfs" in compact
    )


def _is_448_831_like_value(value):
    if not _is_number(value):
        return False
    return math.isclose(float(value), 448.831, rel_tol=1e-6, abs_tol=1e-3)


def _is_231_like_value(value):
    if not _is_number(value):
        return False
    return math.isclose(float(value), 231.0, rel_tol=1e-9, abs_tol=1e-9)


def _extract_variable_metadata(mcm_request):
    metadata = {}
    variables = mcm_request.get("variables")
    if not isinstance(variables, dict):
        return metadata

    for name, value in variables.items():
        if isinstance(value, dict):
            raw_unit = value.get("unit")
            raw_value = value.get("value")
            unit_declared = raw_unit not in (None, "") and str(raw_unit).strip().lower() not in {"unknown", "unk"}
            suffix_unit = _unit_from_name_suffix(name)
            context_unit = _inferred_variable_unit_from_context(name, raw_value)
            declared_unit = _declared_variable_unit(name, raw_unit, raw_value, value) if unit_declared else None
            if isinstance(raw_value, (list, tuple)):
                if declared_unit:
                    declared_unit = _make_list_unit(declared_unit)
                elif context_unit:
                    context_unit = _make_list_unit(context_unit)
                elif suffix_unit:
                    suffix_unit = _make_list_unit(suffix_unit)
            metadata[str(name)] = {
                "unit": declared_unit if unit_declared else (context_unit or suffix_unit),
                "unit_declared": unit_declared,
                "unit_inferred_from_name": bool(not unit_declared and (context_unit or suffix_unit)),
                "unit_inferred_from_context": bool(not unit_declared and context_unit),
                "description": value.get("description"),
                "source": value.get("source"),
            }
        else:
            context_unit = _inferred_variable_unit_from_context(name, value)
            suffix_unit = _unit_from_name_suffix(name)
            if isinstance(value, (list, tuple)):
                if context_unit:
                    context_unit = _make_list_unit(context_unit)
                elif suffix_unit:
                    suffix_unit = _make_list_unit(suffix_unit)
            metadata[str(name)] = {
                "unit": context_unit or suffix_unit,
                "unit_declared": False,
                "unit_inferred_from_name": bool(context_unit or suffix_unit),
                "unit_inferred_from_context": bool(context_unit),
            }

    return metadata


def _canonical_annualized_currency_unit_alias(text):
    lowered = str(text or "").strip().lower()
    if not lowered:
        return None

    compact = re.sub(r"[^a-z0-9$]+", "_", lowered).strip("_")
    tokens = {token for token in re.split(r"[^a-z0-9$]+", lowered) if token}
    has_currency = "$" in lowered or bool(tokens.intersection({"usd", "dollar", "dollars"}))
    has_year = bool(tokens.intersection({"year", "years", "yr", "yrs"}))
    has_rate_marker = "/" in lowered or " per " in lowered or "_per_" in f"_{compact}_"
    if not (has_currency and has_year and has_rate_marker):
        return None

    if "scfm" in tokens or "scfm" in compact:
        return "USD/scfm/year"
    return "USD/year"


def normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return "dimensionless"

    text = str(unit).strip()
    if not text:
        return "dimensionless"

    list_element_unit = _list_element_unit_text(text)
    if list_element_unit is not None:
        return _make_list_unit(list_element_unit)

    compact = (
        text
        .replace(" ", "")
        .replace("·", "*")
        .replace("°", "deg")
        .replace("·", "*")
        .replace("°", "deg")
        .replace("(", "")
        .replace(")", "")
    )
    compact_lower = compact.lower()
    text_lower = text.lower().strip()

    if text_lower in UNIT_ALIASES:
        return UNIT_ALIASES[text_lower]
    if compact_lower in UNIT_ALIASES:
        return UNIT_ALIASES[compact_lower]
    torque_compound_unit = _canonical_torque_compound_unit_text(compact_lower)
    if torque_compound_unit:
        return torque_compound_unit
    currency_rate_unit = _canonical_annualized_currency_unit_alias(text)
    if currency_rate_unit:
        return currency_rate_unit
    compound_unit = _canonical_compound_unit_alias(compact_lower)
    if compound_unit:
        return compound_unit

    if compact_lower in {"list", "array", "vector"}:
        return "list"

    if compact_lower in {
        "kj/kg/degc",
        "kj/kg*c",
        "kj/kg*degc",
        "kj/kgc",
    }:
        return "kJ/kg/C"

    return text


def _list_element_unit_text(text):
    stripped = text.strip()
    lowered = stripped.lower()
    for prefix in ("list", "array", "vector"):
        if not lowered.startswith(prefix):
            continue
        remainder = stripped[len(prefix) :].lstrip()
        if (
            len(remainder) >= 3
            and remainder[0] in "[("
            and remainder[-1] in "])"
        ):
            return remainder[1:-1]
    return None


def _canonical_compound_unit_alias(text):
    text = str(text or "").strip()
    if not text or not any(operator in text for operator in ("*", "/")):
        return None

    tokens = re.split(r"([*/])", text)
    if not tokens or len(tokens) < 3:
        return None

    normalized = []
    changed = False
    for token in tokens:
        if token in {"*", "/"}:
            normalized.append(token)
            continue
        if not token:
            return None
        unit = _canonical_simple_unit_alias(token)
        if not unit:
            return None
        normalized.append(unit)
        changed = changed or unit != token

    result = "".join(normalized)
    return result if changed else None


def _canonical_simple_unit_alias(token):
    text = str(token or "").strip()
    if not text:
        return None
    lowered = text.lower()
    compact = lowered.replace(" ", "")
    if lowered in UNIT_ALIASES:
        return UNIT_ALIASES[lowered]
    if compact in UNIT_ALIASES:
        return UNIT_ALIASES[compact]
    if re.fullmatch(r"[A-Za-z_$]+(?:\^\d+(?:\.\d+)?)?", text):
        return text
    return None


def _canonical_torque_compound_unit_text(text):
    normalized = str(text or "").strip().lower()
    if not normalized:
        return None

    original = normalized
    replacements = (
        ("lbf-ft", "lbf*ft"),
        ("ft-lbf", "lbf*ft"),
        ("lb-ft", "lbf*ft"),
        ("ft-lb", "lbf*ft"),
        ("lbf_ft", "lbf*ft"),
        ("ft_lbf", "lbf*ft"),
        ("lb_ft", "lbf*ft"),
        ("ft_lb", "lbf*ft"),
        ("lbfft", "lbf*ft"),
        ("lbft", "lbf*ft"),
    )
    for source, target in replacements:
        normalized = re.sub(rf"(?<![a-z0-9]){re.escape(source)}(?![a-z0-9])", target, normalized)

    return normalized if normalized != original else None


def _normalize_list_element_unit(element_unit):
    text = str(element_unit or "").strip()
    lowered = re.sub(r"[\s_]+", "_", text.lower()).strip("_")
    if lowered in {"string", "str", "text"}:
        return "string"
    if lowered in {"label", "name", "label_string"}:
        return "label_string"
    return normalize_unit(element_unit)


def _make_list_unit(element_unit=None):
    if element_unit is None:
        return "list"
    normalized = _normalize_list_element_unit(element_unit)
    if normalized in {None, "", "list"}:
        return "list"
    if _is_list_unit(normalized):
        return normalized
    return f"list[{normalized}]"


def _is_list_unit(unit):
    normalized = normalize_unit(unit)
    return normalized == "list" or (
        isinstance(normalized, str)
        and normalized.startswith("list[")
        and normalized.endswith("]")
    )


def _list_element_unit(unit):
    normalized = normalize_unit(unit)
    if normalized == "list":
        return None
    if isinstance(normalized, str) and normalized.startswith("list[") and normalized.endswith("]"):
        return _normalize_list_element_unit(normalized[5:-1])
    return None


def normalize_eas_mode(mode: str | None) -> str | None:
    if mode is None:
        return None
    text = str(mode).strip().lower()
    if not text:
        return ""
    normalized = re.sub(r"[\s_]+", "-", text)
    normalized = re.sub(r"-+", "-", normalized)
    aliases = {
        "explore-novel-solution": "explore-novel-solution",
        "solve-problem": "solve-problem",
        "solve-the-problem": "solve-problem",
        "review-design": "review-design",
        "diagnose-root-cause": "diagnose-root-cause",
        "suggest-improvements": "suggest-improvements",
    }
    return aliases.get(normalized, normalized)


def infer_rhs_unit(rhs_expression: str, variable_units: dict, names: dict | None = None) -> dict:
    try:
        rhs_expression = _normalize_boolean_operators(rhs_expression)
        tree = ast.parse(rhs_expression, mode="eval")
        pump_power_result = _pump_horsepower_formula_unit_result(tree.body, variable_units, names)
        if pump_power_result:
            return pump_power_result
        return _infer_unit_node(tree.body, variable_units, names=names)
    except KeyError as e:
        return _unit_result(
            None,
            "unknown",
            "warning",
            f"Unit validation could not find unit for variable: {e.args[0]}",
        )
    except Exception as e:
        return _unit_result(
            None,
            "unknown",
            "info",
            f"Unit compatibility was not validated for this expression: {e}",
        )


def _evaluate_units_rhs(rhs_expression, variable_units):
    try:
        rhs_expression = _normalize_boolean_operators(rhs_expression)
        tree = ast.parse(rhs_expression, mode="eval")
    except SyntaxError:
        return None

    node = tree.body
    if not _is_units_call(node):
        return None

    try:
        unit_result = _infer_dimensional_unit_node(node.args[0], variable_units)
    except KeyError as e:
        unit_result = _unit_result(
            None,
            "unknown",
            "warning",
            f"Unit extraction could not find unit for variable: {e.args[0]}",
        )

    inferred_unit = unit_result.get("unit")
    display_unit = _display_unit(inferred_unit)
    status = unit_result.get("status", "unknown")
    severity = unit_result.get("severity", "info")

    if status == "unknown":
        message = unit_result.get("message", "Unit extraction could not determine the expression unit.")
    else:
        message = f"Unit extraction computed expression unit {display_unit}."

    return {
        "value": display_unit,
        "unit_validation": {
            "lhs_expected_unit": "dimensionless",
            "rhs_inferred_unit": "dimensionless",
            "status": status,
            "severity": severity,
            "message": message,
            "rhs_expression_unit": display_unit,
            "compatible": None,
        },
    }


def _evaluate_unit_literal_rhs(rhs_expression):
    try:
        rhs_expression = _normalize_boolean_operators(rhs_expression)
        tree = ast.parse(rhs_expression, mode="eval")
    except SyntaxError:
        return None

    unit = _render_unit_node(tree.body)
    if not unit or not _looks_like_unit_expression(unit):
        return None

    display_unit = _display_unit(unit)
    return {
        "value": display_unit,
        "unit_validation": {
            "lhs_expected_unit": "dimensionless",
            "rhs_inferred_unit": "dimensionless",
            "status": "valid",
            "severity": "info",
            "message": f"Unit literal expression computed unit {display_unit}.",
            "rhs_expression_unit": display_unit,
            "compatible": None,
        },
    }


def _evaluate_dimensional_check_rhs(rhs_expression, variable_units):
    try:
        rhs_expression = _normalize_boolean_operators(rhs_expression)
        tree = ast.parse(rhs_expression, mode="eval")
    except SyntaxError:
        return None

    node = tree.body
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
        return None

    if not isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
        return None

    dim_call = node.left
    expected_node = node.comparators[0]
    if not _is_dim_call(dim_call):
        return None

    expected_unit_result = _dimensional_unit_from_node(expected_node, variable_units)
    if not expected_unit_result:
        return None
    expected_unit = expected_unit_result.get("unit")

    inner_node = dim_call.args[0]
    try:
        inner_unit_result = _infer_dimensional_unit_node(inner_node, variable_units)
    except KeyError as e:
        inner_unit_result = _unit_result(
            None,
            "unknown",
            "warning",
            f"Dimensional check could not find unit for variable: {e.args[0]}",
        )
    inner_unit = inner_unit_result.get("unit")

    unknown_unit_result = _first_unknown_unit(inner_unit_result, expected_unit_result)
    if unknown_unit_result:
        compatible = False
        status = "unknown"
        severity = "warning"
        message = unknown_unit_result.get("message", "Dimensional compatibility could not be determined.")
    else:
        compatible = _units_compatible(inner_unit, expected_unit)
        status = "valid"
        severity = "info"
        inner_display = _display_unit(inner_unit)
        expected_display = _display_unit(expected_unit)
        if compatible:
            message = f"Unit compatibility check completed: {inner_display} is compatible with {expected_display}."
        else:
            message = f"Unit compatibility check completed: {inner_display} is not compatible with {expected_display}."

    value = compatible
    if isinstance(node.ops[0], ast.NotEq):
        value = not compatible

    return {
        "value": value,
        "unit_validation": {
            "lhs_expected_unit": "boolean",
            "rhs_inferred_unit": "boolean",
            "status": status,
            "severity": severity,
            "message": message,
            "rhs_expression_unit": _display_unit(inner_unit),
            "expected_physical_unit": _display_unit(expected_unit),
            "compatible": compatible,
        },
    }


def _dimensional_unit_from_node(node, variable_units):
    if _is_dim_call(node):
        try:
            return _infer_dimensional_unit_node(node.args[0], variable_units)
        except KeyError as e:
            return _unit_result(
                None,
                "unknown",
                "warning",
                f"Dimensional check could not find unit for variable: {e.args[0]}",
            )

    expected_unit = _unit_symbol_from_node(node)
    if expected_unit:
        return _unit_result(expected_unit, "valid", "info", f"Expected unit is {expected_unit}.")

    return None


def _is_dim_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "dim"
        and len(node.args) == 1
        and not node.keywords
    )


def _is_units_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"units", "unit"}
        and len(node.args) == 1
        and not node.keywords
    )


def _is_sqrt_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "sqrt"
        and len(node.args) == 1
        and not node.keywords
    )


def _infer_sqrt_unit(argument_node, variable_units, infer_node):
    argument = infer_node(argument_node, variable_units)
    invalid = _first_invalid_unit(argument)
    if invalid:
        return invalid
    if argument.get("status") == "unknown":
        return _unit_result(None, "unknown", "info", "Square-root unit compatibility is unknown.")
    unit = _compose_power_unit(argument.get("unit"), 0.5)
    return _unit_result(unit, "valid", "info", f"Square-root unit rule produced {unit}.")


def _unit_symbol_from_node(node):
    if isinstance(node, ast.Name):
        return normalize_unit(node.id)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return normalize_unit(node.value)
    if isinstance(node, ast.BinOp):
        rendered = _render_unit_node(node)
        return normalize_unit(rendered) if rendered else None
    return None


def _render_unit_node(node):
    if isinstance(node, ast.Name):
        return normalize_unit(node.id)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return normalize_unit(node.value)
    if isinstance(node, ast.BinOp):
        left = _render_unit_node(node.left)
        right = _render_unit_node(node.right)
        if not left or not right:
            return None
        if isinstance(node.op, ast.Mult):
            return _compose_product_unit(left, right)
        if isinstance(node.op, ast.Div):
            return _compose_ratio_unit(left, right)
        if isinstance(node.op, ast.Pow):
            exponent = _constant_numeric_value(node.right)
            if exponent is not None:
                return _compose_power_unit(left, exponent)
    return None


def _infer_dimensional_unit_node(node, variable_units):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return _unit_result("boolean", "valid", "info", "Boolean literal is boolean.")
        if isinstance(node.value, (int, float, bool)):
            return _unit_result("dimensionless", "valid", "info", "Numeric literal is dimensionless.")
        if isinstance(node.value, str):
            unit = _string_literal_unit(node.value)
            return _unit_result(unit, "valid", "info", f"String literal is {unit}.")
        if node.value is None:
            return _unit_result("dimensionless", "valid", "info", "Null literal is dimensionless.")
        return _unit_result(None, "unknown", "info", "Non-numeric literal unit is unknown.")

    if isinstance(node, ast.Name):
        if node.id not in variable_units:
            suffix_unit = _unit_from_name_suffix(node.id)
            if suffix_unit:
                return _unit_result(suffix_unit, "valid", "info", f"Variable {node.id} unit inferred from name suffix as {suffix_unit}.")
            raise KeyError(node.id)
        unit = normalize_unit(variable_units.get(node.id))
        return _unit_result(unit, "valid", "info", f"Variable {node.id} has unit {unit}.")

    if isinstance(node, ast.UnaryOp):
        return _infer_dimensional_unit_node(node.operand, variable_units)

    if isinstance(node, ast.BinOp):
        left = _infer_dimensional_unit_node(node.left, variable_units)
        right = _infer_dimensional_unit_node(node.right, variable_units)
        invalid = _first_invalid_unit(left, right)
        if invalid:
            return invalid
        if left["status"] == "unknown" or right["status"] == "unknown":
            return _unit_result(None, "unknown", "warning", "Dimensional unit inference is unknown.")
        if isinstance(node.op, ast.Pow):
            return _combine_power_units(left, right, node.right)
        if isinstance(node.op, ast.Mult):
            return _unit_result(
                _compose_product_unit(left["unit"], right["unit"]),
                "valid",
                "info",
                "Composite multiplication unit inferred.",
            )
        if isinstance(node.op, ast.Div):
            numeric_length_conversion = _numeric_inch_length_division_unit_result(
                left["unit"],
                right["unit"],
                node.left,
                node.right,
            )
            if numeric_length_conversion:
                return numeric_length_conversion
            return _unit_result(
                _compose_ratio_unit(left["unit"], right["unit"]),
                "valid",
                "info",
                "Composite division unit inferred.",
            )
        if isinstance(node.op, (ast.Add, ast.Sub)):
            numeric_literal_result = _numeric_literal_add_sub_unit(left, node.left, right, node.right)
            if numeric_literal_result:
                return numeric_literal_result
            return _combine_add_sub_units(left, right, node.left, node.right, node.op)
        return _unit_result(None, "unknown", "warning", "Dimensional operator is not supported.")

    if isinstance(node, ast.Call):
        if _is_dim_call(node):
            return _infer_dimensional_unit_node(node.args[0], variable_units)
        if _is_minmax_call(node):
            return _infer_minmax_unit(node, variable_units)
        if _is_sqrt_call(node):
            return _infer_sqrt_unit(node.args[0], variable_units, _infer_dimensional_unit_node)
        return _unit_result(None, "unknown", "warning", "Function calls are not supported inside dim().")

    return _unit_result(None, "unknown", "warning", f"Dimensional inference does not support {type(node).__name__}.")


def _compose_product_unit(left_unit, right_unit):
    left_unit = normalize_unit(left_unit)
    right_unit = normalize_unit(right_unit)
    if left_unit == "dimensionless":
        return right_unit
    if right_unit == "dimensionless":
        return left_unit
    if left_unit == "percent" and right_unit == "percent":
        return "dimensionless"
    if left_unit == "percent":
        return right_unit
    if right_unit == "percent":
        return left_unit
    if (
        (_is_cycle_rate_unit(left_unit) and _is_scf_per_cycle_unit(right_unit))
        or (_is_scf_per_cycle_unit(left_unit) and _is_cycle_rate_unit(right_unit))
    ):
        return "scfm"
    thermal_interval = _thermal_resistance_product_unit(left_unit, right_unit)
    if thermal_interval:
        return thermal_interval
    conversion = _conversion_ratio_multiply_result_unit(left_unit, right_unit)
    if conversion:
        return conversion
    conversion = _conversion_ratio_multiply_result_unit(right_unit, left_unit)
    if conversion:
        return conversion

    known = {
        ("kg", "kJ/kg/C"): "kJ/C",
        ("kJ/kg/C", "kg"): "kJ/C",
        ("kJ/C", "C"): "kJ",
        ("C", "kJ/C"): "kJ",
        ("V", "A"): "W",
        ("A", "V"): "W",
        ("V", "Ah"): "Wh",
        ("Ah", "V"): "Wh",
        ("A", "ohm"): "V",
        ("ohm", "A"): "V",
        ("A", "h"): "Ah",
        ("h", "A"): "Ah",
        ("W", "C/W"): "delta_C",
        ("C/W", "W"): "delta_C",
        ("W", "K/W"): "delta_C",
        ("K/W", "W"): "delta_C",
        ("ft", "ft"): "ft^2",
        ("ft^2", "ft"): "ft^3",
        ("ft", "ft^2"): "ft^3",
        ("ft", "rpm"): "fpm",
        ("rpm", "ft"): "fpm",
        ("fpm", "ft^2"): "cfm",
        ("ft^2", "fpm"): "cfm",
    }
    if (left_unit, right_unit) in known:
        return known[(left_unit, right_unit)]

    reduced = _compose_units_by_dimensions(left_unit, right_unit, "*")
    if reduced:
        return reduced

    return f"{left_unit}*{right_unit}"


def _thermal_resistance_product_unit(left_unit, right_unit):
    pair = (normalize_unit(left_unit), normalize_unit(right_unit))
    if pair in {
        ("W", "C/W"),
        ("C/W", "W"),
        ("W", "K/W"),
        ("K/W", "W"),
    }:
        return "delta_C"
    return None


def _thermal_conductance_division_unit(left_unit, right_unit):
    pair = (normalize_unit(left_unit), normalize_unit(right_unit))
    if pair in {
        ("W", "W/C"),
        ("W", "W/K"),
        ("kW", "kW/C"),
        ("kW", "kW/K"),
    }:
        return "delta_C"
    return None


def _compose_ratio_unit(left_unit, right_unit):
    left_unit = normalize_unit(left_unit)
    right_unit = normalize_unit(right_unit)
    if right_unit in {"dimensionless", "percent"}:
        return left_unit
    if left_unit == right_unit:
        return "dimensionless"
    thermal_interval = _thermal_conductance_division_unit(left_unit, right_unit)
    if thermal_interval:
        return thermal_interval
    if left_unit == "Wh" and right_unit == "W":
        return "h"
    if left_unit == "kWh" and right_unit == "kW":
        return "h"
    if left_unit == "Ah" and right_unit == "A":
        return "h"
    if left_unit == "kg" and right_unit == "C":
        return "kg/C"
    if left_unit == "in" and _is_inches_per_foot_unit(right_unit):
        return "ft"
    if left_unit == "ft" and right_unit == "min":
        return "fpm"
    if left_unit == "ft" and right_unit == "s":
        return "ft/s"
    if left_unit == "m" and right_unit == "s":
        return "m/s"
    if _is_cfm_unit(left_unit) and _is_fpm_unit(right_unit):
        return "ft^2"
    if _is_cfm_unit(left_unit) and _is_square_foot_unit(right_unit):
        return "fpm"
    if _is_cfs_unit(left_unit) and _is_square_foot_unit(right_unit):
        return "ft/s"
    conversion = _conversion_ratio_divide_result_unit(left_unit, right_unit)
    if conversion:
        return conversion
    reduced = _compose_units_by_dimensions(left_unit, right_unit, "/")
    if reduced:
        return reduced
    return f"{left_unit}/{right_unit}"


def _compose_power_unit(base_unit, exponent):
    base_unit = normalize_unit(base_unit)
    if base_unit in {None, "dimensionless", "percent"}:
        return "dimensionless"
    if math.isclose(float(exponent), 0.0, abs_tol=1e-12):
        return "dimensionless"
    if math.isclose(float(exponent), 1.0, abs_tol=1e-12):
        return base_unit

    exponent_int = _canonical_exponent(float(exponent))
    known = {
        ("ft", 2): "ft^2",
        ("ft", 3): "ft^3",
        ("ft^2", 0.5): "ft",
        ("ft^3", 1 / 3): "ft",
        ("in", 2): "in^2",
        ("in", 3): "in^3",
        ("in", 4): "in^4",
        ("in^2", 0.5): "in",
        ("in^3", 1 / 3): "in",
        ("in^4", 0.5): "in^2",
        ("m^2", 0.5): "m",
        ("m^3", 1 / 3): "m",
    }
    for (known_base_unit, known_exponent), known_result in known.items():
        if base_unit == known_base_unit and math.isclose(float(exponent), known_exponent, rel_tol=0.0, abs_tol=1e-12):
            return known_result

    dims = _unit_dimensions(base_unit)
    if dims is not None:
        return _canonical_unit_from_dimensions(_scale_unit_dimensions(dims, float(exponent)))

    return f"{base_unit}^{exponent_int}"


def _conversion_ratio_multiply_result_unit(source_unit, factor_unit):
    parts = _simple_conversion_ratio_parts(factor_unit)
    if not parts:
        return None
    numerator, denominator = parts
    source_unit = normalize_unit(source_unit)
    if source_unit == denominator:
        return numerator
    return None


def _conversion_ratio_divide_result_unit(source_unit, factor_unit):
    parts = _simple_conversion_ratio_parts(factor_unit)
    if not parts:
        return None
    numerator, denominator = parts
    source_unit = normalize_unit(source_unit)
    if source_unit == numerator:
        return denominator
    return None


def _simple_conversion_ratio_parts(unit):
    normalized = normalize_unit(unit)
    if not isinstance(normalized, str) or normalized.count("/") != 1:
        return None
    numerator, denominator = normalized.split("/", 1)
    numerator = normalize_unit(numerator)
    denominator = normalize_unit(denominator)
    if not numerator or not denominator:
        return None
    if numerator in {"dimensionless", "percent", "boolean", "status_string"} or _is_textual_unit(numerator):
        return None
    if denominator in {"dimensionless", "percent", "boolean", "status_string"} or _is_textual_unit(denominator):
        return None
    if _is_list_unit(numerator) or _is_list_unit(denominator):
        return None
    return numerator, denominator


def _units_compatible(actual_unit, expected_unit):
    return _units_validation_compatible(actual_unit, expected_unit)


def _display_unit(unit):
    normalized = normalize_unit(unit)
    if normalized is None:
        return None
    return normalized.replace("/C", "/degC")


def _looks_like_unit_output(name):
    lowered = str(name).lower()
    return "unit" in lowered or "dimension" in lowered


def _looks_like_unit_expression(unit):
    if unit in {"dimensionless", "boolean"}:
        return False
    known_units = {
        "C", "F", "delta_F", "kg", "kg/m^3", "N", "Pa", "J", "W", "kW", "Wh", "kWh", "kJ", "h", "kJ/kg/C", "kJ/C", "kg/C",
        "in", "in^2", "in^3", "in^4", "lbf", "psi", "psf", "lbf_in", "ft", "ft^2", "ft^3", "ft/s", "m", "m^2", "m^3", "m/s",
        "cfm", "fpm", "ft^3/s", "scfm", "cycle/min", "scf/cycle", "gpm", "rpm", "hp", "BTU/hr", "BTU/hr/gpm/F",
        "BTU/lb/F", "lb", "lb/gal", "lb/min", "lb/hr",
        "inH2O", "V", "A", "Ah", "ohm", "ohm/ft", "ohm/1000ft", "1/ft",
        "USD", "USD/year", "USD/scfm/year", "year",
    }
    return unit in known_units or "/" in unit or "*" in unit


def validate_equation_units(
    lhs: str,
    rhs: str,
    variable_units: dict,
    known_output_units: dict | None = None,
    names: dict | None = None,
) -> dict:
    known_output_units = known_output_units or {}
    lhs_expected_unit, lhs_expected_unit_source, lhs_expected_unit_raw = _lhs_expected_unit_for_validation(
        lhs,
        variable_units,
        known_output_units,
    )
    inferred = infer_rhs_unit(rhs, variable_units, names=names)
    rhs_inferred_unit = inferred.get("unit")
    lhs_expected_unit = _adjust_lhs_expected_unit_for_list_rhs(lhs, rhs, lhs_expected_unit, rhs_inferred_unit)
    if (
        _is_list_unit(lhs_expected_unit)
        and _is_list_unit(rhs_inferred_unit)
        and normalize_unit(_list_element_unit(rhs_inferred_unit)) == "dimensionless"
        and _rhs_list_contains_only_nullish_or_numeric_literals(rhs)
        and normalize_unit(_list_element_unit(lhs_expected_unit)) not in {None, "dimensionless"}
    ):
        rhs_inferred_unit = lhs_expected_unit
        inferred = {
            **inferred,
            "unit": rhs_inferred_unit,
            "status": "valid",
            "severity": "info",
            "message": f"Numeric list literal inherits LHS list unit {lhs_expected_unit}.",
        }

    result = {
        "lhs_expected_unit": lhs_expected_unit,
        "lhs_expected_unit_source": lhs_expected_unit_source,
        "lhs_expected_unit_raw": lhs_expected_unit_raw,
        "rhs_inferred_unit": rhs_inferred_unit,
        "status": inferred.get("status", "unknown"),
        "severity": inferred.get("severity", "info"),
        "message": inferred.get("message", "Unit compatibility was not validated."),
    }

    selected_branch_result = _selected_branch_unit_validation(
        lhs,
        rhs,
        variable_units,
        names,
        lhs_expected_unit,
    )
    if selected_branch_result:
        result.update(selected_branch_result)
        return result

    fluid_rule_result = _fluid_thermal_unit_validation(lhs, rhs, variable_units, names, lhs_expected_unit)
    if fluid_rule_result:
        result.update(fluid_rule_result)
        return result

    conversion_rule_result = _explicit_conversion_unit_validation(
        rhs,
        lhs_expected_unit,
        rhs_inferred_unit,
        variable_units,
    )
    if conversion_rule_result:
        result.update(conversion_rule_result)
        return result

    hydraulic_head_result = _hydraulic_head_equation_unit_validation(
        lhs,
        rhs,
        lhs_expected_unit,
        rhs_inferred_unit,
        variable_units,
    )
    if hydraulic_head_result:
        result.update(hydraulic_head_result)
        return result

    if inferred.get("status") == "invalid":
        return result

    if inferred.get("status") == "unknown":
        return result

    temperature_interval = _temperature_interval_unit_result(lhs, rhs, variable_units, lhs_expected_unit)
    if temperature_interval:
        result.update(temperature_interval)
        return result

    if _is_temperature_interval_lhs(lhs, lhs_expected_unit) and _is_temperature_interval_unit(rhs_inferred_unit):
        result.update({
            "status": "valid",
            "severity": "info",
            "message": f"Unit validation passed: {rhs_inferred_unit} temperature interval is compatible with {lhs}.",
        })
        return result

    if lhs_expected_unit == "percent" and rhs_inferred_unit == "dimensionless":
        result.update({
            "rhs_inferred_unit": "percent",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: percent output is compatible with dimensionless ratio multiplied by 100.",
        })
        return result

    if lhs_expected_unit and rhs_inferred_unit == "dimensionless" and _rhs_is_numeric_literal(rhs):
        result.update({
            "rhs_inferred_unit": lhs_expected_unit,
            "status": "valid",
            "severity": "info",
            "message": f"Unit validation passed: numeric literal inherits LHS unit {lhs_expected_unit}.",
        })
        return result

    if lhs_expected_unit and rhs_inferred_unit and not _units_validation_compatible(lhs_expected_unit, rhs_inferred_unit):
        hydraulic_head_result = _hydraulic_head_equation_unit_validation(
            lhs,
            rhs,
            lhs_expected_unit,
            rhs_inferred_unit,
            variable_units,
        )
        if hydraulic_head_result:
            result.update(hydraulic_head_result)
            return result
        result.update({
            "status": "invalid",
            "severity": "warning",
            "message": f"LHS unit {lhs_expected_unit} is incompatible with inferred RHS unit {rhs_inferred_unit}.",
        })
        return result

    result.update({
        "status": "valid",
        "severity": "info",
        "message": f"Unit validation passed: RHS inferred as {rhs_inferred_unit}.",
    })
    return result


def _lhs_expected_unit_for_validation(lhs, variable_units, known_output_units):
    if lhs in known_output_units:
        raw_unit = known_output_units.get(lhs)
        return normalize_unit(raw_unit), "equation_output_metadata", raw_unit
    if lhs in variable_units:
        raw_unit = variable_units.get(lhs)
        return normalize_unit(raw_unit), "variable_metadata", raw_unit

    suffix_unit = _unit_from_name_suffix(lhs)
    if suffix_unit:
        return suffix_unit, "suffix_inference", suffix_unit
    return None, "unresolved", None


def _hydraulic_head_equation_unit_validation(lhs, rhs, lhs_expected_unit, rhs_inferred_unit, variable_units):
    lhs_expected_unit = normalize_unit(lhs_expected_unit)
    rhs_inferred_unit = normalize_unit(rhs_inferred_unit)
    if not _is_hydraulic_head_family_unit(lhs_expected_unit):
        return None
    if not _name_has_hydraulic_head_context(lhs):
        return None
    if _name_has_geometry_length_context(lhs) and not _name_has_hydraulic_head_context(lhs):
        return None
    if _is_hydraulic_head_family_unit(rhs_inferred_unit):
        if rhs_inferred_unit == "ft" and not _rhs_expression_has_hydraulic_head_context(rhs):
            return None
        if (
            _rhs_expression_has_geometry_only_length_context(rhs)
            and not _rhs_is_supported_hydraulic_head_loss_formula(rhs)
        ):
            return None
        return {
            "rhs_inferred_unit": "ft_head",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: hydraulic head/TDH context treats ft, ft_head, and ft_water as compatible head units.",
        }

    safe_rhs_unit = _infer_hydraulic_head_rhs_unit(rhs, variable_units)
    if safe_rhs_unit:
        return {
            "rhs_inferred_unit": safe_rhs_unit,
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: hydraulic head expression canonicalized to ft_head.",
        }
    return None


def _rhs_is_supported_hydraulic_head_loss_formula(rhs):
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return False
    if any(isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)) for node in ast.walk(tree.body)):
        return False
    factors = _multiplicative_factors(tree.body)
    names = [node.id for node, _sign in factors if isinstance(node, ast.Name)]
    if not names:
        return False
    has_head_loss_rate = any(_name_is_hydraulic_head_loss_rate(name) for name in names)
    has_geometry_length = any(_name_has_geometry_length_context(name) for name in names)
    return has_head_loss_rate and has_geometry_length


def _name_is_hydraulic_head_loss_rate(name):
    lowered = str(name or "").strip().lower()
    if not _name_has_hydraulic_head_context(lowered):
        return False
    compact = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    tokens = {token for token in re.split(r"[_\W]+", lowered) if token}
    return (
        "per" in tokens
        or "gradient" in tokens
        or "loss_per" in compact
        or "head_per" in compact
        or "per_100ft" in compact
        or "per_100_ft" in compact
    )


def _rhs_expression_has_hydraulic_head_context(rhs):
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return False
    return _node_has_hydraulic_head_context(tree.body)


def _rhs_expression_has_geometry_only_length_context(rhs):
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return False
    return _node_has_geometry_only_length_context(tree.body)


def _infer_hydraulic_head_rhs_unit(rhs, variable_units):
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return None
    inferred = _infer_unit_node(tree.body, variable_units)
    if inferred.get("status") == "valid" and _is_hydraulic_head_family_unit(inferred.get("unit")):
        if _node_has_hydraulic_head_context(tree.body) and not _node_has_geometry_only_length_context(tree.body):
            return "ft_head"
    return None


def _adjust_lhs_expected_unit_for_list_rhs(lhs, rhs, lhs_expected_unit, rhs_inferred_unit):
    if not _is_list_unit(rhs_inferred_unit):
        return lhs_expected_unit
    if _is_list_unit(lhs_expected_unit):
        if _list_element_unit(lhs_expected_unit) is None and _list_element_unit(rhs_inferred_unit) is not None:
            return rhs_inferred_unit
        return lhs_expected_unit
    if lhs_expected_unit:
        return _make_list_unit(lhs_expected_unit)
    inferred = _list_lhs_element_unit_from_name(lhs)
    if inferred:
        return _make_list_unit(inferred)
    if _lhs_name_prefers_list_unit(lhs) or _rhs_is_list_literal(rhs):
        if _list_element_unit(rhs_inferred_unit) is not None:
            return rhs_inferred_unit
        return _make_list_unit()
    return lhs_expected_unit


def _list_lhs_element_unit_from_name(lhs):
    lowered = str(lhs or "").strip().lower()
    tokens = [token for token in re.split(r"[_\W]+", lowered) if token]
    token_set = set(tokens)
    if lowered.endswith(("_usd_list", "_cost_usd_list", "_costs_usd_list")) or token_set.intersection({"usd", "cost", "costs", "price", "prices", "budget", "budgets"}):
        return "USD"
    suffix_unit = _unit_from_name_suffix(lhs)
    if suffix_unit:
        return suffix_unit
    unit_token = _list_value_element_unit_from_tokens(tokens)
    if unit_token:
        return unit_token
    if token_set.intersection({"label", "labels", "name", "names", "string", "strings"}):
        return "label_string"
    if token_set.intersection({"flag", "flags", "viability"}):
        return "boolean"
    return None


def _list_value_element_unit_from_tokens(tokens):
    if not tokens:
        return None
    reduced = [
        token
        for token in tokens
        if token not in {
            "list",
            "lists",
            "value",
            "values",
            "val",
            "vals",
            "candidate",
            "candidates",
            "option",
            "options",
            "viable",
            "non",
            "selected",
            "available",
        }
    ]
    if len(reduced) == 1 and re.fullmatch(r"[a-z]", reduced[0]):
        return None
    return _physical_unit_from_name_token_sequence(reduced)


def _lhs_name_prefers_list_unit(lhs):
    lowered = str(lhs or "").strip().lower()
    return (
        lowered.endswith(("_list", "_values", "_flags", "_labels", "_names"))
        or "_candidates_" in lowered
        or "candidate_labels" in lowered
        or "candidate_viability_flags" in lowered
    )


def _rhs_is_list_literal(rhs):
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return False
    return isinstance(tree.body, (ast.List, ast.Tuple))


def _rhs_list_contains_only_nullish_or_numeric_literals(rhs):
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return False
    if not isinstance(tree.body, (ast.List, ast.Tuple)):
        return False
    return all(_is_null_node(item) or _is_numeric_constant(item) for item in tree.body.elts)


def _fluid_thermal_unit_validation(lhs, rhs, variable_units, names, lhs_expected_unit):
    pump_result = _pump_brake_horsepower_unit_validation(rhs, variable_units, names, lhs_expected_unit)
    if pump_result:
        return pump_result
    return None


def _explicit_conversion_unit_validation(rhs, lhs_expected_unit, rhs_inferred_unit, variable_units=None):
    lhs_expected_unit = normalize_unit(lhs_expected_unit)
    rhs_inferred_unit = normalize_unit(rhs_inferred_unit)
    if not lhs_expected_unit or not rhs_inferred_unit:
        return None
    variable_units = variable_units or {}

    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return None

    node = tree.body
    if (
        lhs_expected_unit == "min"
        and rhs_inferred_unit == "h"
        and _has_numeric_conversion_factor(node, 1, 60.0)
        and _has_wh_per_w_runtime_division(node, variable_units)
    ):
        return {
            "rhs_inferred_unit": "min",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: Wh/W runtime converted to minutes by explicit *60 factor.",
        }

    if (
        _is_square_foot_unit(lhs_expected_unit)
        and _is_square_inch_unit(rhs_inferred_unit)
        and _has_numeric_conversion_factor(node, -1, 144.0)
    ):
        return {
            "rhs_inferred_unit": "ft^2",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: explicit square-inch to square-foot conversion factor /144 is present.",
        }

    if (
        _is_square_inch_unit(lhs_expected_unit)
        and _is_square_foot_unit(rhs_inferred_unit)
        and _has_numeric_conversion_factor(node, 1, 144.0)
    ):
        return {
            "rhs_inferred_unit": "in^2",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: explicit square-foot to square-inch conversion factor *144 is present.",
        }

    if (
        lhs_expected_unit == "ft"
        and rhs_inferred_unit == "in"
        and _has_numeric_conversion_factor(node, -1, 12.0)
    ):
        return {
            "rhs_inferred_unit": "ft",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: explicit inch to foot conversion factor /12 is present.",
        }

    if (
        lhs_expected_unit == "in"
        and rhs_inferred_unit == "ft"
        and _has_numeric_conversion_factor(node, 1, 12.0)
    ):
        return {
            "rhs_inferred_unit": "in",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: explicit foot to inch conversion factor *12 is present.",
        }

    if (
        _is_gpm_unit(lhs_expected_unit)
        and _is_cubic_inch_per_minute_unit(rhs_inferred_unit)
        and _has_numeric_conversion_factor(node, -1, 231.0)
    ):
        return {
            "rhs_inferred_unit": "gpm",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: explicit hydraulic conversion factor /231 converts in^3/min to gpm.",
        }

    if (
        _is_cubic_inch_per_minute_unit(lhs_expected_unit)
        and _is_gpm_unit(rhs_inferred_unit)
        and _has_numeric_conversion_factor(node, 1, 231.0)
    ):
        return {
            "rhs_inferred_unit": "in^3/min",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: explicit hydraulic conversion factor *231 converts gpm to in^3/min.",
        }

    if (
        _is_cfs_unit(lhs_expected_unit)
        and _is_gpm_unit(rhs_inferred_unit)
        and _has_numeric_conversion_factor(node, -1, 448.831)
    ):
        return {
            "rhs_inferred_unit": "ft^3/s",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: explicit hydraulic conversion factor /448.831 converts gpm to ft^3/s.",
        }

    if (
        _is_gpm_unit(lhs_expected_unit)
        and _is_cfs_unit(rhs_inferred_unit)
        and _has_numeric_conversion_factor(node, 1, 448.831)
    ):
        return {
            "rhs_inferred_unit": "gpm",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: explicit hydraulic conversion factor *448.831 converts ft^3/s to gpm.",
        }

    if (
        _is_btu_per_hr_unit(lhs_expected_unit)
        and normalize_unit(rhs_inferred_unit) == "W"
        and _has_numeric_conversion_factor(node, 1, 3.412)
    ):
        return {
            "rhs_inferred_unit": "BTU/hr",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: explicit W to BTU/hr conversion factor *3.412 is present.",
        }

    if (
        normalize_unit(lhs_expected_unit) == "W"
        and _is_btu_per_hr_unit(rhs_inferred_unit)
        and _has_numeric_conversion_factor(node, -1, 3.412)
    ):
        return {
            "rhs_inferred_unit": "W",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: explicit BTU/hr to W conversion factor /3.412 is present.",
        }

    if (
        _is_cfm_unit(lhs_expected_unit)
        and _is_btu_per_hr_per_f_unit(rhs_inferred_unit)
        and _is_hvac_sensible_required_airflow_expression(node, variable_units)
    ):
        return {
            "rhs_inferred_unit": "cfm",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: HVAC sensible heat rule BTU/hr / (1.08 * delta_F) produces cfm.",
        }

    if (
        _is_temperature_interval_unit(lhs_expected_unit)
        and _is_hvac_sensible_temperature_rise_expression(node, variable_units)
    ):
        return {
            "rhs_inferred_unit": normalize_unit(lhs_expected_unit),
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: HVAC sensible heat rule BTU/hr / (1.08 * cfm) produces a temperature rise.",
        }

    if (
        _is_temperature_interval_unit(lhs_expected_unit)
        and rhs_inferred_unit in {"C", "F"}
        and _is_heat_rate_temperature_response_expression(node, variable_units)
    ):
        return {
            "rhs_inferred_unit": normalize_unit(lhs_expected_unit),
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: heat-rate divided by a heat-transfer-per-temperature factor produces a temperature interval.",
        }

    return None


def _has_wh_per_w_runtime_division(node, variable_units):
    for child in ast.walk(node):
        if not isinstance(child, ast.BinOp) or not isinstance(child.op, ast.Div):
            continue
        try:
            left = _infer_unit_node(child.left, variable_units)
            right = _infer_unit_node(child.right, variable_units)
        except KeyError:
            continue
        if normalize_unit(left.get("unit")) == "Wh" and normalize_unit(right.get("unit")) == "W":
            return True
    return False


def _pump_brake_horsepower_unit_validation(rhs, variable_units, names, lhs_expected_unit):
    if normalize_unit(lhs_expected_unit) != "hp":
        return None

    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return None

    return _pump_horsepower_formula_unit_result(tree.body, variable_units, names)


def _pump_horsepower_formula_unit_result(node, variable_units, names):
    factors = _multiplicative_factors(node)
    numerator = [factor for factor, sign in factors if sign > 0]
    denominator = [factor for factor, sign in factors if sign < 0]
    if not numerator or not denominator:
        return None

    numerator_units = [_factor_unit(node, variable_units) for node in numerator]
    denominator_units = [_factor_unit(node, variable_units) for node in denominator]

    if not any(_is_gpm_unit(unit) for unit in numerator_units):
        return None
    if not any(_is_hydraulic_head_family_unit(unit) for unit in numerator_units):
        return None
    if not all(_is_gpm_unit(unit) or _is_hydraulic_head_family_unit(unit) or _is_dimensionless_unit(unit) for unit in numerator_units):
        return None
    has_hp_conversion = False
    for denominator_node, unit in zip(denominator, denominator_units, strict=False):
        if _is_3960_like_factor(denominator_node, names):
            has_hp_conversion = True
            continue
        if not _is_dimensionless_unit(unit):
            return None
    if not has_hp_conversion:
        return None

    return {
        "rhs_inferred_unit": "hp",
        "unit": "hp",
        "status": "valid",
        "severity": "info",
        "message": "Unit validation passed: standard pump brake-horsepower expression with gpm, ft head, specific gravity, 3960 conversion factor, and efficiency produces hp.",
    }


def _multiplicative_factors(node, sign=1):
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        return _multiplicative_factors(node.left, sign) + _multiplicative_factors(node.right, sign)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _multiplicative_factors(node.left, sign) + _multiplicative_factors(node.right, -sign)
    return [(node, sign)]


def _has_numeric_conversion_factor(node, sign, target):
    product = 1.0
    found_numeric = False
    for factor, factor_sign in _multiplicative_factors(node):
        if factor_sign != sign:
            continue
        value = _constant_numeric_value(factor)
        if value is None:
            continue
        if math.isclose(float(value), float(target), rel_tol=1e-12, abs_tol=1e-12):
            return True
        product *= float(value)
        found_numeric = True
    return found_numeric and math.isclose(product, float(target), rel_tol=1e-12, abs_tol=1e-12)


def _factor_unit(node, variable_units):
    if _is_numeric_constant(node):
        return "dimensionless"
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)) and _is_numeric_constant(node.operand):
        return "dimensionless"
    if isinstance(node, ast.Name):
        if node.id in variable_units:
            return normalize_unit(variable_units.get(node.id))
        return _unit_from_name_suffix(node.id)
    inferred = _infer_unit_node(node, variable_units)
    if inferred.get("status") == "valid":
        return inferred.get("unit")
    return None


def _is_gpm_unit(unit):
    return normalize_unit(unit) == "gpm"


def _is_cfs_unit(unit):
    return normalize_unit(unit) == "ft^3/s"


def _is_cubic_inch_per_minute_unit(unit):
    return normalize_unit(unit) == "in^3/min"


def _is_cfm_unit(unit):
    return normalize_unit(unit) == "cfm"


def _is_btu_per_hr_unit(unit):
    return normalize_unit(unit) == "BTU/hr"


def _is_btu_per_hr_per_f_unit(unit):
    return normalize_unit(unit) in {"BTU/hr/F", "BTU/h/F"}


def _is_hvac_sensible_required_airflow_expression(node, variable_units):
    if not _has_numeric_conversion_factor(node, -1, 1.08):
        return False
    numerator_units, denominator_units = _factor_units_by_sign(node, variable_units)
    return (
        any(_is_btu_per_hr_unit(unit) for unit in numerator_units)
        and any(_is_temperature_interval_unit(unit) for unit in denominator_units)
        and all(
            _is_btu_per_hr_unit(unit) or _is_dimensionless_unit(unit)
            for unit in numerator_units
            if unit is not None
        )
    )


def _is_hvac_sensible_temperature_rise_expression(node, variable_units):
    if not _has_numeric_conversion_factor(node, -1, 1.08):
        return False
    numerator_units, denominator_units = _factor_units_by_sign(node, variable_units)
    return (
        any(_is_btu_per_hr_unit(unit) for unit in numerator_units)
        and any(_is_cfm_unit(unit) for unit in denominator_units)
        and all(
            _is_btu_per_hr_unit(unit) or _is_dimensionless_unit(unit)
            for unit in numerator_units
            if unit is not None
        )
    )


def _is_heat_rate_temperature_response_expression(node, variable_units):
    numerator_units, denominator_units = _factor_units_by_sign(node, variable_units)
    return (
        any(_is_btu_per_hr_unit(unit) or normalize_unit(unit) == "W" for unit in numerator_units)
        and any(_is_heat_transfer_per_temperature_factor_unit(unit) for unit in denominator_units)
        and all(
            _is_btu_per_hr_unit(unit) or normalize_unit(unit) == "W" or _is_dimensionless_unit(unit)
            for unit in numerator_units
            if unit is not None
        )
    )


def _is_heat_transfer_per_temperature_factor_unit(unit):
    normalized = normalize_unit(unit)
    if normalized in {"BTU/hr/F", "BTU/h/F", "BTU/hr/gpm/F", "BTU/hr/cfm/F", "W/C", "W/K"}:
        return True
    return bool(
        isinstance(normalized, str)
        and (
            normalized.endswith("/F")
            or normalized.endswith("/C")
            or normalized.endswith("/K")
        )
        and ("BTU/hr" in normalized or normalized.startswith("W/"))
    )


def _factor_units_by_sign(node, variable_units):
    numerator_units = []
    denominator_units = []
    for factor, sign in _multiplicative_factors(node):
        unit = _factor_unit(factor, variable_units)
        if sign > 0:
            numerator_units.append(unit)
        else:
            denominator_units.append(unit)
    return numerator_units, denominator_units


def _is_fpm_unit(unit):
    return normalize_unit(unit) == "fpm"


def _is_cycle_rate_unit(unit):
    return normalize_unit(unit) == "cycle/min"


def _is_scf_per_cycle_unit(unit):
    return normalize_unit(unit) == "scf/cycle"


def _is_square_foot_unit(unit):
    return normalize_unit(unit) == "ft^2"


def _is_square_inch_unit(unit):
    return normalize_unit(unit) == "in^2"


def _is_inches_per_foot_unit(unit):
    return normalize_unit(unit) == "in/ft"


def _is_dimensionless_unit(unit):
    return normalize_unit(unit) in {"dimensionless", "percent"}


def _is_3960_like_factor(node, names):
    value = _constant_numeric_value(node)
    if value is None and isinstance(node, ast.Name) and isinstance(names, dict):
        value = names.get(node.id)
    if _is_number(value) and math.isclose(float(value), 3960.0, rel_tol=0.02, abs_tol=1.0):
        return True
    if isinstance(node, ast.Name):
        lowered = node.id.lower()
        compact = re.sub(r"[^a-z0-9]+", "", lowered)
        tokens = {token for token in re.split(r"[^a-z0-9]+", lowered) if token}
        if "3960" in compact and any(marker in compact for marker in ("hp", "bhp", "horsepower", "conversion", "constant", "factor")):
            return True
        if any(
            marker in compact
            for marker in (
                "bhpconversionfactor",
                "hpconversionfactor",
                "horsepowerconversionfactor",
                "hydraulichpconstant",
                "hydraulichorsepowerconstant",
                "hydraulichpconversion",
                "hydraulichorsepowerconversion",
                "pumphorsepowerconstant",
                "pumpbhpconstant",
                "gpmftperhp",
                "gpmheadperhp",
            )
        ):
            return True
        if (
            "conversion" in tokens
            and "factor" in tokens
            and bool(tokens.intersection({"hp", "bhp", "horsepower"}))
        ):
            return True
    return False


_NO_SELECTED_BRANCH = object()


def _selected_branch_unit_validation(lhs, rhs, variable_units, names, lhs_expected_unit):
    if not isinstance(names, dict):
        return None
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return None

    node = tree.body
    selected_node = _selected_conditional_value_node(node, names)
    if selected_node is _NO_SELECTED_BRANCH:
        return None

    selected_unit = _infer_selected_branch_unit(selected_node, variable_units, lhs_expected_unit, names=names)
    if _is_null_node(selected_node):
        expression_unit = _infer_unit_node(node, variable_units, names=names)
        if expression_unit.get("status") == "valid" and normalize_unit(expression_unit.get("unit")) != "dimensionless":
            selected_unit = expression_unit
    if selected_unit.get("status") == "invalid":
        return selected_unit
    if selected_unit.get("status") == "unknown":
        return None

    inferred_unit = selected_unit.get("unit")
    if lhs_expected_unit and inferred_unit and not _units_validation_compatible(lhs_expected_unit, inferred_unit):
        return {
            "rhs_inferred_unit": inferred_unit,
            "status": "invalid",
            "severity": "warning",
            "message": f"Selected branch unit {inferred_unit} is incompatible with LHS unit {lhs_expected_unit}.",
        }

    return {
        "rhs_inferred_unit": inferred_unit,
        "status": "valid",
        "severity": "info",
        "message": f"Unit validation passed: selected conditional branch is compatible with {lhs}.",
    }


def _selected_conditional_value_node(node, names):
    if _is_if_call(node):
        try:
            condition = _eval_node(node.args[0], names)
        except Exception:
            return _NO_SELECTED_BRANCH
        return node.args[1] if bool(condition) else node.args[2]

    if _is_piecewise_call(node):
        args = node.args
        has_default = len(args) % 2 == 1
        pair_count = (len(args) - 1) // 2 if has_default else len(args) // 2
        for index in range(pair_count):
            try:
                condition = _eval_node(args[index * 2], names)
            except Exception:
                return _NO_SELECTED_BRANCH
            if bool(condition):
                return args[index * 2 + 1]
        if has_default:
            return args[-1]
        return ast.Constant(value=None)

    return _NO_SELECTED_BRANCH


def _infer_selected_branch_unit(node, variable_units, lhs_expected_unit, names=None):
    lhs_expected_unit = normalize_unit(lhs_expected_unit) if lhs_expected_unit else None
    if _is_null_node(node):
        return _unit_result(
            lhs_expected_unit or "dimensionless",
            "valid",
            "info",
            "Null fallback is compatible with the selected branch/LHS for validation.",
        )
    if _is_numeric_constant(node) and lhs_expected_unit:
        return _unit_result(
            lhs_expected_unit,
            "valid",
            "info",
            f"Numeric conditional fallback inherits LHS unit {lhs_expected_unit} for validation.",
        )
    if _is_string_node(node):
        unit = "status_string" if _is_status_text_unit(lhs_expected_unit) else _string_literal_unit(node.value)
        return _unit_result(unit, "valid", "info", f"String branch is {unit}.")
    return _infer_unit_node(node, variable_units, names=names)


def _temperature_interval_unit_result(lhs, rhs, variable_units, lhs_expected_unit):
    if not _is_temperature_interval_lhs(lhs, lhs_expected_unit):
        return None
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return None
    node = tree.body
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Sub):
        return None
    if not isinstance(node.left, ast.Name) or not isinstance(node.right, ast.Name):
        return None
    left_unit = normalize_unit(variable_units.get(node.left.id))
    right_unit = normalize_unit(variable_units.get(node.right.id))
    if left_unit == right_unit and left_unit == "C":
        return {
            "rhs_inferred_unit": "delta_C",
            "status": "valid",
            "severity": "info",
            "message": "Unit validation passed: subtracting two absolute C temperatures produces a temperature interval.",
        }
    return None


def _rhs_is_numeric_literal(rhs):
    try:
        tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
    except SyntaxError:
        return False
    node = tree.body
    if _is_numeric_constant(node):
        return True
    return (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, (ast.UAdd, ast.USub))
        and _is_numeric_constant(node.operand)
    )


def _is_temperature_interval_lhs(lhs, lhs_expected_unit):
    lowered = str(lhs or "").lower()
    interval_markers = [
        "delta_t",
        "deltat",
        "deltat_",
        "delta_",
        "allowable_delta",
        "allowed_delta",
        "temperature_difference",
        "temperature_rise",
        "temp_rise",
        "delta_temperature",
        "temperature_delta",
        "temperature_margin",
        "temp_margin",
        "thermal_margin",
        "temp_diff",
        "deadband",
        "control_deadband",
        "differential",
        "difference",
    ]
    return _is_temperature_interval_unit(lhs_expected_unit) or any(marker in lowered for marker in interval_markers)


def _infer_unit_node(node, variable_units, names=None):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return _unit_result("boolean", "valid", "info", "Boolean literal is boolean.")
        if isinstance(node.value, (int, float, bool)):
            return _unit_result("dimensionless", "valid", "info", "Numeric literal is dimensionless.")
        if isinstance(node.value, str):
            unit = _string_literal_unit(node.value)
            return _unit_result(unit, "valid", "info", f"String literal is {unit}.")
        if node.value is None:
            return _unit_result("dimensionless", "valid", "info", "Null literal is dimensionless.")
        return _unit_result(None, "unknown", "info", "Non-numeric literal unit is unknown.")

    if isinstance(node, ast.Name):
        if node.id not in variable_units:
            suffix_unit = _unit_from_name_suffix(node.id)
            if suffix_unit:
                return _unit_result(suffix_unit, "valid", "info", f"Variable {node.id} unit inferred from name suffix as {suffix_unit}.")
            raise KeyError(node.id)
        unit = normalize_unit(variable_units.get(node.id))
        return _unit_result(unit, "valid", "info", f"Variable {node.id} has unit {unit}.")

    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return _unit_result("boolean", "valid", "info", "Boolean NOT expression produces boolean.")
        return _infer_unit_node(node.operand, variable_units, names=names)

    if isinstance(node, ast.BinOp):
        left = _infer_unit_node(node.left, variable_units, names=names)
        right = _infer_unit_node(node.right, variable_units, names=names)
        if isinstance(node.op, (ast.Add, ast.Sub)):
            numeric_literal_result = _numeric_literal_add_sub_unit(left, node.left, right, node.right)
            if numeric_literal_result:
                return numeric_literal_result
            return _combine_add_sub_units(left, right, node.left, node.right, node.op)
        if isinstance(node.op, ast.Mult):
            return _combine_multiply_units(left, right, node.left, node.right, names, variable_units)
        if isinstance(node.op, ast.Div):
            return _combine_divide_units(left, right, node.left, node.right, names, variable_units)
        if isinstance(node.op, ast.Pow):
            return _combine_power_units(left, right, node.right)
        return _unit_result(None, "unknown", "info", "Unit algebra for this arithmetic operator is not supported.")

    if isinstance(node, ast.Compare):
        return _infer_compare_units(node, variable_units, names=names)

    if isinstance(node, ast.BoolOp):
        if not isinstance(node.op, (ast.And, ast.Or)):
            return _unit_result(None, "unknown", "info", "Only boolean AND/OR unit inference is supported.")
        for value in node.values:
            inferred = _infer_unit_node(value, variable_units, names=names)
            invalid = _first_invalid_unit(inferred)
            if invalid:
                return invalid
            if inferred["status"] == "unknown":
                return _unit_result(None, "unknown", "info", "Boolean expression unit compatibility is unknown.")
            if not _is_boolean_compatible_unit(inferred["unit"]):
                return _unit_result(None, "invalid", "warning", f"Boolean AND requires boolean operands, found {inferred['unit']}.")
        return _unit_result("boolean", "valid", "info", "Boolean expression produces boolean.")

    if isinstance(node, ast.Call):
        if _is_piecewise_call(node):
            return _infer_piecewise_unit(node, variable_units, names=names)
        if _is_if_call(node):
            return _infer_if_unit(node, variable_units, names=names)
        if _is_any_null_call(node):
            return _unit_result("boolean", "valid", "info", "any_null returns boolean.")
        if _is_is_null_call(node):
            return _unit_result("boolean", "valid", "info", "is_null returns boolean.")
        if _is_boolean_count_call(node):
            return _infer_boolean_count_unit(node, variable_units, names=names)
        if _is_safe_int_call(node):
            return _infer_safe_int_unit(node, variable_units, names=names)
        if _is_minmax_call(node):
            return _infer_minmax_unit(node, variable_units, names=names)
        if _is_min_ignore_null_call(node):
            return _infer_min_ignore_null_unit(node, variable_units, names=names)
        if _is_max_ignore_null_call(node):
            return _infer_max_ignore_null_unit(node, variable_units, names=names)
        if _is_argmin_label_ignore_null_call(node):
            return _infer_argmin_label_ignore_null_unit(node, variable_units, names=names)
        if _is_argmax_label_ignore_null_call(node):
            return _infer_argmax_label_ignore_null_unit(node, variable_units, names=names)
        if _is_value_for_label_ignore_null_call(node):
            return _infer_value_for_label_ignore_null_unit(node, variable_units, names=names)
        if _is_sqrt_call(node):
            return _infer_sqrt_unit(
                node.args[0],
                variable_units,
                lambda child, units: _infer_unit_node(child, units, names=names),
            )
        if isinstance(node.func, ast.Name) and node.func.id in ALLOWED_FUNCTIONS:
            if not node.args:
                return _unit_result(None, "unknown", "info", "Function call has no arguments for unit inference.")
            first = _infer_unit_node(node.args[0], variable_units, names=names)
            if node.func.id in {"abs", "round", "floor", "ceil"}:
                return first
        return _unit_result(None, "unknown", "info", "Unit compatibility for this function is not validated.")

    if isinstance(node, (ast.List, ast.Tuple)):
        return _infer_list_unit(node, variable_units, names=names)

    return _unit_result(None, "unknown", "info", f"Unit inference does not support {type(node).__name__}.")


def _infer_list_unit(node, variable_units, names=None):
    inferred_units = []
    for item in node.elts:
        if _is_null_node(item):
            continue
        inferred = _infer_unit_node(item, variable_units, names=names)
        invalid = _first_invalid_unit(inferred)
        if invalid:
            return invalid
        if inferred.get("status") == "unknown":
            return _unit_result("list", "unknown", "info", "List element unit compatibility is unknown.")
        unit = _normalize_inferred_element_unit(inferred.get("unit"))
        if _is_list_unit(unit):
            return _unit_result("list[mixed]", "invalid", "warning", "Nested list values are not supported in MCM list expressions.")
        inferred_units.append(unit)

    if not inferred_units:
        return _unit_result("list", "valid", "info", "List expression contains only null values.")

    textual_unit = _common_textual_unit(inferred_units)
    if textual_unit:
        return _unit_result(
            _make_list_unit(textual_unit),
            "valid",
            "info",
            f"List expression inferred as {_make_list_unit(textual_unit)}.",
        )

    first = inferred_units[0]
    for unit in inferred_units[1:]:
        if not _units_validation_compatible(first, unit):
            return _unit_result(
                "list[mixed]",
                "invalid",
                "warning",
                f"List expression contains incompatible element units {first} and {unit}.",
            )
    return _unit_result(_make_list_unit(first), "valid", "info", f"List expression inferred as {_make_list_unit(first)}.")


def _combine_add_sub_units(left, right, left_node=None, right_node=None, operator=None):
    invalid = _first_invalid_unit(left, right)
    if invalid:
        return invalid
    if left["status"] == "unknown" or right["status"] == "unknown":
        return _unit_result(None, "unknown", "info", "Addition/subtraction unit compatibility is unknown.")
    hydraulic_head_result = _hydraulic_head_add_sub_unit_result(left, right, left_node, right_node)
    if hydraulic_head_result:
        return hydraulic_head_result
    temperature_result = _temperature_add_sub_unit_result(left["unit"], right["unit"], operator)
    if temperature_result:
        return temperature_result
    if left["unit"] == right["unit"]:
        return _unit_result(left["unit"], "valid", "info", f"Compatible units for addition/subtraction: {left['unit']}.")
    if left["unit"] == "C" and _is_celsius_temperature_interval_unit(right["unit"]):
        return _unit_result("C", "valid", "info", f"Absolute C plus/minus temperature interval {right['unit']} produces C.")
    if right["unit"] == "C" and _is_celsius_temperature_interval_unit(left["unit"]):
        return _unit_result("C", "valid", "info", f"Temperature interval {left['unit']} plus absolute C produces C.")
    if _units_validation_compatible(left["unit"], right["unit"]):
        return _unit_result(
            left["unit"],
            "valid",
            "info",
            f"Compatible dimensions for addition/subtraction: {left['unit']} and {right['unit']}.",
        )
    return _unit_result(
        None,
        "invalid",
        "warning",
        f"Cannot add or subtract incompatible units {left['unit']} and {right['unit']}.",
    )


def _temperature_add_sub_unit_result(left_unit, right_unit, operator=None):
    left_unit = normalize_unit(left_unit)
    right_unit = normalize_unit(right_unit)
    if not (_is_temperature_arithmetic_unit(left_unit) and _is_temperature_arithmetic_unit(right_unit)):
        return None

    is_subtract = isinstance(operator, ast.Sub) or operator in {"-", "subtract", "sub"}
    is_add = isinstance(operator, ast.Add) or operator in {"+", "add", None}

    if left_unit == "C" and right_unit == "C":
        if is_subtract:
            return _unit_result("delta_C", "valid", "info", "Absolute C minus absolute C produces a temperature interval.")
        if is_add:
            return _unit_result(None, "invalid", "warning", "Adding two absolute C temperatures is not a supported unit operation.")
    if left_unit == "F" and right_unit == "F":
        if is_subtract:
            return _unit_result("delta_F", "valid", "info", "Absolute F minus absolute F produces a temperature interval.")
        if is_add:
            return _unit_result(None, "invalid", "warning", "Adding two absolute F temperatures is not a supported unit operation.")

    if left_unit == "C" and _is_celsius_temperature_interval_unit(right_unit):
        return _unit_result("C", "valid", "info", f"Absolute C plus/minus temperature interval {right_unit} produces C.")
    if left_unit == "F" and _is_fahrenheit_temperature_interval_unit(right_unit):
        return _unit_result("F", "valid", "info", f"Absolute F plus/minus temperature interval {right_unit} produces F.")
    if _is_celsius_temperature_interval_unit(left_unit) and right_unit == "C":
        if is_add:
            return _unit_result("C", "valid", "info", f"Temperature interval {left_unit} plus absolute C produces C.")
        if is_subtract:
            return _unit_result(None, "invalid", "warning", "Subtracting an absolute C temperature from a temperature interval is not supported.")
    if _is_fahrenheit_temperature_interval_unit(left_unit) and right_unit == "F":
        if is_add:
            return _unit_result("F", "valid", "info", f"Temperature interval {left_unit} plus absolute F produces F.")
        if is_subtract:
            return _unit_result(None, "invalid", "warning", "Subtracting an absolute F temperature from a temperature interval is not supported.")

    if _is_celsius_temperature_interval_unit(left_unit) and _is_celsius_temperature_interval_unit(right_unit):
        return _unit_result("delta_C", "valid", "info", "Temperature intervals are compatible for addition/subtraction.")
    if _is_fahrenheit_temperature_interval_unit(left_unit) and _is_fahrenheit_temperature_interval_unit(right_unit):
        return _unit_result("delta_F", "valid", "info", "Temperature intervals are compatible for addition/subtraction.")
    return None


def _is_temperature_arithmetic_unit(unit):
    unit = normalize_unit(unit)
    return unit in {"C", "F"} or _is_celsius_temperature_interval_unit(unit) or _is_fahrenheit_temperature_interval_unit(unit)


def _is_celsius_temperature_interval_unit(unit):
    return normalize_unit(unit) in {"K", "delta_C", "C_delta", "K_delta"}


def _is_fahrenheit_temperature_interval_unit(unit):
    return normalize_unit(unit) in {"delta_F", "F_delta"}


def _hydraulic_head_add_sub_unit_result(left, right, left_node=None, right_node=None):
    left_unit = normalize_unit(left.get("unit"))
    right_unit = normalize_unit(right.get("unit"))
    if not (_is_hydraulic_head_family_unit(left_unit) and _is_hydraulic_head_family_unit(right_unit)):
        return None
    if not _hydraulic_head_operand_is_safe(left_unit, left_node):
        return None
    if not _hydraulic_head_operand_is_safe(right_unit, right_node):
        return None
    return _unit_result(
        "ft_head",
        "valid",
        "info",
        f"Hydraulic head units are compatible for addition/subtraction: {left_unit} and {right_unit}.",
    )


def _is_hydraulic_head_family_unit(unit):
    return normalize_unit(unit) in {"ft", "ft_head"}


def _hydraulic_head_operand_is_safe(unit, node=None):
    unit = normalize_unit(unit)
    if unit == "ft_head":
        return not _node_has_geometry_only_length_context(node)
    if unit == "ft":
        return _node_has_hydraulic_head_context(node) and not _node_has_geometry_only_length_context(node)
    return False


def _hydraulic_head_preserved_unit(unit, node=None):
    if _hydraulic_head_operand_is_safe(unit, node):
        return "ft_head"
    return None


def _node_has_hydraulic_head_context(node):
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return _name_has_hydraulic_head_context(node.id)
    return any(isinstance(child, ast.Name) and _name_has_hydraulic_head_context(child.id) for child in ast.walk(node))


def _node_has_geometry_only_length_context(node):
    if node is None:
        return False
    for child in ast.walk(node):
        if not isinstance(child, ast.Name):
            continue
        if _name_has_geometry_length_context(child.id) and not _name_has_hydraulic_head_context(child.id):
            return True
    return False


def _numeric_literal_add_sub_unit(left, left_node, right, right_node):
    invalid = _first_invalid_unit(left, right)
    if invalid:
        return invalid
    if left.get("status") == "unknown" or right.get("status") == "unknown":
        return None
    left_unit = normalize_unit(left.get("unit"))
    right_unit = normalize_unit(right.get("unit"))
    if _is_numeric_constant(right_node) and right_unit == "dimensionless" and left_unit not in {None, "dimensionless", "boolean"} and not _is_textual_unit(left_unit):
        return _unit_result(left_unit, "valid", "info", f"Numeric literal inherits {left_unit} for addition/subtraction.")
    if _is_numeric_constant(left_node) and left_unit == "dimensionless" and right_unit not in {None, "dimensionless", "boolean"} and not _is_textual_unit(right_unit):
        return _unit_result(right_unit, "valid", "info", f"Numeric literal inherits {right_unit} for addition/subtraction.")
    return None


def _named_conversion_factor_unit_result(source_unit, factor_unit, factor_node, names, operator):
    if normalize_unit(factor_unit) not in {"dimensionless", "percent"}:
        return None
    if not isinstance(factor_node, ast.Name):
        return None

    hydraulic_result = _hydraulic_gpm_cfs_named_conversion_unit_result(
        source_unit,
        factor_node,
        names,
        operator,
    )
    if hydraulic_result:
        return hydraulic_result

    profile = _conversion_factor_profile_from_name(factor_node.id)
    if not profile:
        return None

    source_unit = normalize_unit(source_unit)
    from_unit = profile["from_unit"]
    to_unit = profile["to_unit"]
    if source_unit != from_unit:
        return None

    actual_value = _conversion_factor_value(factor_node.id, names)
    expected_value = _expected_conversion_factor_value(from_unit, to_unit, operator)
    if actual_value is None or expected_value is None:
        return None
    if not _conversion_factor_value_matches(actual_value, expected_value):
        return None

    operator_text = "*" if operator == "multiply" else "/"
    return _unit_result(
        to_unit,
        "valid",
        "info",
        f"Named conversion factor {factor_node.id} applied as {from_unit} {operator_text} factor -> {to_unit}.",
    )


def _hydraulic_gpm_cfs_named_conversion_unit_result(source_unit, factor_node, names, operator):
    if not _looks_like_gpm_cfs_conversion_factor_name(factor_node.id):
        return None
    actual_value = _conversion_factor_value(factor_node.id, names)
    if not _is_448_831_like_value(actual_value):
        return None

    source_unit = normalize_unit(source_unit)
    if operator == "divide" and _is_gpm_unit(source_unit):
        return _unit_result(
            "ft^3/s",
            "valid",
            "info",
            f"Named hydraulic conversion factor {factor_node.id} applied as gpm / 448.831 -> ft^3/s.",
        )
    if operator == "multiply" and _is_cfs_unit(source_unit):
        return _unit_result(
            "gpm",
            "valid",
            "info",
            f"Named hydraulic conversion factor {factor_node.id} applied as ft^3/s * 448.831 -> gpm.",
        )
    return None


def _numeric_inch_length_division_unit_result(left_unit, right_unit, left_node, right_node):
    left_unit = normalize_unit(left_unit)
    right_unit = normalize_unit(right_unit)
    if left_unit != "in" or right_unit not in {"dimensionless", "percent"}:
        return None

    divisor = _constant_numeric_expression_value(right_node)
    if divisor is None or divisor <= 0:
        return None

    if math.isclose(divisor, 12.0, rel_tol=0.0, abs_tol=1e-12):
        return _unit_result("ft", "valid", "info", "Known conversion rule: in / 12 -> ft.")

    if (
        math.isclose(divisor, 24.0, rel_tol=0.0, abs_tol=1e-12)
        and _node_is_diameter_length_reference(left_node)
    ):
        return _unit_result(
            "ft",
            "valid",
            "info",
            "Known geometry conversion rule: diameter in / 24 -> radius ft.",
        )

    return None


def _constant_numeric_expression_value(node):
    value = _constant_numeric_value(node)
    if value is not None:
        return value

    if isinstance(node, ast.BinOp):
        left = _constant_numeric_expression_value(node.left)
        right = _constant_numeric_expression_value(node.right)
        if left is None or right is None:
            return None
        try:
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if math.isclose(right, 0.0, abs_tol=1e-12):
                    return None
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
        except (OverflowError, ValueError, ZeroDivisionError):
            return None

    return None


def _node_is_diameter_length_reference(node):
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _node_is_diameter_length_reference(node.operand)
    if not isinstance(node, ast.Name):
        return False
    tokens = {token for token in re.split(r"[^a-z0-9]+", node.id.lower()) if token}
    return bool(tokens.intersection({"diameter", "diam"}))


def _conversion_factor_profile_from_name(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return None

    tokens = [token for token in re.split(r"[_\W]+", lowered) if token]
    if "to" not in tokens or "conversion" not in tokens or "factor" not in tokens:
        return None

    for to_index, token in enumerate(tokens):
        if token != "to":
            continue
        from_unit = _conversion_unit_from_tokens(tokens[:to_index])
        target_tokens = []
        for target_token in tokens[to_index + 1:]:
            if target_token in {"conversion", "factor"}:
                break
            target_tokens.append(target_token)
        to_unit = _conversion_unit_from_tokens(target_tokens)
        if from_unit and to_unit and from_unit != to_unit:
            return {"from_unit": from_unit, "to_unit": to_unit}
    return None


def _conversion_unit_from_tokens(tokens):
    if not tokens:
        return None
    candidates = [
        "_".join(tokens),
        " ".join(tokens),
        "".join(tokens),
    ]
    for candidate in candidates:
        unit = normalize_unit(candidate)
        if _conversion_unit_scale(unit):
            return unit
    return None


def _conversion_factor_value(name, names):
    if not isinstance(names, dict) or name not in names:
        return None
    value = names.get(name)
    if not _is_number(value):
        return None
    value = float(value)
    if value <= 0:
        return None
    return value


def _expected_conversion_factor_value(from_unit, to_unit, operator):
    from_scale = _conversion_unit_scale(from_unit)
    to_scale = _conversion_unit_scale(to_unit)
    if not from_scale or not to_scale:
        return None
    from_dimension, from_value = from_scale
    to_dimension, to_value = to_scale
    if from_dimension != to_dimension or from_value <= 0 or to_value <= 0:
        return None
    if operator == "multiply":
        return from_value / to_value
    if operator == "divide":
        return to_value / from_value
    return None


def _conversion_unit_scale(unit):
    unit = normalize_unit(unit)
    scales = {
        "in": ("length", 0.0254),
        "ft": ("length", 0.3048),
        "m": ("length", 1.0),
        "s": ("time", 1.0),
        "min": ("time", 60.0),
        "h": ("time", 3600.0),
    }
    return scales.get(unit)


def _conversion_factor_value_matches(actual_value, expected_value):
    return math.isclose(
        float(actual_value),
        float(expected_value),
        rel_tol=1e-6,
        abs_tol=1e-12,
    )


def _combine_multiply_units(left, right, left_node=None, right_node=None, names=None, variable_units=None):
    invalid = _first_invalid_unit(left, right)
    if invalid:
        return invalid
    if left["status"] == "unknown" or right["status"] == "unknown":
        return _unit_result(None, "unknown", "info", "Multiplication unit compatibility is unknown.")

    left_unit = left["unit"]
    right_unit = right["unit"]

    thousand_foot_result = _ohm_per_1000ft_multiply_result(
        left_node,
        right_node,
        variable_units or {},
        names,
    )
    if thousand_foot_result:
        return thousand_foot_result

    conversion = _named_conversion_factor_unit_result(left_unit, right_unit, right_node, names, "multiply")
    if conversion:
        return conversion
    conversion = _named_conversion_factor_unit_result(right_unit, left_unit, left_node, names, "multiply")
    if conversion:
        return conversion

    if left_unit == "dimensionless":
        preserved = _hydraulic_head_preserved_unit(right_unit, right_node) or right_unit
        return _unit_result(preserved, "valid", "info", f"Dimensionless multiplier preserves {preserved}.")
    if right_unit == "dimensionless":
        preserved = _hydraulic_head_preserved_unit(left_unit, left_node) or left_unit
        return _unit_result(preserved, "valid", "info", f"Dimensionless multiplier preserves {preserved}.")
    if left_unit == "percent" and right_unit == "percent":
        return _unit_result("dimensionless", "valid", "info", "Percent multiplied by percent is dimensionless for unit validation.")
    if left_unit == "percent":
        preserved = _hydraulic_head_preserved_unit(right_unit, right_node) or right_unit
        return _unit_result(preserved, "valid", "info", f"Percent multiplier preserves {preserved}.")
    if right_unit == "percent":
        preserved = _hydraulic_head_preserved_unit(left_unit, left_node) or left_unit
        return _unit_result(preserved, "valid", "info", f"Percent multiplier preserves {preserved}.")
    if (
        (_is_cycle_rate_unit(left_unit) and _is_scf_per_cycle_unit(right_unit))
        or (_is_scf_per_cycle_unit(left_unit) and _is_cycle_rate_unit(right_unit))
    ):
        return _unit_result("scfm", "valid", "info", "Known pneumatic flow unit rule: cycle/min * scf/cycle -> scfm.")
    thermal_interval = _thermal_resistance_product_unit(left_unit, right_unit)
    if thermal_interval:
        return _unit_result(
            thermal_interval,
            "valid",
            "info",
            f"Thermal resistance product {left_unit} * {right_unit} produces a temperature interval.",
        )
    conversion = _conversion_ratio_multiply_result_unit(left_unit, right_unit)
    if conversion:
        return _unit_result(
            conversion,
            "valid",
            "info",
            f"Conversion-ratio multiplication reduced {left_unit} * {right_unit} -> {conversion}.",
        )
    conversion = _conversion_ratio_multiply_result_unit(right_unit, left_unit)
    if conversion:
        return _unit_result(
            conversion,
            "valid",
            "info",
            f"Conversion-ratio multiplication reduced {left_unit} * {right_unit} -> {conversion}.",
        )

    known = {
        ("kg", "kJ/kg/C"): "kJ/C",
        ("kJ/kg/C", "kg"): "kJ/C",
        ("kJ/C", "C"): "kJ",
        ("C", "kJ/C"): "kJ",
        ("V", "A"): "W",
        ("A", "V"): "W",
        ("V", "Ah"): "Wh",
        ("Ah", "V"): "Wh",
        ("A", "ohm"): "V",
        ("ohm", "A"): "V",
        ("A", "h"): "Ah",
        ("h", "A"): "Ah",
        ("W", "C/W"): "delta_C",
        ("C/W", "W"): "delta_C",
        ("W", "K/W"): "delta_C",
        ("K/W", "W"): "delta_C",
        ("ft", "ft"): "ft^2",
        ("ft^2", "ft"): "ft^3",
        ("ft", "ft^2"): "ft^3",
        ("ft", "rpm"): "fpm",
        ("rpm", "ft"): "fpm",
        ("fpm", "ft^2"): "cfm",
        ("ft^2", "fpm"): "cfm",
    }
    if (left_unit, right_unit) in known:
        unit = known[(left_unit, right_unit)]
        return _unit_result(unit, "valid", "info", f"Known multiplication unit rule produced {unit}.")

    reduced = _compose_units_by_dimensions(left_unit, right_unit, "*")
    if reduced:
        return _unit_result(
            reduced,
            "valid",
            "info",
            f"Compound-unit multiplication reduced {left_unit} * {right_unit} -> {reduced}.",
        )

    return _unit_result(None, "unknown", "info", f"Multiplication unit rule is not known for {left_unit} * {right_unit}.")


def _ohm_per_1000ft_multiply_result(left_node, right_node, variable_units, names):
    if _is_resistance_per_1000ft_expression(left_node, variable_units) and _is_thousand_foot_length_count_expression(
        right_node,
        variable_units,
        names,
    ):
        return _unit_result(
            "ohm",
            "valid",
            "info",
            "Unit validation passed: ohm/1000ft resistance multiplied by an explicit thousand-foot length count produces ohm.",
        )
    if _is_resistance_per_1000ft_expression(right_node, variable_units) and _is_thousand_foot_length_count_expression(
        left_node,
        variable_units,
        names,
    ):
        return _unit_result(
            "ohm",
            "valid",
            "info",
            "Unit validation passed: explicit thousand-foot length count multiplied by ohm/1000ft resistance produces ohm.",
        )
    return None


def _is_resistance_per_1000ft_expression(node, variable_units):
    if not isinstance(node, ast.Name):
        return False
    unit = variable_units.get(node.id) if isinstance(variable_units, dict) else None
    return _is_resistance_per_1000ft_name_or_unit(node.id, unit)


def _is_resistance_per_1000ft_name_or_unit(name, unit):
    if _unit_text_is_resistance_per_1000ft(unit):
        return True

    lowered = str(name or "").strip().lower()
    if not lowered:
        return False
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    tokens = {token for token in re.split(r"[^a-z0-9]+", lowered) if token}
    has_thousand_foot = any(marker in compact for marker in ("1000ft", "1000feet"))
    has_resistance_marker = "ohm" in compact or "ohms" in compact or "resistance" in tokens
    has_rate_marker = "per" in tokens or "per1000" in compact or "ohmper" in compact or "ohmsper" in compact
    return bool(has_thousand_foot and has_resistance_marker and has_rate_marker)


def _unit_text_is_resistance_per_1000ft(unit):
    raw = str(unit or "").strip().lower()
    if not raw:
        return False
    normalized = normalize_unit(raw)
    if normalized == "ohm/1000ft":
        return True
    compact = re.sub(r"[^a-z0-9]+", "", raw)
    return bool(
        any(marker in compact for marker in ("ohmper1000ft", "ohmsper1000ft", "ohm1000ft", "ohms1000ft"))
        or re.search(r"ohms?\s*/\s*1000\s*(?:ft|feet)\b", raw)
    )


def _is_thousand_foot_length_count_expression(node, variable_units, names):
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _is_foot_length_expression(node.left, variable_units) and _is_1000ft_denominator_factor(
            node.right,
            names,
        )

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        return (
            _is_foot_length_expression(node.left, variable_units)
            and _is_ft_to_1000ft_multiplier_factor(node.right, variable_units, names)
        ) or (
            _is_foot_length_expression(node.right, variable_units)
            and _is_ft_to_1000ft_multiplier_factor(node.left, variable_units, names)
        )

    return False


def _is_foot_length_expression(node, variable_units):
    if not isinstance(node, ast.Name):
        return False
    unit = variable_units.get(node.id) if isinstance(variable_units, dict) else None
    if normalize_unit(unit) == "ft":
        return True
    return _unit_from_name_suffix(node.id) == "ft"


def _is_1000ft_denominator_factor(node, names):
    value = _numeric_node_or_named_value(node, names)
    if value is not None:
        return _is_1000ft_denominator_value(value)
    if isinstance(node, ast.Name):
        return _is_1000ft_denominator_factor_name(node.id)
    return False


def _is_1000ft_denominator_value(value):
    return _is_number(value) and math.isclose(float(value), 1000.0, rel_tol=1e-9, abs_tol=1e-9)


def _is_1000ft_denominator_factor_name(name):
    lowered = str(name or "").strip().lower()
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    return bool("factor" in compact and "per1000ft" in compact and "to1000ft" not in compact)


def _is_ft_to_1000ft_multiplier_factor(node, variable_units, names):
    if not isinstance(node, ast.Name):
        return False
    role = _ft_to_1000ft_factor_role(node.id)
    if role != "multiplier":
        return False

    value = _numeric_node_or_named_value(node, names)
    if value is not None and not _is_0_001_multiplier_value(value):
        return False

    unit = normalize_unit(variable_units.get(node.id)) if isinstance(variable_units, dict) else None
    return unit in {"dimensionless", "percent", None} or _units_validation_compatible(unit, "1/ft")


def _ft_to_1000ft_factor_role(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return None
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    if "factor" not in compact and "conversion" not in compact:
        return None
    if "ftto1000ft" in compact:
        return "multiplier"
    if "per1000ft" in compact:
        return "denominator"
    return None


def _is_0_001_multiplier_value(value):
    return _is_number(value) and math.isclose(float(value), 0.001, rel_tol=1e-6, abs_tol=1e-12)


def _numeric_node_or_named_value(node, names):
    value = _constant_numeric_value(node)
    if value is not None:
        return value
    if isinstance(node, ast.Name) and isinstance(names, dict):
        value = names.get(node.id)
        if _is_number(value):
            return float(value)
    return None


def _combine_power_units(left, right, exponent_node):
    invalid = _first_invalid_unit(left, right)
    if invalid:
        return invalid
    if left["status"] == "unknown" or right["status"] == "unknown":
        return _unit_result(None, "unknown", "info", "Power unit compatibility is unknown.")
    if normalize_unit(right.get("unit")) not in {"dimensionless", "percent"}:
        return _unit_result(None, "invalid", "warning", f"Exponent must be dimensionless, found {right.get('unit')}.")

    exponent = _constant_numeric_value(exponent_node)
    if exponent is None:
        return _unit_result(None, "unknown", "info", "Power unit inference requires a numeric exponent.")

    unit = _compose_power_unit(left.get("unit"), exponent)
    return _unit_result(unit, "valid", "info", f"Power unit rule produced {unit}.")


def _is_temperature_interval_unit(unit):
    unit = normalize_unit(unit)
    return _is_temperature_delta_unit(unit)


def _is_absolute_temperature_unit(unit):
    return normalize_unit(unit) in {"C", "F", "K_abs"}


def _is_temperature_delta_unit(unit):
    return normalize_unit(unit) in {"K", "delta_C", "C_delta", "K_delta", "delta_F", "F_delta"}


def _is_temperature_unit_family(unit):
    return _is_absolute_temperature_unit(unit) or _is_temperature_delta_unit(unit)


def _temperature_family(unit):
    unit = normalize_unit(unit)
    if unit in {"C", "K", "delta_C", "C_delta", "K_delta"}:
        return "C"
    if unit in {"F", "delta_F", "F_delta"}:
        return "F"
    if unit == "K_abs":
        return "K"
    return None


def _temperature_absolute_delta_mismatch(left_unit, right_unit):
    left_abs = _is_absolute_temperature_unit(left_unit)
    right_abs = _is_absolute_temperature_unit(right_unit)
    left_delta = _is_temperature_delta_unit(left_unit)
    right_delta = _is_temperature_delta_unit(right_unit)
    if not ((left_abs or left_delta) and (right_abs or right_delta)):
        return False
    return (left_abs and right_delta) or (left_delta and right_abs)


def _same_temperature_kind_and_family(left_unit, right_unit):
    if _temperature_family(left_unit) != _temperature_family(right_unit):
        return False
    return (
        (_is_absolute_temperature_unit(left_unit) and _is_absolute_temperature_unit(right_unit))
        or (_is_temperature_delta_unit(left_unit) and _is_temperature_delta_unit(right_unit))
    )


def _is_piecewise_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"piecewise", "piecewise_select"}
        and not node.keywords
        and len(node.args) >= 3
    )


def _is_if_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"if_", "if_func"}
        and not node.keywords
        and len(node.args) == 3
    )


def _is_any_null_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "any_null"
        and not node.keywords
        and len(node.args) == 1
    )


def _is_is_null_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "is_null"
        and not node.keywords
        and len(node.args) == 1
    )


def _is_boolean_count_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {
            "count_true",
            "count_false",
            "count_true_ignore_null",
            "count_false_ignore_null",
        }
        and not node.keywords
        and len(node.args) == 1
    )


def _is_safe_int_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "int"
        and not node.keywords
        and len(node.args) == 1
    )


def _is_minmax_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"max", "min"}
        and not node.keywords
        and len(node.args) >= 1
    )


def _is_min_ignore_null_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "min_ignore_null"
        and not node.keywords
        and len(node.args) == 1
    )


def _is_max_ignore_null_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "max_ignore_null"
        and not node.keywords
        and len(node.args) == 1
    )


def _is_argmin_label_ignore_null_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "argmin_label_ignore_null"
        and not node.keywords
        and len(node.args) >= 2
    )


def _is_argmax_label_ignore_null_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "argmax_label_ignore_null"
        and not node.keywords
        and len(node.args) >= 2
    )


def _is_value_for_label_ignore_null_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "value_for_label_ignore_null"
        and not node.keywords
        and len(node.args) == 3
    )


def _infer_piecewise_unit(node, variable_units, names=None):
    value_units = []
    value_args = node.args[1::2]
    if len(node.args) % 2 == 1:
        value_args = node.args[1:-1:2] + [node.args[-1]]
    for value_node in value_args:
        if _is_null_node(value_node):
            continue
        if _is_string_node(value_node):
            value_units.append(_string_literal_unit(value_node.value))
            continue
        inferred = _infer_unit_node(value_node, variable_units, names=names)
        invalid = _first_invalid_unit(inferred)
        if invalid:
            return invalid
        if inferred.get("status") == "unknown":
            return _unit_result(None, "unknown", "info", "Piecewise output unit compatibility is unknown.")
        value_units.append(inferred.get("unit"))
    if not value_units:
        return _unit_result("dimensionless", "valid", "info", "Piecewise only contains null/default outputs.")
    textual_unit = _common_textual_unit(value_units)
    if textual_unit:
        return _unit_result(textual_unit, "valid", "info", f"Piecewise output unit inferred as {textual_unit}.")
    first = value_units[0]
    for unit in value_units[1:]:
        if not _units_validation_compatible(first, unit):
            return _unit_result(None, "invalid", "warning", f"Piecewise branches have incompatible units {first} and {unit}.")
    return _unit_result(first, "valid", "info", f"Piecewise output unit inferred as {first}.")


def _infer_if_unit(node, variable_units, names=None):
    condition_unit = _infer_unit_node(node.args[0], variable_units, names=names)
    invalid = _first_invalid_unit(condition_unit)
    if invalid:
        return invalid
    if condition_unit.get("status") == "unknown":
        return _unit_result(None, "unknown", "info", "If-expression condition unit compatibility is unknown.")
    if not _is_boolean_compatible_unit(condition_unit.get("unit")):
        return _unit_result(None, "invalid", "warning", f"If-expression condition must be boolean, found {condition_unit.get('unit')}.")

    true_is_null = _is_null_node(node.args[1])
    false_is_null = _is_null_node(node.args[2])
    true_unit = _infer_branch_value_unit(node.args[1], variable_units, names=names)
    false_unit = _infer_branch_value_unit(node.args[2], variable_units, names=names)
    invalid = _first_invalid_unit(true_unit, false_unit)
    if invalid:
        return invalid
    if true_is_null and false_is_null:
        return _unit_result("dimensionless", "valid", "info", "If-expression branches are both null.")
    if true_is_null:
        return false_unit
    if false_is_null:
        return true_unit
    if true_unit.get("status") == "unknown" or false_unit.get("status") == "unknown":
        return _unit_result(None, "unknown", "info", "If-expression output unit compatibility is unknown.")
    textual_unit = _common_textual_unit([true_unit.get("unit"), false_unit.get("unit")])
    if textual_unit:
        return _unit_result(textual_unit, "valid", "info", f"If-expression output unit inferred as {textual_unit}.")
    if not _units_validation_compatible(true_unit.get("unit"), false_unit.get("unit")):
        return _unit_result(
            None,
            "invalid",
            "warning",
            f"If-expression branches have incompatible units {true_unit.get('unit')} and {false_unit.get('unit')}.",
        )
    return _unit_result(true_unit.get("unit"), "valid", "info", f"If-expression output unit inferred as {true_unit.get('unit')}.")


def _infer_branch_value_unit(node, variable_units, names=None):
    if _is_null_node(node):
        return _unit_result("dimensionless", "valid", "info", "Null branch is dimensionless.")
    if _is_string_node(node):
        unit = _string_literal_unit(node.value)
        return _unit_result(unit, "valid", "info", f"String branch is {unit}.")
    return _infer_unit_node(node, variable_units, names=names)


def _infer_boolean_count_unit(node, variable_units, names=None):
    list_node = node.args[0]
    if isinstance(list_node, ast.Name):
        if names and isinstance(names.get(list_node.id), (list, tuple)):
            ignore_null = node.func.id.endswith("_ignore_null")
            for value in names.get(list_node.id):
                if is_missing_value(value):
                    if ignore_null:
                        continue
                    return _unit_result(None, "unknown", "info", "Boolean count helper result is unknown because the list contains null.")
                if _coerce_boolean(value) is None:
                    return _unit_result(None, "invalid", "warning", "Boolean count helper requires boolean or boolean-like list values.")
            return _unit_result("dimensionless", "valid", "info", f"{node.func.id} returns a dimensionless count.")
        unit = normalize_unit(variable_units.get(list_node.id))
        element_unit = _list_element_unit(unit)
        if element_unit and _is_boolean_compatible_unit(element_unit):
            return _unit_result("dimensionless", "valid", "info", f"{node.func.id} returns a dimensionless count.")
        if _is_list_unit(unit):
            return _unit_result(None, "invalid", "warning", f"Boolean count helper requires list[boolean], found {unit}.")
        return _unit_result(None, "invalid", "warning", "Boolean count helper expects a list argument.")

    if not isinstance(list_node, (ast.List, ast.Tuple)):
        return _unit_result(None, "invalid", "warning", "Boolean count helper expects a list argument.")

    ignore_null = node.func.id.endswith("_ignore_null")
    for item in list_node.elts:
        if _is_null_node(item):
            if ignore_null:
                continue
            return _unit_result(None, "unknown", "info", "Boolean count helper result is unknown because the list contains null.")
        inferred = _infer_unit_node(item, variable_units, names=names)
        invalid = _first_invalid_unit(inferred)
        if invalid:
            return invalid
        if inferred.get("status") == "unknown":
            return _unit_result(None, "unknown", "info", "Boolean count helper input unit is unknown.")
        if not _is_boolean_compatible_unit(inferred.get("unit")):
            return _unit_result(None, "invalid", "warning", f"Boolean count helper requires boolean inputs, found {inferred.get('unit')}.")

    return _unit_result("dimensionless", "valid", "info", f"{node.func.id} returns a dimensionless count.")


def _infer_safe_int_unit(node, variable_units, names=None):
    arg = node.args[0]
    if _is_null_node(arg):
        return _unit_result(None, "unknown", "info", "int(null) is unsupported because the boolean value is unknown.")
    inferred = _infer_unit_node(arg, variable_units, names=names)
    invalid = _first_invalid_unit(inferred)
    if invalid:
        return invalid
    if inferred.get("status") == "unknown":
        return _unit_result(None, "unknown", "info", "int() input unit is unknown.")
    if not _is_boolean_compatible_unit(inferred.get("unit")):
        return _unit_result(None, "invalid", "warning", f"int() only supports boolean inputs, found {inferred.get('unit')}.")
    return _unit_result("dimensionless", "valid", "info", "int(boolean) returns a dimensionless 0/1 value.")


def _infer_minmax_unit(node, variable_units, names=None):
    function_name = node.func.id if isinstance(node.func, ast.Name) else "min/max"
    if len(node.args) == 1:
        arg = node.args[0]
        inferred = _infer_unit_node(arg, variable_units, names=names)
        invalid = _first_invalid_unit(inferred)
        if invalid:
            return invalid
        if inferred.get("status") == "unknown":
            return _unit_result(None, "unknown", "info", f"{function_name}() argument unit is unknown.")
        unit = _normalize_inferred_element_unit(inferred.get("unit"))
        if _is_list_unit(unit):
            element_unit = _list_element_unit(unit)
            if element_unit is None:
                return _unit_result(None, "unknown", "info", f"{function_name}() list element unit is unknown.")
            if element_unit == "mixed":
                return _unit_result(None, "invalid", "warning", f"{function_name}() list argument has mixed units.")
            if not _minmax_unit_is_numeric_compatible(element_unit):
                return _unit_result(None, "invalid", "warning", f"{function_name}() requires numeric operands, found {element_unit}.")
            return _unit_result(element_unit, "valid", "info", f"{function_name}() over compatible list values preserves {element_unit}.")
        return _unit_result(None, "invalid", "warning", f"{function_name}() requires at least two scalar operands or one list argument.")

    first_unit = None
    for arg in node.args:
        inferred = _infer_unit_node(arg, variable_units, names=names)
        invalid = _first_invalid_unit(inferred)
        if invalid:
            return invalid
        if inferred.get("status") == "unknown":
            return _unit_result(None, "unknown", "info", f"{function_name}() argument unit is unknown.")
        unit = _normalize_inferred_element_unit(inferred.get("unit"))
        if _is_list_unit(unit):
            return _unit_result(None, "invalid", "warning", f"{function_name}() varargs form does not accept list operand {unit}.")
        if not _minmax_unit_is_numeric_compatible(unit):
            return _unit_result(None, "invalid", "warning", f"{function_name}() requires numeric operands, found {unit}.")
        if first_unit is None:
            first_unit = unit
            continue
        if not _units_validation_compatible(first_unit, unit):
            return _unit_result(None, "invalid", "warning", f"{function_name}() arguments have incompatible units {first_unit} and {unit}.")

    return _unit_result(first_unit, "valid", "info", f"{function_name}() preserves compatible argument unit {first_unit}.")


def _minmax_unit_is_numeric_compatible(unit):
    unit = normalize_unit(unit)
    return unit not in {None, "boolean", "unit_expression"} and not _is_textual_unit(unit) and not _is_list_unit(unit)


def _infer_min_ignore_null_unit(node, variable_units, names=None):
    return _infer_extreme_ignore_null_unit(node, variable_units, names=names)


def _infer_max_ignore_null_unit(node, variable_units, names=None):
    return _infer_extreme_ignore_null_unit(node, variable_units, names=names)


def _infer_extreme_ignore_null_unit(node, variable_units, names=None):
    helper_name = node.func.id if isinstance(node.func, ast.Name) else "ignore-null selector"
    list_node = node.args[0]
    value_unit = _infer_nullable_value_list_unit(list_node, variable_units, names=names)
    if value_unit.get("status") in {"invalid", "unknown"}:
        return value_unit
    return _unit_result(value_unit.get("unit"), "valid", "info", f"{helper_name} preserves compatible value unit {value_unit.get('unit')}.")


def _infer_argmin_label_ignore_null_unit(node, variable_units, names=None):
    return _infer_label_selector_ignore_null_unit(node, variable_units, names=names)


def _infer_argmax_label_ignore_null_unit(node, variable_units, names=None):
    return _infer_label_selector_ignore_null_unit(node, variable_units, names=names)


def _infer_label_selector_ignore_null_unit(node, variable_units, names=None):
    helper_name = node.func.id if isinstance(node.func, ast.Name) else "label selector"
    parsed = _selector_argument_nodes(node, variable_units=variable_units, names=names)
    if not parsed:
        return _unit_result(None, "invalid", "warning", f"{helper_name} expects at least two arguments.")
    label_node, viable_node, metric_nodes = parsed

    if not _unit_node_can_be_list(label_node, variable_units, names=names):
        return _unit_result(None, "invalid", "warning", f"{helper_name} labels argument must be a list.")
    if viable_node is not None:
        viable_unit = _infer_selector_viability_list_unit(viable_node, variable_units, names=names)
        if viable_unit.get("status") in {"invalid", "unknown"}:
            return viable_unit

    metric_units = []
    for metric_node in metric_nodes:
        value_unit = _infer_nullable_value_list_unit(metric_node, variable_units, names=names)
        if value_unit.get("status") == "invalid":
            return value_unit
        if value_unit.get("status") == "unknown":
            return _unit_result(None, "unknown", "info", f"{helper_name} metric-list unit compatibility is unknown.")
        metric_units.append(value_unit.get("unit"))

    label_unit = _infer_selector_label_list_unit(
        label_node,
        variable_units,
        names=names,
        primary_metric_node=metric_nodes[0] if metric_nodes else None,
        primary_metric_unit=metric_units[0] if metric_units else None,
    )
    if label_unit.get("status") in {"invalid", "unknown"}:
        return label_unit
    return _unit_result(
        label_unit.get("unit"),
        "valid",
        "info",
        f"{helper_name} returns the selected label/value with unit {label_unit.get('unit')}.",
    )


def _infer_selector_label_list_unit(
    label_node,
    variable_units,
    names=None,
    primary_metric_node=None,
    primary_metric_unit=None,
):
    if isinstance(label_node, ast.Name):
        declared = variable_units.get(label_node.id)
        element_unit = _list_element_unit(declared)
        if element_unit is None and declared is not None:
            element_unit = normalize_unit(declared)
        if element_unit and element_unit not in {"list"}:
            return _selector_label_unit_with_metric_fallback(
                _unit_result(element_unit, "valid", "info", f"Selector labels unit inferred from {label_node.id} as {element_unit}."),
                label_node,
                primary_metric_node,
                primary_metric_unit,
                names,
            )
        value = names.get(label_node.id) if isinstance(names, dict) else None
        if isinstance(value, (list, tuple)):
            return _selector_label_unit_with_metric_fallback(
                _infer_selector_label_values_unit(value),
                label_node,
                primary_metric_node,
                primary_metric_unit,
                names,
            )

    if not isinstance(label_node, (ast.List, ast.Tuple)):
        return _unit_result(None, "invalid", "warning", "Selector labels argument must be a list.")

    inferred_units = []
    for item in label_node.elts:
        if _is_null_node(item):
            continue
        inferred = _infer_unit_node(item, variable_units, names=names)
        invalid = _first_invalid_unit(inferred)
        if invalid:
            return invalid
        if inferred.get("status") == "unknown":
            return _unit_result(None, "unknown", "info", "Selector label-list unit compatibility is unknown.")
        unit = _normalize_inferred_element_unit(inferred.get("unit"))
        if unit == "boolean" or _is_list_unit(unit):
            return _unit_result(None, "invalid", "warning", f"Selector labels must be text or numeric values, found {unit}.")
        inferred_units.append(unit)

    if not inferred_units:
        return _unit_result("label_string", "valid", "info", "Selector labels contain only null values.")

    textual_unit = _common_textual_unit(inferred_units)
    if textual_unit:
        return _selector_label_unit_with_metric_fallback(
            _unit_result(textual_unit, "valid", "info", f"Selector label-list unit inferred as {textual_unit}."),
            label_node,
            primary_metric_node,
            primary_metric_unit,
            names,
        )

    first = inferred_units[0]
    for unit in inferred_units[1:]:
        if not _units_validation_compatible(first, unit):
            return _unit_result(None, "invalid", "warning", f"Selector label-list units are incompatible: {first} and {unit}.")
    return _selector_label_unit_with_metric_fallback(
        _unit_result(first, "valid", "info", f"Selector label-list unit inferred as {first}."),
        label_node,
        primary_metric_node,
        primary_metric_unit,
        names,
    )


def _infer_selector_label_values_unit(values):
    inferred_units = []
    for value in values:
        if is_missing_value(value):
            continue
        if isinstance(value, bool):
            return _unit_result(None, "invalid", "warning", "Selector labels must not be boolean values.")
        if _coerce_number(value) is not None:
            inferred_units.append("dimensionless")
        elif isinstance(value, str):
            inferred_units.append(_string_literal_unit(value))
        else:
            return _unit_result(None, "unknown", "info", "Selector label-list value unit is unknown.")

    if not inferred_units:
        return _unit_result("label_string", "valid", "info", "Selector labels contain only null values.")
    textual_unit = _common_textual_unit(inferred_units)
    if textual_unit:
        return _unit_result(textual_unit, "valid", "info", f"Selector label-list unit inferred from runtime values as {textual_unit}.")
    first = inferred_units[0]
    for unit in inferred_units[1:]:
        if not _units_validation_compatible(first, unit):
            return _unit_result(None, "invalid", "warning", f"Selector label-list units are incompatible: {first} and {unit}.")
    return _unit_result(first, "valid", "info", f"Selector label-list unit inferred from runtime values as {first}.")


def _selector_label_unit_with_metric_fallback(label_unit, label_node, metric_node, metric_unit, names):
    if label_unit.get("status") != "valid":
        return label_unit
    normalized_label_unit = normalize_unit(label_unit.get("unit"))
    normalized_metric_unit = normalize_unit(metric_unit)
    if normalized_label_unit != "dimensionless":
        return label_unit
    if normalized_metric_unit in {None, "dimensionless", "boolean"} or _is_textual_unit(normalized_metric_unit):
        return label_unit
    if _selector_numeric_labels_match_metric_values(label_node, metric_node, names):
        return _unit_result(
            normalized_metric_unit,
            "valid",
            "info",
            f"Numeric selector labels match primary metric values; selected label inherits metric unit {normalized_metric_unit}.",
        )
    return label_unit


def _selector_numeric_labels_match_metric_values(label_node, metric_node, names):
    if metric_node is None or not isinstance(names, dict):
        return False
    try:
        labels = _nullable_list_values_from_node(label_node, names, set(), "selector", "labels")
        metrics = _nullable_list_values_from_node(metric_node, names, set(), "selector", "values")
    except Exception:
        return False
    if labels is None or metrics is None or len(labels) != len(metrics):
        return False
    comparable = False
    for label, metric in zip(labels, metrics, strict=False):
        if is_missing_value(label) or is_missing_value(metric):
            continue
        label_number = _coerce_number(label)
        metric_number = _coerce_number(metric)
        if label_number is None or metric_number is None:
            return False
        comparable = True
        if not math.isclose(float(label_number), float(metric_number), rel_tol=1e-12, abs_tol=1e-12):
            return False
    return comparable


def _selector_argument_nodes(node, variable_units=None, names=None):
    if not isinstance(node, ast.Call) or len(node.args) < 2:
        return None
    if len(node.args) == 2:
        if _selector_two_arg_nodes_are_labels_first(node.args[0], node.args[1], variable_units or {}, names):
            return node.args[0], None, [node.args[1]]
        return node.args[1], None, [node.args[0]]
    return node.args[0], node.args[1], list(node.args[2:])


def _selector_two_arg_nodes_are_labels_first(first_node, second_node, variable_units, names=None):
    if _selector_node_contains_text_label(first_node, variable_units, names=names):
        return True
    if _selector_node_contains_text_label(second_node, variable_units, names=names):
        return False
    first_metric = _selector_node_is_metric_compatible(first_node, variable_units, names=names)
    second_metric = _selector_node_is_metric_compatible(second_node, variable_units, names=names)
    return bool(second_metric and not first_metric)


def _selector_node_contains_text_label(node, variable_units, names=None):
    if isinstance(node, ast.Name) and isinstance(names, dict):
        value = names.get(node.id)
        if isinstance(value, (list, tuple)):
            return _selector_values_contain_text_label(value)
    if isinstance(node, ast.Name):
        unit = normalize_unit(_list_element_unit(variable_units.get(node.id)) or variable_units.get(node.id))
        return _is_textual_unit(unit)
    if isinstance(node, (ast.List, ast.Tuple)):
        return any(_node_is_text_label_literal(item) for item in node.elts)
    return False


def _node_is_text_label_literal(node):
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and _coerce_number(node.value) is None
        and not is_missing_value(node.value)
    )


def _selector_node_is_metric_compatible(node, variable_units, names=None):
    if isinstance(node, ast.Name) and isinstance(names, dict):
        value = names.get(node.id)
        if isinstance(value, (list, tuple)):
            return _selector_values_are_metric_compatible(value)
    unit = None
    if isinstance(node, ast.Name):
        unit = normalize_unit(_list_element_unit(variable_units.get(node.id)) or variable_units.get(node.id))
        if unit and not _is_textual_unit(unit) and unit not in {"boolean", "list"}:
            return True
    if isinstance(node, (ast.List, ast.Tuple)):
        for item in node.elts:
            if _is_null_node(item):
                continue
            if _is_numeric_constant(item):
                continue
            if isinstance(item, ast.Constant) and isinstance(item.value, Decimal):
                continue
            if isinstance(item, ast.Name):
                item_unit = normalize_unit(variable_units.get(item.id) or _unit_from_name_suffix(item.id))
                if item_unit and not _is_textual_unit(item_unit) and item_unit != "boolean":
                    continue
            return False
        return True
    return False


def _infer_selector_viability_list_unit(node, variable_units, names=None):
    if isinstance(node, ast.Name):
        if names and isinstance(names.get(node.id), (list, tuple)):
            values = names.get(node.id)
            for value in values:
                if is_missing_value(value):
                    continue
                if _coerce_boolean(value) is None:
                    return _unit_result(None, "invalid", "warning", "Selector viability flags must be boolean or boolean-like values.")
            return _unit_result("boolean", "valid", "info", "Selector viability list contains boolean-like values.")
        unit = normalize_unit(variable_units.get(node.id))
        element_unit = _list_element_unit(unit)
        if element_unit and _is_boolean_compatible_unit(element_unit):
            return _unit_result("boolean", "valid", "info", f"Selector viability list {node.id} has boolean unit.")
        if _is_boolean_compatible_unit(unit):
            return _unit_result(None, "invalid", "warning", f"Selector viability flags must be a list, found scalar {unit}.")
        return _unit_result(None, "invalid", "warning", f"Selector viability flags must be list[boolean], found {unit}.")

    if not isinstance(node, (ast.List, ast.Tuple)):
        return _unit_result(None, "invalid", "warning", "Selector viability flags argument must be a list.")

    for item in node.elts:
        if _is_null_node(item):
            continue
        inferred = _infer_unit_node(item, variable_units, names=names)
        invalid = _first_invalid_unit(inferred)
        if invalid:
            return invalid
        if inferred.get("status") == "unknown":
            return _unit_result(None, "unknown", "info", "Selector viability flag unit is unknown.")
        if not _is_boolean_compatible_unit(inferred.get("unit")):
            return _unit_result(None, "invalid", "warning", f"Selector viability flags must be boolean, found {inferred.get('unit')}.")
    return _unit_result("boolean", "valid", "info", "Selector viability list contains boolean values.")


def _infer_value_for_label_ignore_null_unit(node, variable_units, names=None):
    if not _unit_node_can_be_list(node.args[1], variable_units, names=names):
        return _unit_result(None, "invalid", "warning", "value_for_label_ignore_null labels argument must be a list.")
    value_unit = _infer_lookup_value_list_unit(node.args[2], variable_units, names=names)
    if value_unit.get("status") in {"invalid", "unknown"}:
        return value_unit
    return _unit_result(
        value_unit.get("unit"),
        "valid",
        "info",
        f"value_for_label_ignore_null preserves compatible value unit {value_unit.get('unit')}.",
    )


def _infer_lookup_value_list_unit(list_node, variable_units, names=None):
    if isinstance(list_node, ast.Name):
        value = names.get(list_node.id) if isinstance(names, dict) else None
        if isinstance(value, (list, tuple)):
            unit = _list_element_unit(variable_units.get(list_node.id)) or normalize_unit(variable_units.get(list_node.id) or _unit_from_name_suffix(list_node.id))
            if unit and unit != "list":
                return _unit_result(unit, "valid", "info", f"Lookup value-list unit inferred from {list_node.id} as {unit}.")
            return _infer_lookup_runtime_values_unit(value)
        if list_node.id in variable_units:
            unit = _list_element_unit(variable_units.get(list_node.id)) or normalize_unit(variable_units.get(list_node.id))
            if unit == "list":
                return _unit_result(None, "unknown", "info", f"Lookup value-list element unit for {list_node.id} is unknown.")
            return _unit_result(unit, "valid", "info", f"Lookup value-list unit inferred from {list_node.id} as {unit}.")

    if not isinstance(list_node, (ast.List, ast.Tuple)):
        return _unit_result(None, "invalid", "warning", "Lookup value helper expects a list argument.")

    inferred_units = []
    for item in list_node.elts:
        if _is_null_node(item):
            continue
        inferred = _infer_unit_node(item, variable_units, names=names)
        invalid = _first_invalid_unit(inferred)
        if invalid:
            return invalid
        if inferred.get("status") == "unknown":
            return _unit_result(None, "unknown", "info", "Lookup value-list unit compatibility is unknown.")
        unit = _normalize_inferred_element_unit(inferred.get("unit"))
        if _is_list_unit(unit):
            return _unit_result(None, "invalid", "warning", f"Lookup value helper cannot select from nested list values {unit}.")
        inferred_units.append(unit)

    return _compatible_lookup_value_unit(inferred_units, "Lookup value-list")


def _infer_lookup_runtime_values_unit(values):
    inferred_units = []
    for value in values:
        if is_missing_value(value):
            continue
        if isinstance(value, bool):
            inferred_units.append("boolean")
        elif _coerce_number(value) is not None:
            inferred_units.append("dimensionless")
        elif isinstance(value, str):
            inferred_units.append(_string_literal_unit(value))
        else:
            return _unit_result(None, "unknown", "info", "Lookup value-list runtime value unit is unknown.")
    return _compatible_lookup_value_unit(inferred_units, "Lookup value-list runtime")


def _compatible_lookup_value_unit(inferred_units, context):
    if not inferred_units:
        return _unit_result("dimensionless", "valid", "info", f"{context} contains only null values.")
    textual_unit = _common_textual_unit(inferred_units)
    if textual_unit:
        return _unit_result(textual_unit, "valid", "info", f"{context} unit inferred as {textual_unit}.")
    first = inferred_units[0]
    for unit in inferred_units[1:]:
        if not _units_validation_compatible(first, unit):
            return _unit_result(None, "invalid", "warning", f"{context} units are incompatible: {first} and {unit}.")
    return _unit_result(first, "valid", "info", f"{context} unit inferred as {first}.")


def _unit_node_can_be_list(node, variable_units, names=None):
    if isinstance(node, (ast.List, ast.Tuple)):
        return True
    if isinstance(node, ast.Name):
        if names and isinstance(names.get(node.id), (list, tuple)):
            return True
        return _is_list_unit(variable_units.get(node.id))
    return False


def _infer_nullable_value_list_unit(list_node, variable_units, names=None):
    if isinstance(list_node, ast.Name):
        value = names.get(list_node.id) if isinstance(names, dict) else None
        if isinstance(value, (list, tuple)):
            unit = _list_element_unit(variable_units.get(list_node.id)) or normalize_unit(variable_units.get(list_node.id) or _unit_from_name_suffix(list_node.id))
            if unit in {"boolean", "list"} or _is_textual_unit(unit):
                return _unit_result(None, "invalid", "warning", f"Nullable numeric helper cannot select from {unit} values.")
            return _unit_result(unit, "valid", "info", f"Nullable value-list unit inferred from {list_node.id} as {unit}.")
        if list_node.id in variable_units:
            unit = _list_element_unit(variable_units.get(list_node.id)) or normalize_unit(variable_units.get(list_node.id))
            if unit in {"boolean", "list"} or _is_textual_unit(unit):
                return _unit_result(None, "invalid", "warning", f"Nullable numeric helper cannot select from {unit} values.")
            return _unit_result(unit, "valid", "info", f"Nullable value-list unit inferred from {list_node.id} as {unit}.")

    if not isinstance(list_node, (ast.List, ast.Tuple)):
        return _unit_result(None, "invalid", "warning", "Nullable value helper expects a list argument.")

    inferred_units = []
    for item in list_node.elts:
        if _is_null_node(item):
            continue
        inferred = _infer_unit_node(item, variable_units, names=names)
        invalid = _first_invalid_unit(inferred)
        if invalid:
            return invalid
        if inferred.get("status") == "unknown":
            return _unit_result(None, "unknown", "info", "Nullable value-list unit compatibility is unknown.")
        unit = inferred.get("unit")
        if normalize_unit(unit) == "boolean" or _is_textual_unit(unit) or _is_list_unit(unit):
            return _unit_result(None, "invalid", "warning", f"Nullable numeric helper cannot select from {unit} values.")
        inferred_units.append(unit)

    if not inferred_units:
        return _unit_result("dimensionless", "valid", "info", "Nullable value list contains only null values.")

    first = inferred_units[0]
    for unit in inferred_units[1:]:
        if not _units_validation_compatible(first, unit):
            return _unit_result(None, "invalid", "warning", f"Nullable value-list units are incompatible: {first} and {unit}.")

    return _unit_result(first, "valid", "info", f"Nullable value-list unit inferred as {first}.")


def _is_string_node(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _combine_divide_units(left, right, left_node, right_node, names=None, variable_units=None):
    invalid = _first_invalid_unit(left, right)
    if invalid:
        return invalid
    if left["status"] == "unknown" or right["status"] == "unknown":
        return _unit_result(None, "unknown", "info", "Division unit compatibility is unknown.")

    left_unit = left["unit"]
    right_unit = right["unit"]

    if (
        _is_resistance_per_1000ft_expression(left_node, variable_units or {})
        and normalize_unit(right_unit) in {"dimensionless", "percent"}
        and _is_1000ft_denominator_factor(right_node, names)
    ):
        return _unit_result(
            "ohm/ft",
            "valid",
            "info",
            "Unit validation passed: ohm/1000ft divided by an explicit 1000-ft denominator produces ohm/ft.",
        )

    conversion = _named_conversion_factor_unit_result(left_unit, right_unit, right_node, names, "divide")
    if conversion:
        return conversion

    if _is_hp_rpm_torque_conversion_division(left_unit, right_unit, left_node, right_node, names):
        return _unit_result(
            "lbf*ft",
            "valid",
            "info",
            "Known torque conversion rule: hp * 5252 / rpm -> lbf*ft.",
        )

    if _is_lbf_fpm_horsepower_conversion_division(
        left_unit,
        right_unit,
        left_node,
        right_node,
        names,
        variable_units or {},
    ):
        return _unit_result(
            "hp",
            "valid",
            "info",
            "Known horsepower conversion rule: lbf * ft/min divided by 33000 produces hp.",
        )

    if left_unit == "kJ" and right_unit == "dimensionless" and _is_numeric_literal(right_node, 3600):
        return _unit_result("kWh", "valid", "info", "Known conversion rule: kJ / 3600 -> kWh.")
    if left_unit == "kJ" and right_unit == "dimensionless" and _is_name(right_node, "kJ_per_kWh"):
        return _unit_result("kWh", "valid", "info", "Known conversion rule: kJ / kJ_per_kWh -> kWh.")
    if left_unit == "kJ" and right_unit == "kJ/kWh":
        return _unit_result("kWh", "valid", "info", "Known division unit rule: kJ / kJ/kWh -> kWh.")
    if left_unit == "Wh" and right_unit == "W":
        return _unit_result("h", "valid", "info", "Known division unit rule: Wh / W -> h.")
    if left_unit == "kWh" and right_unit == "kW":
        return _unit_result("h", "valid", "info", "Known division unit rule: kWh / kW -> h.")
    if left_unit == "kWh" and right_unit == "h":
        return _unit_result("kW", "valid", "info", "Known division unit rule: kWh / h -> kW.")
    if left_unit == "Ah" and right_unit == "A":
        return _unit_result("h", "valid", "info", "Known division unit rule: Ah / A -> h.")
    if left_unit == "V" and right_unit == "ohm":
        return _unit_result("A", "valid", "info", "Known division unit rule: V / ohm -> A.")
    if left_unit == "V" and right_unit == "A":
        return _unit_result("ohm", "valid", "info", "Known division unit rule: V / A -> ohm.")
    if left_unit == "kg" and right_unit == "C":
        return _unit_result("kg/C", "valid", "info", "Known division unit rule: kg / C -> kg/C.")
    if left_unit == "in" and _is_inches_per_foot_unit(right_unit):
        return _unit_result("ft", "valid", "info", "Known conversion rule: in / in/ft -> ft.")
    numeric_length_conversion = _numeric_inch_length_division_unit_result(
        left_unit,
        right_unit,
        left_node,
        right_node,
    )
    if numeric_length_conversion:
        return numeric_length_conversion
    if left_unit == "ft" and right_unit == "min":
        return _unit_result("fpm", "valid", "info", "Known division unit rule: ft / min -> fpm.")
    if left_unit == "ft" and right_unit == "s":
        return _unit_result("ft/s", "valid", "info", "Known division unit rule: ft / s -> ft/s.")
    if left_unit == "m" and right_unit == "s":
        return _unit_result("m/s", "valid", "info", "Known division unit rule: m / s -> m/s.")
    if _is_cfm_unit(left_unit) and _is_fpm_unit(right_unit):
        return _unit_result("ft^2", "valid", "info", "Known airflow area unit rule: cfm / fpm -> ft^2.")
    if _is_cfm_unit(left_unit) and _is_square_foot_unit(right_unit):
        return _unit_result("fpm", "valid", "info", "Known airflow unit rule: cfm / ft^2 -> fpm.")
    if _is_cfs_unit(left_unit) and _is_square_foot_unit(right_unit):
        return _unit_result("ft/s", "valid", "info", "Known hydraulic velocity unit rule: ft^3/s / ft^2 -> ft/s.")
    thermal_interval = _thermal_conductance_division_unit(left_unit, right_unit)
    if thermal_interval:
        return _unit_result(
            thermal_interval,
            "valid",
            "info",
            f"Thermal conductance division {left_unit} / {right_unit} produces a temperature interval.",
        )
    conversion = _conversion_ratio_divide_result_unit(left_unit, right_unit)
    if conversion:
        return _unit_result(
            conversion,
            "valid",
            "info",
            f"Conversion-ratio division reduced {left_unit} / {right_unit} -> {conversion}.",
        )
    if right_unit in {"dimensionless", "percent"}:
        preserved = _hydraulic_head_preserved_unit(left_unit, left_node) or left_unit
        return _unit_result(preserved, "valid", "info", f"Division by dimensionless value preserves {preserved}.")
    if left_unit == right_unit:
        return _unit_result("dimensionless", "valid", "info", f"Same-unit ratio {left_unit}/{right_unit} is dimensionless.")

    reduced = _compose_units_by_dimensions(left_unit, right_unit, "/")
    if reduced:
        return _unit_result(
            reduced,
            "valid",
            "info",
            f"Compound-unit division reduced {left_unit} / {right_unit} -> {reduced}.",
        )

    return _unit_result(None, "unknown", "info", f"Division unit rule is not known for {left_unit} / {right_unit}.")


def _is_hp_rpm_torque_conversion_division(left_unit, right_unit, left_node, right_node, names):
    if normalize_unit(left_unit) != "hp" or normalize_unit(right_unit) != "rpm":
        return False
    if not _node_contains_standard_5252_torque_factor(left_node, names):
        return False
    return _node_is_rpm_speed_operand(right_node) or normalize_unit(right_unit) == "rpm"


def _node_contains_standard_5252_torque_factor(node, names):
    for child in ast.walk(node):
        if _is_standard_5252_torque_factor(child, names):
            return True
    return False


def _is_standard_5252_torque_factor(node, names):
    value = _numeric_node_or_named_value(node, names)
    if value is not None and _is_5252_like_value(value):
        return True
    if isinstance(node, ast.Name):
        compact = re.sub(r"[^a-z0-9]+", "", node.id.lower())
        return (
            "5252" in compact
            and any(marker in compact for marker in ("torque", "conversion", "factor"))
        )
    return False


def _is_5252_like_value(value):
    return _is_number(value) and math.isclose(float(value), 5252.0, rel_tol=1e-4, abs_tol=0.5)


def _node_is_rpm_speed_operand(node):
    if isinstance(node, ast.Name):
        lowered = node.id.lower()
        return "rpm" in lowered or "speed" in lowered
    return False


def _is_lbf_fpm_horsepower_conversion_division(left_unit, right_unit, left_node, right_node, names, variable_units):
    if normalize_unit(right_unit) not in {"dimensionless", "percent"}:
        return False
    if not _is_lbf_fpm_power_unit(left_unit):
        return False
    if not _left_node_is_lbf_fpm_power_expression(left_node, variable_units):
        return False
    return _denominator_contains_33000_horsepower_factor(right_node, names)


def _is_lbf_fpm_power_unit(unit):
    dims = _unit_dimensions(unit)
    if dims is None:
        return False
    return dims == {"lbf": 1, "m": 1, "s": -1}


def _left_node_is_lbf_fpm_power_expression(node, variable_units):
    force_seen = False
    speed_seen = False
    length_seen = False
    minute_denominator_seen = False

    for factor, sign in _multiplicative_factors(node):
        unit = normalize_unit(_factor_unit(factor, variable_units))
        if sign > 0:
            if unit == "lbf":
                force_seen = True
                continue
            if _is_fpm_unit(unit):
                speed_seen = True
                continue
            if unit == "ft":
                length_seen = True
                continue
            if unit in {"dimensionless", "percent"}:
                continue
            return False
        if sign < 0:
            if unit == "min":
                minute_denominator_seen = True
                continue
            if unit in {"dimensionless", "percent"}:
                continue
            return False

    return force_seen and (speed_seen or (length_seen and minute_denominator_seen))


def _denominator_contains_33000_horsepower_factor(node, names):
    for factor, sign in _multiplicative_factors(node):
        if sign > 0 and _is_33000_horsepower_factor(factor, names):
            return True
    return False


def _is_33000_horsepower_factor(node, names):
    value = _numeric_node_or_named_value(node, names)
    if value is not None and _is_33000_like_value(value):
        return True
    if isinstance(node, ast.Name):
        compact = re.sub(r"[^a-z0-9]+", "", node.id.lower())
        return (
            "33000" in compact
            and any(marker in compact for marker in ("hp", "horsepower", "conversion", "factor"))
        )
    return False


def _is_33000_like_value(value):
    return _is_number(value) and math.isclose(float(value), 33000.0, rel_tol=1e-6, abs_tol=1.0)


def _infer_compare_units(node, variable_units, names=None):
    left = _infer_unit_node(node.left, variable_units, names=names)
    if left["status"] == "invalid":
        return left

    current = left
    current_node = node.left
    for op, comparator in zip(node.ops, node.comparators, strict=False):
        right = _infer_unit_node(comparator, variable_units, names=names)
        invalid = _first_invalid_unit(current, right)
        if invalid:
            return invalid
        if current["status"] == "unknown" or right["status"] == "unknown":
            return _unit_result(None, "unknown", "info", "Comparison unit compatibility is unknown.")
        if _null_comparison_compatible(current_node, comparator):
            current = right
            current_node = comparator
            continue
        if _boolean_binary_comparison_compatible(current, current_node, right, comparator, op):
            current = right
            current_node = comparator
            continue
        if _hydraulic_head_comparison_compatible(current, current_node, right, comparator):
            current = right
            current_node = comparator
            continue
        temperature_comparison = _temperature_comparison_unit_result(current["unit"], right["unit"])
        if temperature_comparison:
            if temperature_comparison.get("status") == "invalid":
                return temperature_comparison
            current = right
            current_node = comparator
            continue
        if not (
            _units_validation_compatible(current["unit"], right["unit"])
            or _numeric_literal_comparison_compatible(current, current_node, right, comparator)
        ):
            return _unit_result(
                None,
                "invalid",
                "warning",
                f"Cannot compare incompatible units {current['unit']} and {right['unit']}.",
            )
        current = right
        current_node = comparator

    return _unit_result("boolean", "valid", "info", "Comparison of compatible units produces boolean.")


def _temperature_comparison_unit_result(left_unit, right_unit):
    left_unit = normalize_unit(left_unit)
    right_unit = normalize_unit(right_unit)
    if not (_is_temperature_unit_family(left_unit) or _is_temperature_unit_family(right_unit)):
        return None
    if _temperature_absolute_delta_mismatch(left_unit, right_unit):
        absolute_unit = left_unit if _is_absolute_temperature_unit(left_unit) else right_unit
        delta_unit = left_unit if _is_temperature_delta_unit(left_unit) else right_unit
        return _unit_result(
            None,
            "invalid",
            "warning",
            f"Cannot compare absolute temperature {absolute_unit} with temperature interval {delta_unit}.",
        )
    if _same_temperature_kind_and_family(left_unit, right_unit):
        return _unit_result("boolean", "valid", "info", "Temperature comparison uses compatible temperature units.")
    return None


def _hydraulic_head_comparison_compatible(left, left_node, right, right_node):
    left_unit = normalize_unit(left.get("unit"))
    right_unit = normalize_unit(right.get("unit"))
    if not (_is_hydraulic_head_family_unit(left_unit) and _is_hydraulic_head_family_unit(right_unit)):
        return False
    return (
        _hydraulic_head_operand_is_safe(left_unit, left_node)
        and _hydraulic_head_operand_is_safe(right_unit, right_node)
    )


def _null_comparison_compatible(left_node, right_node):
    return _is_null_node(left_node) or _is_null_node(right_node)


def _boolean_binary_comparison_compatible(left, left_node, right, right_node, op):
    if not isinstance(op, (ast.Eq, ast.NotEq)):
        return False
    left_unit = normalize_unit(left.get("unit"))
    right_unit = normalize_unit(right.get("unit"))
    if _is_boolean_compatible_unit(left_unit) and _is_boolean_compatible_unit(right_unit):
        return True
    if _is_boolean_compatible_unit(left_unit) and _is_binary_numeric_literal(right_node):
        return True
    if _is_boolean_compatible_unit(right_unit) and _is_binary_numeric_literal(left_node):
        return True
    return False


def _is_binary_numeric_literal(node):
    value = _constant_numeric_value(node)
    return value is not None and (math.isclose(value, 0.0, abs_tol=1e-12) or math.isclose(value, 1.0, abs_tol=1e-12))


def _is_boolean_compatible_unit(unit):
    return normalize_unit(unit) == "boolean"


def _numeric_literal_comparison_compatible(left, left_node, right, right_node):
    if _is_numeric_constant(right_node) and right.get("unit") == "dimensionless":
        return left.get("unit") not in {None, "dimensionless", "boolean"}
    if _is_numeric_constant(left_node) and left.get("unit") == "dimensionless":
        return right.get("unit") not in {None, "dimensionless", "boolean"}
    return False


def _is_numeric_constant(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)


def _constant_numeric_value(node):
    if _is_numeric_constant(node):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)) and _is_numeric_constant(node.operand):
        value = float(node.operand.value)
        return -value if isinstance(node.op, ast.USub) else value
    return None


def _first_invalid_unit(*items):
    for item in items:
        if item.get("status") == "invalid":
            return item
    return None


def _units_validation_compatible(left_unit, right_unit):
    left_unit = normalize_unit(left_unit)
    right_unit = normalize_unit(right_unit)
    if left_unit == right_unit:
        return True
    if _is_list_unit(left_unit) or _is_list_unit(right_unit):
        if not (_is_list_unit(left_unit) and _is_list_unit(right_unit)):
            return False
        left_element = _list_element_unit(left_unit)
        right_element = _list_element_unit(right_unit)
        if left_element is None or right_element is None:
            return True
        if "mixed" in {left_element, right_element}:
            return left_element == right_element
        return _units_validation_compatible(left_element, right_element)
    if {left_unit, right_unit} == {"percent", "dimensionless"}:
        return True
    if {left_unit, right_unit} == {"pass_fail_unknown", "status_string"}:
        return True
    if _is_textual_unit(left_unit) and _is_textual_unit(right_unit):
        return True
    if _has_mixed_si_imperial_length_units(left_unit, right_unit):
        return False
    if _temperature_absolute_delta_mismatch(left_unit, right_unit):
        return False
    if _is_temperature_interval_unit(left_unit) and _is_temperature_interval_unit(right_unit):
        return True
    if _is_temperature_interval_unit(left_unit) and right_unit == "K":
        return True
    if left_unit == "K" and _is_temperature_interval_unit(right_unit):
        return True
    left_dims = _unit_dimensions(left_unit)
    right_dims = _unit_dimensions(right_unit)
    if left_dims is None or right_dims is None:
        return False
    return left_dims == right_dims


def _has_mixed_si_imperial_length_units(left_unit, right_unit):
    left_system = _length_unit_system(left_unit)
    right_system = _length_unit_system(right_unit)
    return left_system is not None and right_system is not None and left_system != right_system


def _length_unit_system(unit):
    unit = normalize_unit(unit)
    if not unit:
        return None
    tokens = set(re.findall(r"[A-Za-z_]+", str(unit)))
    if tokens.intersection({"ft", "in", "cfm", "fpm"}):
        return "imperial"
    if tokens.intersection({"m", "L"}):
        return "si"
    return None


def _compose_units_by_dimensions(left_unit, right_unit, operator):
    left_dims = _unit_dimensions(left_unit)
    right_dims = _unit_dimensions(right_unit)
    if left_dims is None or right_dims is None:
        return None
    if operator == "*":
        dims = _add_unit_dimensions(left_dims, right_dims)
    elif operator == "/":
        dims = _add_unit_dimensions(left_dims, _scale_unit_dimensions(right_dims, -1))
    else:
        return None
    return _canonical_unit_from_dimensions(dims)


def _unit_dimensions(unit):
    """Parse simple engineering units into dimensional exponents for validation only.

    Scale factors such as k, L-to-m^3, minutes-to-seconds, and hours-to-seconds are
    intentionally ignored here because numeric conversion is handled by explicit
    equation factors. The dimensional map only answers compatibility questions.
    """
    unit = normalize_unit(unit)
    if unit in (None, "dimensionless"):
        return {}
    if _is_list_unit(unit):
        return None
    if unit in {"boolean", "unit_expression", "percent"} or _is_textual_unit(unit):
        return None
    if unit in {"delta_C", "C_delta", "K_delta"}:
        return {"K": 1}
    if unit in {"delta_F", "F_delta"}:
        return {"F": 1}
    if unit == "inH2O":
        return {"pressure_inH2O": 1}
    if unit == "Ah":
        return {"A": 1, "s": 1}
    if _unit_text_is_resistance_per_1000ft(unit):
        return {"V": 1, "A": -1, "m": -1}
    if unit == "C":
        return {"C_abs": 1}
    if unit == "K_abs":
        return {"K_abs": 1}
    if unit == "K":
        return {"K": 1}

    parser = _UnitExpressionParser(str(unit))
    try:
        dims = parser.parse()
    except ValueError:
        return None
    return dims


class _UnitExpressionParser:
    def __init__(self, text):
        cleaned = (
            str(text)
            .strip()
            .replace(" ", "")
            .replace("Â·", "*")
            .replace("·", "*")
            .replace("Â°", "deg")
            .replace("°", "deg")
        )
        self.tokens = re.findall(r"[A-Za-z_$]+|\d+(?:\.\d+)?|\^|\*|/|\(|\)", cleaned)
        self.index = 0

    def parse(self):
        if not self.tokens:
            return {}
        dims = self._parse_product()
        if self.index != len(self.tokens):
            raise ValueError("Unexpected unit token.")
        return dims

    def _parse_product(self):
        dims = self._parse_factor()
        while self._peek() in {"*", "/"}:
            operator = self._take()
            right = self._parse_factor()
            if operator == "*":
                dims = _add_unit_dimensions(dims, right)
            else:
                dims = _add_unit_dimensions(dims, _scale_unit_dimensions(right, -1))
        return dims

    def _parse_factor(self):
        token = self._take()
        if token is None:
            raise ValueError("Missing unit factor.")
        if token == "(":
            dims = self._parse_product()
            if self._take() != ")":
                raise ValueError("Unclosed unit group.")
        elif token == ")":
            raise ValueError("Unexpected unit group close.")
        else:
            dims = _base_unit_dimensions(token)

        if self._peek() == "^":
            self._take()
            exponent = self._take()
            if exponent is None or not re.fullmatch(r"\d+(?:\.\d+)?", exponent):
                raise ValueError("Invalid unit exponent.")
            dims = _scale_unit_dimensions(dims, float(exponent))
        return dims

    def _peek(self):
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _take(self):
        token = self._peek()
        if token is not None:
            self.index += 1
        return token


def _base_unit_dimensions(token):
    unit = normalize_unit(token)
    # In compound units, degC/C appears as a temperature interval dimension.
    # Absolute C-to-K compatibility is handled separately for subtraction only.
    mapping = {
        "dimensionless": {},
        "kg": {"kg": 1},
        "m": {"m": 1},
        "m^2": {"m": 2},
        "ft": {"m": 1},
        "ft^2": {"m": 2},
        "ft^3": {"m": 3},
        "ft/s": {"m": 1, "s": -1},
        "ft^3/s": {"m": 3, "s": -1},
        "m/s": {"m": 1, "s": -1},
        "cfm": {"m": 3, "s": -1},
        "fpm": {"m": 1, "s": -1},
        "cycle": {"cycle": 1},
        "scf": {"scf": 1},
        "scfm": {"scf": 1, "s": -1},
        "gpm": {"gal": 1, "s": -1},
        "in": {"in": 1},
        "in^2": {"in": 2},
        "in^3": {"in": 3},
        "in^4": {"in": 4},
        "lbf": {"lbf": 1},
        "lbf_in": {"lbf": 1, "in": 1},
        "psi": {"lbf": 1, "in": -2},
        "psf": {"lbf": 1, "m": -2},
        "inH2O": {"pressure_inH2O": 1},
        "hp": {"hp": 1},
        "rpm": {"s": -1},
        "N": {"kg": 1, "m": 1, "s": -2},
        "Pa": {"kg": 1, "m": -1, "s": -2},
        "lb": {"lb": 1},
        "m^3": {"m": 3},
        "L": {"m": 3},
        "gal": {"gal": 1},
        "s": {"s": 1},
        "min": {"s": 1},
        "h": {"s": 1},
        "year": {"year": 1},
        "J": {"kg": 1, "m": 2, "s": -2},
        "kJ": {"kg": 1, "m": 2, "s": -2},
        "W": {"kg": 1, "m": 2, "s": -3},
        "kW": {"kg": 1, "m": 2, "s": -3},
        "Wh": {"kg": 1, "m": 2, "s": -2},
        "kWh": {"kg": 1, "m": 2, "s": -2},
        "K": {"K": 1},
        "F": {"F": 1},
        "BTU": {"BTU": 1},
        "C": {"K": 1},
        "USD": {"USD": 1},
        "ton": {"ton": 1},
        "V": {"V": 1},
        "A": {"A": 1},
        "Ah": {"A": 1, "s": 1},
        "ohm": {"V": 1, "A": -1},
    }
    if unit not in mapping:
        raise ValueError(f"Unsupported unit token: {token}")
    return dict(mapping[unit])


def _add_unit_dimensions(left, right):
    combined = dict(left)
    for name, exponent in right.items():
        combined[name] = combined.get(name, 0) + exponent
        if math.isclose(combined[name], 0.0, abs_tol=1e-12):
            combined.pop(name, None)
    return combined


def _scale_unit_dimensions(dims, scale):
    return {name: exponent * scale for name, exponent in dims.items()}


def _canonical_unit_from_dimensions(dims):
    dims = {name: exponent for name, exponent in dims.items() if not math.isclose(exponent, 0.0, abs_tol=1e-12)}
    known = {
        (): "dimensionless",
        (("m", 1),): "m",
        (("m", 2),): "m^2",
        (("kg", 1), ("m", 1), ("s", -2)): "N",
        (("kg", 1), ("m", -1), ("s", -2)): "Pa",
        (("kg", 1), ("m", 2), ("s", -2)): "J",
        (("kg", 1), ("m", 2), ("s", -3)): "W",
        (("kg", 1), ("m", 2), ("s", -2), ("year", -1)): "kWh/year",
        (("K", -1), ("kg", -1), ("m", 2), ("s", -2)): "J/kg/K",
        (("J", 1),): "J",
        (("J", 1), ("s", -1)): "W",
        (("J", 1), ("year", -1)): "kWh/year",
        (("BTU", 1),): "BTU",
        (("BTU", 1), ("s", -1)): "BTU/hr",
        (("BTU", 1), ("F", -1), ("s", -1)): "BTU/hr/F",
        (("BTU", 1), ("F", -1), ("lb", -1)): "BTU/lb/F",
        (("BTU", 1), ("F", -1), ("gal", -1)): "BTU/hr/gpm/F",
        (("K", 1),): "delta_C",
        (("F", 1),): "F",
        (("USD", 1), ("year", -1)): "USD/year",
        (("USD", 1), ("s", 1), ("scf", -1), ("year", -1)): "USD/scfm/year",
        (("kg", 1), ("s", -1)): "kg/s",
        (("m", 3), ("s", -1)): "m^3/s",
        (("kg", 1), ("m", -3)): "kg/m^3",
        (("J", 1), ("K", -1), ("kg", -1)): "J/kg/K",
        (("kg", 1), ("K", -1)): "kg/C",
        (("cycle", 1), ("s", -1)): "cycle/min",
        (("cycle", -1), ("scf", 1)): "scf/cycle",
        (("scf", 1),): "scf",
        (("s", -1), ("scf", 1)): "scfm",
        (("in", 1),): "in",
        (("in", 1), ("s", -1)): "in/min",
        (("in", 2),): "in^2",
        (("in", 3),): "in^3",
        (("in", 3), ("s", -1)): "in^3/min",
        (("in", 4),): "in^4",
        (("in", -1), ("lbf", 1)): "lbf/in",
        (("in", -2), ("lbf", 1)): "psi",
        (("lbf", 1), ("m", -2)): "psf",
        (("pressure_inH2O", 1),): "inH2O",
        (("in", 1), ("lbf", 1)): "lbf_in",
        (("in", 2), ("lbf", 1)): "lbf_in*in",
        (("in", 3), ("lbf", 1)): "lbf_in*in^2",
        (("lbf", 1), ("m", 1)): "lbf*ft",
        (("lbf", 1),): "lbf",
        (("N", 1),): "N",
        (("N", 1), ("m", 1)): "N*m",
        (("gal", -1), ("lb", 1)): "lb/gal",
        (("gal", 1), ("s", -1)): "gpm",
        (("lb", 1), ("s", -1)): "lb/min",
        (("hp", 1),): "hp",
        (("s", 1), ("year", -1)): "h/year",
        (("ton", 1),): "ton",
        (("V", 1),): "V",
        (("A", 1),): "A",
        (("A", 1), ("s", 1)): "Ah",
        (("A", -1), ("V", 1)): "ohm",
        (("A", -1), ("V", 1), ("m", -1)): "ohm/ft",
    }
    key = tuple(sorted((name, _canonical_exponent(exponent)) for name, exponent in dims.items()))
    if key in known:
        return known[key]
    return _format_unit_dimensions(dims)


def _canonical_exponent(exponent):
    if math.isclose(exponent, round(exponent), abs_tol=1e-12):
        return int(round(exponent))
    return exponent


def _format_unit_dimensions(dims):
    if not dims:
        return "dimensionless"
    numerator = []
    denominator = []
    for name, exponent in sorted(dims.items()):
        exponent = _canonical_exponent(exponent)
        target = numerator if exponent > 0 else denominator
        abs_exponent = abs(exponent)
        target.append(name if abs_exponent == 1 else f"{name}^{abs_exponent}")
    result = "*".join(numerator) if numerator else "1"
    if denominator:
        denominator_text = "*".join(denominator)
        result += "/" + (f"({denominator_text})" if len(denominator) > 1 else denominator_text)
    return result


def _first_unknown_unit(*items):
    for item in items:
        if item.get("status") == "unknown":
            return item
    return None


def _unit_result(unit, status, severity, message):
    return {
        "unit": _normalize_inferred_unit(unit) if unit is not None else None,
        "status": status,
        "severity": severity,
        "message": message,
    }


def _normalize_inferred_unit(unit):
    text = str(unit or "").strip()
    lowered = re.sub(r"[\s_]+", "_", text.lower()).strip("_")
    if lowered in {"string", "str", "text"}:
        return "string"
    if lowered in {"label", "name", "label_string"}:
        return "label_string"
    return normalize_unit(unit)


def _normalize_inferred_element_unit(unit):
    return _canonical_text_unit(unit) if _is_textual_unit(unit) else normalize_unit(unit)


def _current_variable_units(variable_meta):
    units = {}
    for name, meta in variable_meta.items():
        suffix_unit = _unit_from_name_suffix(name)
        unit = meta.get("unit") or suffix_unit
        if (
            suffix_unit
            and not meta.get("unit_declared")
            and not meta.get("unit_inferred_from_context")
            and normalize_unit(unit) == "dimensionless"
        ):
            unit = suffix_unit
        if meta.get("unit_declared") or meta.get("unit_inferred_from_name") or meta.get("source") != "unknown":
            units[name] = unit
    return units


def _should_assign_inferred_unit(name, meta, inferred_unit):
    inferred_unit = _normalize_inferred_unit(inferred_unit)
    if not inferred_unit:
        return False
    if _is_list_unit(inferred_unit):
        return True
    if inferred_unit == "boolean":
        return True
    if _is_textual_unit(inferred_unit) and _is_status_text_unit(_unit_from_name_suffix(name)):
        return False
    return not meta.get("unit_declared")


def _is_numeric_literal(node, expected_value):
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and math.isclose(float(node.value), float(expected_value), rel_tol=0.0, abs_tol=1e-12)
    )


def _is_name(node, expected_name):
    return isinstance(node, ast.Name) and node.id == expected_name


FORMULA_HANDLER_METADATA = {
    "thermal_energy_cooldown": {
        "required_inputs": {
            "mass_kg",
            "specific_heat_kJ_per_kg_C",
            "initial_temperature_C",
            "target_temperature_C",
        },
        "optional_inputs": {
            "safety_factor",
            "safety_margin_factor",
            "cooling_power_kW",
            "cooldown_requirement_hours",
        },
        "forbidden_or_conflicting_signals": {
            "v_dot",
            "volumetric_flow",
            "mass_flow",
            "m_dot",
            "rho",
            "density",
            "pump_heat",
            "chiller_capacity",
            "refrigeration_ton",
            "cop",
            "annual_energy",
            "m_dot * cp * delta_t",
            "m_dot*cp*delta_t",
        },
        "minimum_confidence_score": 1.0,
    },
    "power_energy_time": {
        "required_inputs_any": ({"energy_kWh", "Q_margin_kWh", "Q_kWh"}, {"power_kW", "cooling_power_kW"}),
    },
    "requirement_check": {
        "required_inputs": {"value", "limit"},
    },
    "ohms_law": {
        "required_count_from": {"voltage_V", "current_A", "resistance_ohm"},
        "required_count": 2,
    },
    "factor_of_safety": {
        "required_inputs": {"capacity", "demand"},
    },
}


def _formula_handler_missing_inputs(operation, inputs):
    metadata = FORMULA_HANDLER_METADATA.get(operation, {})
    if "required_inputs" in metadata:
        return _missing_inputs(inputs, sorted(metadata["required_inputs"]))
    if "required_inputs_any" in metadata:
        missing_groups = []
        for group in metadata["required_inputs_any"]:
            if not any(name in inputs and not is_missing_value(inputs.get(name)) for name in group):
                missing_groups.append("one of " + "/".join(sorted(group)))
        return missing_groups
    if "required_count_from" in metadata:
        present = [
            name for name in metadata["required_count_from"]
            if name in inputs and not is_missing_value(inputs.get(name))
        ]
        required_count = metadata.get("required_count", 1)
        if len(present) != required_count:
            return [f"exactly {required_count} of " + ", ".join(sorted(metadata["required_count_from"]))]
    return []


def _formula_handler_conflict(operation, mcm_request):
    metadata = FORMULA_HANDLER_METADATA.get(operation, {})
    forbidden = metadata.get("forbidden_or_conflicting_signals")
    if not forbidden:
        return []
    text = _routing_signal_text(mcm_request)
    return sorted(signal for signal in forbidden if signal in text)


def _routing_signal_text(mcm_request):
    parts = []
    for field in ("operation", "formula", "task_type", "problem_type", "objective", "requested_output"):
        value = mcm_request.get(field)
        if isinstance(value, str):
            parts.append(value)
    variables = mcm_request.get("variables")
    if isinstance(variables, dict):
        parts.extend(str(name) for name in variables)
    equations = mcm_request.get("equations")
    if isinstance(equations, list):
        parts.extend(_equation_expression(equation) or "" for equation in equations)
    constraints = mcm_request.get("constraints")
    if isinstance(constraints, list):
        parts.extend(str(constraint) for constraint in constraints)
    return " ".join(parts).lower()


def _equation_plan_router_diagnostics(mcm_request, inputs):
    if not _debug_diagnostics_enabled(mcm_request):
        return []
    operation = _canonical_formula_operation(mcm_request)
    if not operation:
        return ["Explicit equation plan detected; routing directly to dependency-ordered equation execution."]
    missing = _formula_handler_missing_inputs(operation, inputs)
    conflict = _formula_handler_conflict(operation, mcm_request)
    if missing:
        return [
            f"Known handler {operation} was rejected because required inputs were missing: "
            + ", ".join(missing)
            + "; falling back to explicit equation execution."
        ]
    if conflict:
        return [
            f"Known handler {operation} was rejected because conflicting problem signals were detected: "
            + ", ".join(conflict)
            + "; falling back to explicit equation execution."
        ]
    return [
        f"Known handler {operation} was bypassed because an explicit equation/variable/solve_for plan was provided."
    ]


def _debug_diagnostics_enabled(mcm_request):
    if not isinstance(mcm_request, dict):
        return False
    for key in ("debug", "debug_mode", "include_debug_diagnostics", "verbose_diagnostics"):
        value = mcm_request.get(key)
        if value is True:
            return True
        if isinstance(value, str) and value.strip().lower() in {"1", "true", "yes", "on"}:
            return True
    return False


def _process_formula_handler(mcm_request, inputs, explicit_equations_available=False):
    operation = _canonical_formula_operation(mcm_request)
    if not operation:
        return None

    handler = FORMULA_HANDLERS.get(operation)
    if not handler:
        return None

    missing = _formula_handler_missing_inputs(operation, inputs)
    conflict = _formula_handler_conflict(operation, mcm_request)
    if explicit_equations_available and (missing or conflict):
        return None
    if missing:
        return _formula_missing_result(mcm_request, operation, missing)
    if conflict:
        result = _formula_missing_result(mcm_request, operation, ["conflicting problem signals"])
        result["diagnostics"].append(
            f"Known formula handler '{operation}' was rejected because conflicting signals were detected: "
            + ", ".join(conflict)
        )
        return result

    return handler(mcm_request, inputs)


def _canonical_formula_operation(mcm_request):
    for field in ("operation", "formula", "task_type", "problem_type"):
        value = mcm_request.get(field)
        if isinstance(value, str) and value.strip():
            normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
            canonical = FORMULA_ALIASES.get(normalized)
            if canonical:
                return canonical
    return None


def handle_thermal_energy_cooldown(mcm_request, inputs):
    required = [
        "mass_kg",
        "specific_heat_kJ_per_kg_C",
        "initial_temperature_C",
        "target_temperature_C",
    ]
    missing = _missing_inputs(inputs, required)
    if missing:
        return _formula_missing_result(mcm_request, "thermal_energy_cooldown", missing)

    mass = inputs["mass_kg"]
    specific_heat = inputs["specific_heat_kJ_per_kg_C"]
    initial_temperature = inputs["initial_temperature_C"]
    target_temperature = inputs["target_temperature_C"]
    safety_factor = None

    delta_t = initial_temperature - target_temperature
    q_kj = mass * specific_heat * delta_t
    q_kwh = q_kj / 3600

    outputs = {}
    steps = []
    unit_validation = []
    inputs_used = {
        "mass_kg": mass,
        "specific_heat_kJ_per_kg_C": specific_heat,
        "initial_temperature_C": initial_temperature,
        "target_temperature_C": target_temperature,
    }

    _add_formula_output(outputs, steps, unit_validation, "delta_T_C", delta_t, "C", "delta_T_C", "initial_temperature_C - target_temperature_C", "Temperature drop.")
    _add_formula_output(outputs, steps, unit_validation, "Q_kJ", q_kj, "kJ", "Q_kJ", "mass_kg * specific_heat_kJ_per_kg_C * delta_T_C", "Thermal energy removed.")
    _add_formula_output(outputs, steps, unit_validation, "Q_kWh", q_kwh, "kWh", "Q_kWh", "Q_kJ / 3600", "Thermal energy converted to kWh.")

    energy_for_time = q_kwh
    if "safety_factor" in inputs:
        safety_factor = inputs["safety_factor"]
        q_margin_kwh = q_kwh * safety_factor
        inputs_used["safety_factor"] = safety_factor
        energy_for_time = q_margin_kwh
        _add_formula_output(outputs, steps, unit_validation, "Q_margin_kWh", q_margin_kwh, "kWh", "Q_margin_kWh", "Q_kWh * safety_factor", "Safety-factored thermal energy.")
    elif "safety_margin_factor" in inputs:
        safety_factor = inputs["safety_margin_factor"]
        q_margin_kwh = q_kwh * safety_factor
        inputs_used["safety_margin_factor"] = safety_factor
        energy_for_time = q_margin_kwh
        _add_formula_output(outputs, steps, unit_validation, "Q_margin_kWh", q_margin_kwh, "kWh", "Q_margin_kWh", "Q_kWh * safety_margin_factor", "Safety-factored thermal energy.")

    cooling_power = _first_present_input(inputs, ("cooling_power_kW", "power_kW"))
    requirement = _first_present_input(inputs, ("cooldown_requirement_hours", "required_max_cooling_time_hours", "max_allowed_cooling_time_hours", "requirement_time_hours"))

    if cooling_power:
        power_name, power_value = cooling_power
        cooling_time = energy_for_time / power_value
        inputs_used[power_name] = power_value
        _add_formula_output(outputs, steps, unit_validation, "cooling_time_hours", cooling_time, "h", "cooling_time_hours", "Q_margin_kWh / cooling_power_kW", "Cooling time from available cooling power.")

        if requirement:
            requirement_name, requirement_value = requirement
            inputs_used[requirement_name] = requirement_value
            meets_requirement = cooling_time <= requirement_value
            _add_formula_output(outputs, steps, unit_validation, "meets_requirement", meets_requirement, "boolean", "meets_requirement", "cooling_time_hours <= cooldown_requirement_hours", "Cooling-time requirement check.")

    if requirement:
        requirement_name, requirement_value = requirement
        inputs_used[requirement_name] = requirement_value
        required_power = energy_for_time / requirement_value
        _add_formula_output(outputs, steps, unit_validation, "required_cooling_power_kW", required_power, "kW", "required_cooling_power_kW", "Q_margin_kWh / cooldown_requirement_hours", "Required average cooling power.")

        if cooling_power:
            power_name, power_value = cooling_power
            power_margin = power_value - required_power
            power_margin_percent = (power_margin / required_power) * 100 if required_power != 0 else None
            _add_formula_output(outputs, steps, unit_validation, "power_margin_kW", power_margin, "kW", "power_margin_kW", "cooling_power_kW - required_cooling_power_kW", "Cooling-power margin.")
            if power_margin_percent is not None:
                _add_formula_output(outputs, steps, unit_validation, "power_margin_percent", power_margin_percent, "dimensionless", "power_margin_percent", "power_margin_kW / required_cooling_power_kW * 100", "Cooling-power margin percentage.")

    if _thermal_sensitivity_requested(mcm_request, inputs):
        sensitivity_missing = _missing_thermal_sensitivity_inputs(inputs, safety_factor, cooling_power, requirement)
        if sensitivity_missing:
            return _formula_missing_result(mcm_request, "thermal_energy_cooldown", sensitivity_missing)
        _add_thermal_sensitivity_outputs(
            outputs,
            steps,
            unit_validation,
            inputs,
            mass,
            specific_heat,
            delta_t,
            q_kwh,
            q_margin_kwh,
            energy_for_time,
            cooling_power[1],
            requirement[1],
            safety_factor,
            cooling_time,
            meets_requirement,
        )

    diagnostics = [
        "Executed known formula handler: thermal_energy_cooldown.",
        "Technician shortcut formulas are not used as valid cooling-power estimates by this handler.",
    ]
    return _formula_result(mcm_request, "thermal_energy_cooldown", outputs, steps, unit_validation, diagnostics, inputs_used)


def _thermal_sensitivity_requested(mcm_request, inputs):
    variation_inputs = {
        "mass_variation_fraction",
        "cooling_power_variation_fraction",
        "safety_factor_variation_absolute",
    }
    if variation_inputs.intersection(inputs):
        return True

    solve_for = mcm_request.get("solve_for")
    sensitivity_outputs = {
        "mass_low_kg",
        "cooling_time_mass_low_hours",
        "cooling_time_cooling_power_low_hours",
        "cooling_time_safety_factor_low_hours",
        "largest_effect_variable",
        "any_sensitivity_case_changes_pass_fail",
    }
    if isinstance(solve_for, list) and sensitivity_outputs.intersection(str(item) for item in solve_for):
        return True

    for field in ("sensitivity", "sensitivity_analysis"):
        value = mcm_request.get(field)
        if isinstance(value, dict) and value.get("enabled") is True:
            return True

    constraints = mcm_request.get("constraints")
    if isinstance(constraints, list):
        return any("sensitivity" in str(item).lower() for item in constraints)

    return False


def _missing_thermal_sensitivity_inputs(inputs, safety_factor, cooling_power, requirement):
    missing = []
    required = [
        "mass_variation_fraction",
        "cooling_power_variation_fraction",
        "safety_factor_variation_absolute",
    ]
    missing.extend(_missing_inputs(inputs, required))
    if safety_factor is None:
        missing.append("safety_factor")
    if not cooling_power:
        missing.append("cooling_power_kW")
    if not requirement:
        missing.append("cooldown_requirement_hours")
    return missing


def _add_thermal_sensitivity_outputs(
    outputs,
    steps,
    unit_validation,
    inputs,
    mass,
    specific_heat,
    delta_t,
    q_kwh,
    q_margin_kwh,
    energy_for_time,
    cooling_power,
    requirement,
    safety_factor,
    baseline_cooling_time,
    baseline_meets_requirement,
):
    mass_fraction = inputs["mass_variation_fraction"]
    cooling_power_fraction = inputs["cooling_power_variation_fraction"]
    safety_factor_absolute = inputs["safety_factor_variation_absolute"]

    mass_low = mass * (1 - mass_fraction)
    mass_high = mass * (1 + mass_fraction)
    cooling_power_low = cooling_power * (1 - cooling_power_fraction)
    cooling_power_high = cooling_power * (1 + cooling_power_fraction)
    safety_factor_low = safety_factor - safety_factor_absolute
    safety_factor_high = safety_factor + safety_factor_absolute

    effects = {}
    pass_fail_changes = []

    _add_formula_output(outputs, steps, unit_validation, "mass_low_kg", mass_low, "kg", "mass_low_kg", "mass_kg * (1 - mass_variation_fraction)", "Low mass sensitivity bound.")
    _add_formula_output(outputs, steps, unit_validation, "mass_high_kg", mass_high, "kg", "mass_high_kg", "mass_kg * (1 + mass_variation_fraction)", "High mass sensitivity bound.")

    for suffix, case_mass in (("mass_low", mass_low), ("mass_high", mass_high)):
        q_case_kj = case_mass * specific_heat * delta_t
        q_case_kwh = q_case_kj / 3600
        q_margin_case = q_case_kwh * safety_factor
        cooling_time_case = q_margin_case / cooling_power
        meets_case = cooling_time_case <= requirement
        _add_formula_output(outputs, steps, unit_validation, f"Q_margin_{suffix}_kWh", q_margin_case, "kWh", f"Q_margin_{suffix}_kWh", f"Q_{suffix}_kWh * safety_factor", f"Safety-factored thermal energy for {suffix}.")
        _add_formula_output(outputs, steps, unit_validation, f"cooling_time_{suffix}_hours", cooling_time_case, "h", f"cooling_time_{suffix}_hours", f"Q_margin_{suffix}_kWh / cooling_power_kW", f"Cooling time for {suffix}.")
        _add_formula_output(outputs, steps, unit_validation, f"meets_requirement_{suffix}", meets_case, "boolean", f"meets_requirement_{suffix}", f"cooling_time_{suffix}_hours <= cooldown_requirement_hours", f"Requirement result for {suffix}.")
        effect_name = f"cooling_time_effect_{suffix}_hours"
        effects[suffix] = cooling_time_case - baseline_cooling_time
        _add_formula_output(outputs, steps, unit_validation, effect_name, effects[suffix], "h", effect_name, f"cooling_time_{suffix}_hours - cooling_time_hours", f"Cooldown-time effect for {suffix}.")
        if meets_case != baseline_meets_requirement:
            pass_fail_changes.append(suffix)

    _add_formula_output(outputs, steps, unit_validation, "cooling_power_low_kW", cooling_power_low, "kW", "cooling_power_low_kW", "cooling_power_kW * (1 - cooling_power_variation_fraction)", "Low cooling-power sensitivity bound.")
    _add_formula_output(outputs, steps, unit_validation, "cooling_power_high_kW", cooling_power_high, "kW", "cooling_power_high_kW", "cooling_power_kW * (1 + cooling_power_variation_fraction)", "High cooling-power sensitivity bound.")

    for suffix, case_power in (("cooling_power_low", cooling_power_low), ("cooling_power_high", cooling_power_high)):
        q_margin_case = q_margin_kwh
        cooling_time_case = q_margin_case / case_power
        meets_case = cooling_time_case <= requirement
        _add_formula_output(outputs, steps, unit_validation, f"Q_margin_{suffix}_kWh", q_margin_case, "kWh", f"Q_margin_{suffix}_kWh", "baseline Q_margin_kWh", f"Safety-factored thermal energy for {suffix}.")
        _add_formula_output(outputs, steps, unit_validation, f"cooling_time_{suffix}_hours", cooling_time_case, "h", f"cooling_time_{suffix}_hours", f"Q_margin_{suffix}_kWh / {suffix}_kW", f"Cooling time for {suffix}.")
        _add_formula_output(outputs, steps, unit_validation, f"meets_requirement_{suffix}", meets_case, "boolean", f"meets_requirement_{suffix}", f"cooling_time_{suffix}_hours <= cooldown_requirement_hours", f"Requirement result for {suffix}.")
        effect_name = f"cooling_time_effect_{suffix}_hours"
        effects[suffix] = cooling_time_case - baseline_cooling_time
        _add_formula_output(outputs, steps, unit_validation, effect_name, effects[suffix], "h", effect_name, f"cooling_time_{suffix}_hours - cooling_time_hours", f"Cooldown-time effect for {suffix}.")
        if meets_case != baseline_meets_requirement:
            pass_fail_changes.append(suffix)

    _add_formula_output(outputs, steps, unit_validation, "safety_factor_low", safety_factor_low, "dimensionless", "safety_factor_low", "safety_factor - safety_factor_variation_absolute", "Low safety-factor sensitivity bound.")
    _add_formula_output(outputs, steps, unit_validation, "safety_factor_high", safety_factor_high, "dimensionless", "safety_factor_high", "safety_factor + safety_factor_variation_absolute", "High safety-factor sensitivity bound.")

    for suffix, case_factor in (("safety_factor_low", safety_factor_low), ("safety_factor_high", safety_factor_high)):
        q_margin_case = q_kwh * case_factor
        cooling_time_case = q_margin_case / cooling_power
        meets_case = cooling_time_case <= requirement
        _add_formula_output(outputs, steps, unit_validation, f"Q_margin_{suffix}_kWh", q_margin_case, "kWh", f"Q_margin_{suffix}_kWh", f"Q_kWh * {suffix}", f"Safety-factored thermal energy for {suffix}.")
        _add_formula_output(outputs, steps, unit_validation, f"cooling_time_{suffix}_hours", cooling_time_case, "h", f"cooling_time_{suffix}_hours", f"Q_margin_{suffix}_kWh / cooling_power_kW", f"Cooling time for {suffix}.")
        _add_formula_output(outputs, steps, unit_validation, f"meets_requirement_{suffix}", meets_case, "boolean", f"meets_requirement_{suffix}", f"cooling_time_{suffix}_hours <= cooldown_requirement_hours", f"Requirement result for {suffix}.")
        effect_name = f"cooling_time_effect_{suffix}_hours"
        effects[suffix] = cooling_time_case - baseline_cooling_time
        _add_formula_output(outputs, steps, unit_validation, effect_name, effects[suffix], "h", effect_name, f"cooling_time_{suffix}_hours - cooling_time_hours", f"Cooldown-time effect for {suffix}.")
        if meets_case != baseline_meets_requirement:
            pass_fail_changes.append(suffix)

    largest_effect_variable = max(effects, key=lambda key: abs(effects[key]))
    _add_formula_output(outputs, steps, unit_validation, "largest_effect_variable", largest_effect_variable, "case_identifier", "largest_effect_variable", "max absolute cooldown-time sensitivity effect", "Sensitivity case with the largest absolute cooldown-time effect.")
    _add_formula_output(outputs, steps, unit_validation, "any_sensitivity_case_changes_pass_fail", bool(pass_fail_changes), "boolean", "any_sensitivity_case_changes_pass_fail", "any sensitivity case differs from baseline meets_requirement", "Whether any sensitivity case changes the pass/fail result.")


def handle_power_energy_time(mcm_request, inputs):
    energy = _first_present_input(inputs, ("energy_kWh", "Q_margin_kWh", "Q_kWh"))
    power = _first_present_input(inputs, ("power_kW", "cooling_power_kW"))
    missing = []
    if not energy:
        missing.append("energy_kWh or Q_margin_kWh or Q_kWh")
    if not power:
        missing.append("power_kW or cooling_power_kW")
    if missing:
        return _formula_missing_result(mcm_request, "power_energy_time", missing)

    energy_name, energy_value = energy
    power_name, power_value = power
    time_hours = energy_value / power_value
    outputs = {}
    steps = []
    unit_validation = []
    _add_formula_output(outputs, steps, unit_validation, "time_hours", time_hours, "h", "time_hours", f"{energy_name} / {power_name}", "Time from energy and power.")
    return _formula_result(
        mcm_request,
        "power_energy_time",
        outputs,
        steps,
        unit_validation,
        ["Executed known formula handler: power_energy_time."],
        {energy_name: energy_value, power_name: power_value},
    )


def handle_requirement_check(mcm_request, inputs):
    comparator = str(mcm_request.get("comparator") or inputs.get("comparator") or "").strip()
    if comparator not in ALLOWED_COMPARATOR_SYMBOLS:
        return _formula_missing_result(mcm_request, "requirement_check", ["comparator"])

    value = _first_present_input(inputs, ("value", "actual", "measured_value"))
    limit = _first_present_input(inputs, ("limit", "requirement", "threshold", "max_allowed", "min_allowed"))
    missing = []
    if not value:
        missing.append("value")
    if not limit:
        missing.append("limit")
    if missing:
        return _formula_missing_result(mcm_request, "requirement_check", missing)

    value_name, value_value = value
    limit_name, limit_value = limit
    passes = ALLOWED_COMPAREOPS[ALLOWED_COMPARATOR_SYMBOLS[comparator]](value_value, limit_value)
    margin = limit_value - value_value if comparator in {"<=", "<", "==", "!="} else value_value - limit_value
    margin_percent = (margin / abs(limit_value)) * 100 if limit_value != 0 else None

    outputs = {}
    steps = []
    unit_validation = []
    _add_formula_output(outputs, steps, unit_validation, "passes", passes, "boolean", "passes", f"{value_name} {comparator} {limit_name}", "Requirement comparison.")
    _add_formula_output(outputs, steps, unit_validation, "margin", margin, None, "margin", "limit - value or value - limit", "Requirement margin.")
    if margin_percent is not None:
        _add_formula_output(outputs, steps, unit_validation, "margin_percent", margin_percent, "dimensionless", "margin_percent", "margin / limit * 100", "Requirement margin percentage.")
    return _formula_result(
        mcm_request,
        "requirement_check",
        outputs,
        steps,
        unit_validation,
        ["Executed known formula handler: requirement_check."],
        {value_name: value_value, limit_name: limit_value},
    )


def handle_ohms_law(mcm_request, inputs):
    present = {name: inputs[name] for name in ("voltage_V", "current_A", "resistance_ohm") if name in inputs}
    missing = [name for name in ("voltage_V", "current_A", "resistance_ohm") if name not in present]
    if len(missing) != 1 or len(present) != 2:
        return _formula_missing_result(mcm_request, "ohms_law", ["exactly two of voltage_V, current_A, resistance_ohm"])

    outputs = {}
    steps = []
    unit_validation = []
    if "voltage_V" in missing:
        value = present["current_A"] * present["resistance_ohm"]
        _add_formula_output(outputs, steps, unit_validation, "voltage_V", value, "V", "voltage_V", "current_A * resistance_ohm", "Ohm's law voltage.")
    elif "current_A" in missing:
        value = present["voltage_V"] / present["resistance_ohm"]
        _add_formula_output(outputs, steps, unit_validation, "current_A", value, "A", "current_A", "voltage_V / resistance_ohm", "Ohm's law current.")
    else:
        value = present["voltage_V"] / present["current_A"]
        _add_formula_output(outputs, steps, unit_validation, "resistance_ohm", value, "ohm", "resistance_ohm", "voltage_V / current_A", "Ohm's law resistance.")

    return _formula_result(mcm_request, "ohms_law", outputs, steps, unit_validation, ["Executed known formula handler: ohms_law."], present)


def handle_electrical_power(mcm_request, inputs):
    outputs = {}
    steps = []
    unit_validation = []

    if "power_W" not in inputs:
        if "voltage_V" in inputs and "current_A" in inputs:
            _add_formula_output(outputs, steps, unit_validation, "power_W", inputs["voltage_V"] * inputs["current_A"], "W", "power_W", "voltage_V * current_A", "Electrical power.")
        elif "current_A" in inputs and "resistance_ohm" in inputs:
            _add_formula_output(outputs, steps, unit_validation, "power_W", inputs["current_A"] ** 2 * inputs["resistance_ohm"], "W", "power_W", "current_A ** 2 * resistance_ohm", "Electrical power.")
        elif "voltage_V" in inputs and "resistance_ohm" in inputs:
            _add_formula_output(outputs, steps, unit_validation, "power_W", inputs["voltage_V"] ** 2 / inputs["resistance_ohm"], "W", "power_W", "voltage_V ** 2 / resistance_ohm", "Electrical power.")
    if "current_A" not in inputs and "power_W" in inputs and "voltage_V" in inputs:
        _add_formula_output(outputs, steps, unit_validation, "current_A", inputs["power_W"] / inputs["voltage_V"], "A", "current_A", "power_W / voltage_V", "Current from power and voltage.")
    if "voltage_V" not in inputs and "power_W" in inputs and "current_A" in inputs:
        _add_formula_output(outputs, steps, unit_validation, "voltage_V", inputs["power_W"] / inputs["current_A"], "V", "voltage_V", "power_W / current_A", "Voltage from power and current.")

    if not outputs:
        return _formula_missing_result(mcm_request, "electrical_power", ["a supported pair among power_W, voltage_V, current_A, resistance_ohm"])

    used = {name: inputs[name] for name in ("power_W", "voltage_V", "current_A", "resistance_ohm") if name in inputs}
    return _formula_result(mcm_request, "electrical_power", outputs, steps, unit_validation, ["Executed known formula handler: electrical_power."], used)


def handle_factor_of_safety(mcm_request, inputs):
    missing = _missing_inputs(inputs, ["capacity", "demand"])
    if missing:
        return _formula_missing_result(mcm_request, "factor_of_safety", missing)

    fos = inputs["capacity"] / inputs["demand"]
    outputs = {}
    steps = []
    unit_validation = []
    _add_formula_output(outputs, steps, unit_validation, "factor_of_safety", fos, "dimensionless", "factor_of_safety", "capacity / demand", "Factor of safety.")

    inputs_used = {"capacity": inputs["capacity"], "demand": inputs["demand"]}
    if "required_factor_of_safety" in inputs:
        passes = fos >= inputs["required_factor_of_safety"]
        inputs_used["required_factor_of_safety"] = inputs["required_factor_of_safety"]
        _add_formula_output(outputs, steps, unit_validation, "passes", passes, "boolean", "passes", "factor_of_safety >= required_factor_of_safety", "Factor-of-safety requirement check.")

    return _formula_result(mcm_request, "factor_of_safety", outputs, steps, unit_validation, ["Executed known formula handler: factor_of_safety."], inputs_used)


def _formula_result(mcm_request, operation, outputs, steps, unit_validation, diagnostics, inputs_used):
    result = _base_result(
        mcm_request,
        status="computed",
        message=f"MCM completed known formula handler: {operation}.",
        outputs=outputs,
        diagnostics=diagnostics,
        inputs_used=inputs_used,
    )
    result["operation"] = operation
    result["calculations"] = steps
    result["calculation_steps"] = steps
    result["unit_validation"] = unit_validation
    result["unit_warnings"] = []
    result["assumptions"] = mcm_request.get("assumptions", []) if isinstance(mcm_request, dict) else []
    result["missing_variables"] = []
    result["missing_outputs"] = []
    result["equations_skipped"] = []
    return result


def _formula_missing_result(mcm_request, operation, missing):
    result = _base_result(
        mcm_request,
        status="needs_human_review",
        message=f"Known formula handler '{operation}' is missing required inputs.",
        outputs={},
        diagnostics=["Missing required inputs: " + ", ".join(str(item) for item in missing)],
        inputs_used={},
    )
    result["operation"] = operation
    result["calculations"] = []
    result["calculation_steps"] = []
    result["unit_validation"] = []
    result["unit_warnings"] = []
    result["missing_variables"] = [str(item) for item in missing]
    result["missing_outputs"] = []
    result["equations_skipped"] = []
    return result


def _add_formula_output(outputs, steps, unit_validation, name, value, unit, equation, expression, purpose):
    unit = normalize_unit(unit) if unit is not None else unit
    output = {
        "value": value,
        "unit": unit,
        "source": "computed",
        "equation": equation,
        "description": purpose,
    }
    outputs[name] = output
    step = {
        "equation": equation,
        "expression": expression,
        "lhs": name,
        "result": value,
        "purpose": purpose,
    }
    unit_check = {
        "equation_name": equation,
        "expression": expression,
        "lhs": name,
        "lhs_expected_unit": unit,
        "rhs_inferred_unit": unit,
        "status": "valid",
        "severity": "info",
        "message": f"Known formula handler assigned output unit {unit}.",
    }
    step["unit_validation"] = unit_check
    outputs[name]["unit_validation"] = unit_check
    steps.append(step)
    unit_validation.append(unit_check)


def _missing_inputs(inputs, names):
    return [name for name in names if name not in inputs]


def _first_present_input(inputs, names):
    for name in names:
        if name in inputs:
            return name, inputs[name]
    return None


FORMULA_HANDLERS = {
    "thermal_energy_cooldown": handle_thermal_energy_cooldown,
    "power_energy_time": handle_power_energy_time,
    "requirement_check": handle_requirement_check,
    "ohms_law": handle_ohms_law,
    "electrical_power": handle_electrical_power,
    "factor_of_safety": handle_factor_of_safety,
}


def _build_output(name, value, variable_meta, equation_for):
    meta = variable_meta.get(name, {})
    source = "computed" if name in equation_for else meta.get("source", "input")
    if meta.get("source") == "not_computed_missing_inputs":
        source = "not_computed_missing_inputs"
    suffix_unit = _unit_from_name_suffix(name)
    output_unit = meta.get("unit") or suffix_unit
    if suffix_unit and not meta.get("unit_declared") and normalize_unit(output_unit) == "dimensionless":
        output_unit = suffix_unit
    output = {
        "value": value,
        "unit": output_unit,
        "source": source,
        "equation": equation_for.get(name),
    }
    if meta.get("description"):
        output["description"] = meta.get("description")
    if meta.get("status"):
        output["status"] = meta.get("status")
    if meta.get("result_status"):
        output["result_status"] = meta.get("result_status")
    if meta.get("missing_inputs"):
        output["missing_inputs"] = meta.get("missing_inputs")
    if meta.get("unit_validation"):
        output["unit_validation"] = meta.get("unit_validation")
    return output


def _equation_name(equation, index):
    if isinstance(equation, dict) and equation.get("name"):
        return str(equation.get("name"))
    return f"equation_{index}"


def _equation_expression(equation):
    if isinstance(equation, dict):
        expression = equation.get("expression")
    else:
        expression = equation
    if isinstance(expression, str) and expression.strip():
        return expression.strip()
    return None


def _equation_purpose(equation):
    if isinstance(equation, dict) and equation.get("purpose"):
        return str(equation.get("purpose"))
    return ""


def _normalize_equation_assignment(equation, expression):
    expression = expression.strip() if isinstance(expression, str) else ""
    if not expression:
        return None, None, "Equation has no expression."

    if _split_assignment(expression):
        return expression, None, None

    if _contains_bare_assignment_operator(expression):
        return expression, None, (
            "Equation contains a malformed assignment; only equations of the form "
            "'<single_variable> = <safe_expression>' are supported."
        )

    rhs_error = _safe_rhs_expression_error(expression)
    if rhs_error:
        return expression, None, f"RHS-only equation could not be normalized: expression is not a safe RHS expression ({rhs_error})."

    lhs_source, lhs, lhs_error = _equation_lhs_candidate(equation)
    if not lhs:
        return expression, None, lhs_error

    normalized = f"{lhs} = {expression}"
    diagnostic = f"Normalized RHS-only equation to assignment using equation.{lhs_source} as lhs: {lhs}"
    return normalized, diagnostic, None


def _contains_bare_assignment_operator(expression):
    return bool(re.search(r"(?<![<>=!])=(?!=)", expression))


def _equation_lhs_candidate(equation):
    if not isinstance(equation, dict):
        return None, None, "RHS-only equation could not be normalized: no equation object field can provide a lhs."

    errors = []
    for field in ("lhs", "output", "target", "result", "name"):
        if field not in equation:
            continue
        raw_value = equation.get(field)
        if not isinstance(raw_value, str):
            errors.append(f"equation.{field} is not a string")
            continue
        candidate = raw_value.strip()
        if _is_safe_variable_name(candidate):
            return field, candidate, None
        errors.append(f"equation.{field} is not a safe identifier")

    if errors:
        return None, None, "RHS-only equation could not be normalized: " + "; ".join(errors) + "."
    return None, None, "RHS-only equation could not be normalized: no safe lhs identifier found in equation.name/lhs/output/target/result."


def _safe_rhs_expression_error(expression):
    try:
        tree = ast.parse(_normalize_boolean_operators(expression), mode="eval")
    except SyntaxError as exc:
        return f"syntax error: {exc.msg}"

    return _safe_rhs_node_error(tree.body)


def _safe_rhs_node_error(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (bool, int, float, str)) or node.value is None:
            return None
        return "constant type is not allowed"

    if isinstance(node, ast.Name):
        return None if _is_safe_variable_name(node.id) else f"name is not a safe identifier: {node.id}"

    if isinstance(node, ast.BinOp):
        if type(node.op) not in ALLOWED_BINOPS:
            return f"operator {type(node.op).__name__} is not allowed"
        return _first_rhs_error(node.left, node.right)

    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, ast.Not) and type(node.op) not in ALLOWED_UNARYOPS:
            return f"operator {type(node.op).__name__} is not allowed"
        return _safe_rhs_node_error(node.operand)

    if isinstance(node, ast.Compare):
        error = _safe_rhs_node_error(node.left)
        if error:
            return error
        for op, comparator in zip(node.ops, node.comparators, strict=False):
            op_type = type(op)
            if op_type in {ast.Is, ast.IsNot}:
                if not _is_null_node(comparator):
                    return "only null identity comparisons are allowed"
            elif op_type not in ALLOWED_COMPAREOPS:
                return f"comparison {op_type.__name__} is not allowed"
            error = _safe_rhs_node_error(comparator)
            if error:
                return error
        return None

    if isinstance(node, ast.BoolOp):
        if not isinstance(node.op, (ast.And, ast.Or)):
            return "only boolean AND/OR is supported"
        return _first_rhs_error(*node.values)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            return "function is not allowed"
        allowed_functions = set(ALLOWED_FUNCTIONS).union({
            "piecewise",
            "piecewise_select",
            "if_",
            "if_func",
            "any_null",
            "is_null",
            "min_ignore_null",
            "max_ignore_null",
            "argmin_label_ignore_null",
            "argmax_label_ignore_null",
            "value_for_label_ignore_null",
            "dim",
            "units",
            "unit",
        })
        if node.func.id not in allowed_functions:
            return f"function is not allowed: {node.func.id}"
        if node.keywords:
            return "keyword arguments are not allowed"
        return _first_rhs_error(*node.args)

    if isinstance(node, (ast.List, ast.Tuple)):
        return _first_rhs_error(*node.elts)

    return f"expression element {type(node).__name__} is not allowed"


def _first_rhs_error(*nodes):
    for node in nodes:
        error = _safe_rhs_node_error(node)
        if error:
            return error
    return None


def _split_assignment(expression):
    expression = _normalize_boolean_operators(expression)
    try:
        tree = ast.parse(expression, mode="exec")
    except SyntaxError:
        return None

    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Assign):
        return None

    assignment = tree.body[0]
    if len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name):
        return None

    lhs = assignment.targets[0].id
    if not _is_safe_variable_name(lhs):
        return None

    if len(expression) > MAX_EXPRESSION_LENGTH:
        return None

    rhs = ast.get_source_segment(expression, assignment.value)
    if not rhs:
        lhs_text, rhs_text = expression.split("=", 1)
        rhs = rhs_text.strip()

    return lhs, rhs.strip()


def _is_safe_variable_name(name):
    return isinstance(name, str) and name.isidentifier() and not keyword.iskeyword(name)


def _collect_names(expression):
    expression = _normalize_boolean_operators(expression)
    tree = ast.parse(expression, mode="eval")
    return {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id not in ALLOWED_FUNCTIONS and node.id not in _DIALECT_NON_VARIABLE_NAMES
    }


def _select_expression(mcm_request):
    expression = mcm_request.get("expression")
    if isinstance(expression, str) and expression.strip():
        return expression.strip()

    equations = mcm_request.get("equations")
    if not isinstance(equations, list) or len(equations) != 1:
        return None

    equation = equations[0]
    if isinstance(equation, dict):
        expression = equation.get("expression")
    else:
        expression = equation

    if not isinstance(expression, str) or not expression.strip():
        return None

    expression = expression.strip()
    if "=" in expression:
        left, right = expression.split("=", 1)
        solve_for = mcm_request.get("solve_for")
        if isinstance(solve_for, list) and len(solve_for) == 1:
            target = str(solve_for[0]).strip()
            if left.strip() == target:
                return right.strip()
        return None

    return expression


def _normalize_boolean_operators(expression):
    if not isinstance(expression, str):
        return expression
    expression, _ = _normalize_piecewise_default_argument(expression)
    expression = re.sub(r"\bpiecewise_select\s*\(", "piecewise(", expression, flags=re.IGNORECASE)
    expression = re.sub(r"\bif\s*\(", "if_(", expression, flags=re.IGNORECASE)
    expression = expression.replace("&&", " and ").replace("||", " or ")
    expression = re.sub(r"\bAND\b", "and", expression, flags=re.IGNORECASE)
    expression = re.sub(r"\bOR\b", "or", expression, flags=re.IGNORECASE)
    expression = re.sub(r"\bNOT\b", "not", expression, flags=re.IGNORECASE)
    expression = _normalize_null_checks(expression)
    expression = re.sub(r"\btrue\b", "True", expression, flags=re.IGNORECASE)
    expression = re.sub(r"\bfalse\b", "False", expression, flags=re.IGNORECASE)
    expression = re.sub(r"\bnull\b", "None", expression, flags=re.IGNORECASE)
    expression = _normalize_caret_exponentiation(expression)
    return expression


def _normalize_piecewise_default_argument(expression):
    if not isinstance(expression, str) or "else" not in expression.lower():
        return expression, False

    result = []
    position = 0
    changed = False
    pattern = re.compile(r"\bpiecewise(?:_select)?\s*\(", re.IGNORECASE)
    while True:
        match = pattern.search(expression, position)
        if not match:
            result.append(expression[position:])
            break

        open_index = expression.find("(", match.start(), match.end())
        close_index = _find_matching_paren(expression, open_index)
        if close_index is None:
            result.append(expression[position:])
            break

        result.append(expression[position:open_index + 1])
        inner = expression[open_index + 1:close_index]
        normalized_inner, inner_changed = _normalize_piecewise_inner_default_argument(inner)
        result.append(normalized_inner)
        result.append(")")
        changed = changed or inner_changed
        position = close_index + 1

    return "".join(result), changed


def _normalize_piecewise_inner_default_argument(inner):
    args = _split_top_level_arguments(inner)
    if not args:
        return inner, False
    candidate = args[-1].lstrip()
    if candidate[:4].lower() != "else":
        return inner, False
    remainder = candidate[4:].lstrip()
    if not remainder.startswith("="):
        return inner, False
    raw_value = remainder[1:]
    if not raw_value:
        return inner, False
    args[-1] = raw_value.strip()
    return ", ".join(arg.strip() for arg in args), True


def _find_matching_paren(text, open_index):
    if open_index < 0 or open_index >= len(text) or text[open_index] != "(":
        return None
    depth = 0
    quote = None
    escape = False
    for index in range(open_index, len(text)):
        char = text[index]
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def _split_top_level_arguments(text):
    args = []
    start = 0
    depth = 0
    quote = None
    escape = False
    for index, char in enumerate(text):
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            if depth > 0:
                depth -= 1
        elif char == "," and depth == 0:
            args.append(text[start:index])
            start = index + 1
    args.append(text[start:])
    return args


def _normalize_null_checks(expression):
    variable = r"([A-Za-z_]\w*)"
    null_literal = r"(?:null|none)"
    expression = re.sub(
        rf"\b{variable}\s+is\s+not\s+{null_literal}\b",
        r"not is_null(\1)",
        expression,
        flags=re.IGNORECASE,
    )
    expression = re.sub(
        rf"\b{variable}\s+is\s+{null_literal}\b",
        r"is_null(\1)",
        expression,
        flags=re.IGNORECASE,
    )
    expression = re.sub(
        rf"\b{variable}\s*!=\s*{null_literal}\b",
        r"not is_null(\1)",
        expression,
        flags=re.IGNORECASE,
    )
    expression = re.sub(
        rf"\b{variable}\s*==\s*{null_literal}\b",
        r"is_null(\1)",
        expression,
        flags=re.IGNORECASE,
    )
    return expression


def _normalize_caret_exponentiation(expression):
    if "^" not in expression:
        return expression

    result = []
    quote = None
    escaped = False
    for char in expression:
        if quote:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {"'", '"'}:
            quote = char
            result.append(char)
        elif char == "^":
            result.append("**")
        else:
            result.append(char)

    return "".join(result)


_DIALECT_NON_VARIABLE_NAMES = {
    "piecewise",
    "piecewise_select",
    "if_",
    "if_func",
    "any_null",
    "is_null",
    "min_ignore_null",
    "max_ignore_null",
    "argmin_label_ignore_null",
    "argmax_label_ignore_null",
    "value_for_label_ignore_null",
    "dim",
    "units",
    "unit",
    "True",
    "False",
    "None",
    "true",
    "false",
    "none",
    "null",
}


def _process_expression(mcm_request, expression, inputs):
    if len(expression) > MAX_EXPRESSION_LENGTH:
        return _base_result(
            mcm_request,
            status="unsupported",
            message="Expression is too long for the deterministic MCM evaluator.",
            outputs={},
            diagnostics=[f"Expression length exceeds {MAX_EXPRESSION_LENGTH} characters."],
        )

    try:
        value = _safe_eval(expression, inputs)
    except KeyError as e:
        return _base_result(
            mcm_request,
            status="needs_human_review",
            message="Expression references variables with no numeric value.",
            outputs={},
            diagnostics=[f"Missing numeric value for variable: {e.args[0]}"],
        )
    except Exception as e:
        return _base_result(
            mcm_request,
            status="unsupported",
            message=f"Expression could not be evaluated safely: {e}",
            outputs={},
            diagnostics=["Only arithmetic over numeric inputs and whitelisted math functions is supported."],
        )

    output_name = _output_name(mcm_request)
    return _base_result(
        mcm_request,
        status="computed",
        message="MCM completed deterministic expression evaluation.",
        outputs={output_name: value},
        diagnostics=[f"Evaluated expression: {expression}"],
        inputs_used=inputs,
    )


def _process_operation(mcm_request, operation, inputs):
    values = [value for value in inputs.values() if _is_number(value)]
    if not values:
        return _base_result(
            mcm_request,
            status="needs_human_review",
            message="Operation requested but no numeric inputs were available.",
            outputs={},
            diagnostics=["Provide numeric inputs or variable values before invoking MCM."],
        )

    try:
        for value in values:
            _validate_evaluated_value(value)
        if operation in SUPPORTED_OPERATIONS:
            value = SUPPORTED_OPERATIONS[operation](values)
        elif operation in {"subtract", "difference"}:
            if len(values) != 2:
                raise ValueError("difference requires exactly two numeric inputs")
            value = values[0] - values[1]
        elif operation in {"divide", "ratio"}:
            if len(values) != 2:
                raise ValueError("ratio requires exactly two numeric inputs")
            value = values[0] / values[1]
        elif operation in {"average", "mean"}:
            value = sum(values) / len(values)
        else:
            return _base_result(
                mcm_request,
                status="unsupported",
                message=f"Unsupported MCM operation: {operation}",
                outputs={},
                diagnostics=["Supported operations: add, sum, multiply, product, difference, ratio, average, min, max."],
            )
    except Exception as e:
        return _base_result(
            mcm_request,
            status="error",
            message=f"Operation failed: {e}",
            outputs={},
            diagnostics=["MCM operation failed with numeric inputs."],
        )

    try:
        value = _validate_evaluated_value(value)
    except ValueError as e:
        return _base_result(
            mcm_request,
            status="unsupported",
            message=f"Operation result was rejected safely: {e}",
            outputs={},
            diagnostics=["MCM rejected an unbounded or non-finite operation result."],
        )

    return _base_result(
        mcm_request,
        status="computed",
        message="MCM completed deterministic operation.",
        outputs={_output_name(mcm_request): value},
        diagnostics=[f"Executed operation: {operation}"],
        inputs_used=inputs,
    )


def _safe_eval(expression, names, declared_names=None):
    expression = _normalize_boolean_operators(expression)
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError("expression exceeds the evaluator length limit")
    tree = ast.parse(expression, mode="eval")
    nodes = list(ast.walk(tree))
    if len(nodes) > MAX_EXPRESSION_AST_NODES:
        raise ValueError("expression exceeds the AST node limit")
    stack = [(tree.body, 1)]
    while stack:
        current, depth = stack.pop()
        if depth > MAX_EXPRESSION_AST_DEPTH:
            raise ValueError("expression exceeds the AST depth limit")
        stack.extend((child, depth + 1) for child in ast.iter_child_nodes(current))
    return _validate_evaluated_value(
        _eval_node(tree.body, names, declared_names or set())
    )


def _validate_evaluated_value(value, depth=0):
    if depth > MAX_EXPRESSION_AST_DEPTH:
        raise ValueError("evaluated value exceeds the nesting limit")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value.bit_length() > MAX_EVALUATED_INTEGER_BITS:
            raise ValueError("integer result exceeds the bit-length limit")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite numeric values are not allowed")
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite numeric values are not allowed")
        if len(value.as_tuple().digits) > MAX_EVALUATED_INTEGER_BITS:
            raise ValueError("decimal result exceeds the precision limit")
        return value
    if isinstance(value, str):
        if len(value) > MAX_EVALUATED_SEQUENCE_LENGTH:
            raise ValueError("string result exceeds the length limit")
        return value
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_EVALUATED_CONTAINER_ITEMS:
            raise ValueError("sequence result exceeds the item limit")
        for item in value:
            _validate_evaluated_value(item, depth + 1)
        return value
    if isinstance(value, dict):
        if len(value) > MAX_EVALUATED_CONTAINER_ITEMS:
            raise ValueError("mapping result exceeds the item limit")
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("mapping result keys must be strings")
            _validate_evaluated_value(item, depth + 1)
        return value
    raise ValueError(f"evaluated value type {type(value).__name__} is not allowed")


def _bounded_binary_operation(op_type, left_value, right_value):
    _validate_evaluated_value(left_value)
    _validate_evaluated_value(right_value)
    if not _is_number(left_value) or not _is_number(right_value):
        raise ValueError("binary arithmetic requires numeric operands")

    if op_type is ast.Pow:
        if not _is_number(left_value) or not _is_number(right_value):
            raise ValueError("exponentiation requires numeric operands")
        if abs(right_value) > MAX_ABS_EXPONENT:
            raise ValueError("exponent exceeds the evaluator limit")
        if (
            isinstance(left_value, int)
            and not isinstance(left_value, bool)
            and isinstance(right_value, int)
            and not isinstance(right_value, bool)
            and right_value > 0
            and max(1, left_value.bit_length()) * right_value
            > MAX_EVALUATED_INTEGER_BITS
        ):
            raise ValueError("integer power exceeds the bit-length limit")

    return _validate_evaluated_value(
        ALLOWED_BINOPS[op_type](left_value, right_value)
    )


def _eval_node(node, names, declared_names=None):
    declared_names = declared_names or set()
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return _validate_evaluated_value(node.value)
        if isinstance(node.value, (int, float)):
            return _validate_evaluated_value(node.value)
        if isinstance(node.value, str):
            return _validate_evaluated_value(node.value)
        if node.value is None:
            return None
        raise ValueError("constant type is not allowed")

    if isinstance(node, ast.Name):
        if node.id in names:
            return _validate_evaluated_value(names[node.id])
        raise KeyError(node.id)

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_BINOPS:
            raise ValueError(f"operator {op_type.__name__} is not allowed")
        left_value = _eval_node(node.left, names, declared_names)
        right_value = _eval_node(node.right, names, declared_names)
        return _bounded_binary_operation(op_type, left_value, right_value)

    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return not bool(_eval_node(node.operand, names, declared_names))
        op_type = type(node.op)
        if op_type not in ALLOWED_UNARYOPS:
            raise ValueError(f"operator {op_type.__name__} is not allowed")
        return _validate_evaluated_value(
            ALLOWED_UNARYOPS[op_type](_eval_node(node.operand, names, declared_names))
        )

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, names, declared_names)
        for op, comparator in zip(node.ops, node.comparators, strict=False):
            op_type = type(op)
            if op_type in {ast.Is, ast.IsNot}:
                if not _is_null_node(comparator):
                    raise ValueError("only null identity comparisons are allowed")
                comparison_result = is_missing_value(left)
                if op_type is ast.IsNot:
                    comparison_result = not comparison_result
                if not comparison_result:
                    return False
                left = _eval_nullable_node(comparator, names, declared_names)
                continue
            if op_type not in ALLOWED_COMPAREOPS:
                raise ValueError(f"comparison {op_type.__name__} is not allowed")
            right = _eval_node(comparator, names, declared_names)
            if not _safe_compare_values(op_type, left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(bool(_eval_node(value, names, declared_names)) for value in node.values)
        if isinstance(node.op, ast.Or):
            return any(bool(_eval_node(value, names, declared_names)) for value in node.values)
        raise ValueError("only boolean AND/OR is supported")

    if isinstance(node, ast.Call):
        if _is_piecewise_call(node):
            return _eval_piecewise_node(node, names, declared_names)
        if _is_if_call(node):
            condition = _eval_node(node.args[0], names, declared_names)
            return _eval_nullable_node(node.args[1] if bool(condition) else node.args[2], names, declared_names)
        if _is_any_null_call(node):
            return _eval_any_null_node(node.args[0], names, declared_names)
        if _is_is_null_call(node):
            return _eval_is_null_node(node.args[0], names, declared_names)
        if _is_min_ignore_null_call(node):
            return _eval_min_ignore_null_node(node, names, declared_names)
        if _is_max_ignore_null_call(node):
            return _eval_max_ignore_null_node(node, names, declared_names)
        if _is_argmin_label_ignore_null_call(node):
            return _eval_argmin_label_ignore_null_node(node, names, declared_names)
        if _is_argmax_label_ignore_null_call(node):
            return _eval_argmax_label_ignore_null_node(node, names, declared_names)
        if _is_value_for_label_ignore_null_call(node):
            return _eval_value_for_label_ignore_null_node(node, names, declared_names)
        if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCTIONS:
            raise ValueError("function is not allowed")
        args = [_eval_node(arg, names, declared_names) for arg in node.args]
        if node.keywords:
            raise ValueError("keyword arguments are not allowed")
        return _validate_evaluated_value(ALLOWED_FUNCTIONS[node.func.id](*args))

    if isinstance(node, (ast.List, ast.Tuple)):
        if len(node.elts) > MAX_EVALUATED_CONTAINER_ITEMS:
            raise ValueError("sequence literal exceeds the item limit")
        return [_eval_nullable_node(item, names, declared_names) for item in node.elts]

    raise ValueError(f"expression element {type(node).__name__} is not allowed")


def _eval_any_null_node(node, names, declared_names=None):
    if isinstance(node, (ast.List, ast.Tuple)):
        return any(_node_is_nullish(item, names, declared_names) for item in node.elts)
    return _node_is_nullish(node, names, declared_names)


def _eval_is_null_node(node, names, declared_names=None):
    return _node_is_nullish(node, names, declared_names)


def _eval_min_ignore_null_node(node, names, declared_names=None):
    values = _numeric_values_from_nullable_list(node.args[0], names, declared_names, "min_ignore_null")
    if not values:
        return None
    return min(values)


def _eval_max_ignore_null_node(node, names, declared_names=None):
    values = _numeric_values_from_nullable_list(node.args[0], names, declared_names, "max_ignore_null")
    if not values:
        return None
    return max(values)


def _eval_argmin_label_ignore_null_node(node, names, declared_names=None):
    return _eval_label_selector_ignore_null_node(node, names, declared_names, maximize=False)


def _eval_argmax_label_ignore_null_node(node, names, declared_names=None):
    return _eval_label_selector_ignore_null_node(node, names, declared_names, maximize=True)


def _eval_label_selector_ignore_null_node(node, names, declared_names=None, maximize=False):
    declared_names = declared_names or set()
    helper_name = node.func.id if isinstance(node.func, ast.Name) else "label selector"
    if len(node.args) == 2:
        first_values = _nullable_list_values_from_node(
            node.args[0],
            names,
            declared_names,
            helper_name,
            "first argument",
        )
        second_values = _nullable_list_values_from_node(
            node.args[1],
            names,
            declared_names,
            helper_name,
            "second argument",
        )
        if first_values is None or second_values is None:
            return None
        labels_first = _selector_two_arg_order_is_labels_first(first_values, second_values)
        if labels_first:
            labels = first_values
            values = second_values
        else:
            values = first_values
            labels = second_values
        viable_flags = [True] * len(values or [])
        tie_breaker_lists = []
        tie_breaker_directions = []
    elif len(node.args) >= 3:
        labels = _nullable_list_values_from_node(
            node.args[0],
            names,
            declared_names,
            helper_name,
            "labels",
        )
        viable_flags = _nullable_list_values_from_node(
            node.args[1],
            names,
            declared_names,
            helper_name,
            "viability flags",
        )
        values = _nullable_list_values_from_node(
            node.args[2],
            names,
            declared_names,
            helper_name,
            "values",
        )
        tie_breaker_lists = [
            _nullable_list_values_from_node(
                tie_node,
                names,
                declared_names,
                helper_name,
                "tie-breaker values",
            )
            for tie_node in node.args[3:]
        ]
        tie_breaker_directions = [
            _selector_tie_breaker_direction(tie_node)
            for tie_node in node.args[3:]
        ]
    else:
        raise ValueError(f"{helper_name} expects at least two arguments")

    if values is None or labels is None or viable_flags is None or any(item is None for item in tie_breaker_lists):
        return None
    _validate_selector_list_lengths(helper_name, labels, viable_flags, values, tie_breaker_lists)

    best_value = None
    best_label = None
    best_tie_values = []
    for index, (value, label, viable) in enumerate(
        zip(values, labels, viable_flags, strict=False)
    ):
        if not _selector_viability_enabled(viable, helper_name):
            continue
        if is_missing_value(value):
            continue
        number = _coerce_number(value)
        if number is None:
            raise ValueError(f"{helper_name} primary metric values must be numeric or null")
        if is_missing_value(label):
            continue
        tie_values = [
            _selector_metric_number(tie_list[index], helper_name, "tie-breaker")
            for tie_list in tie_breaker_lists
        ]
        if _selector_candidate_is_better(
            number,
            tie_values,
            best_value,
            best_tie_values,
            maximize=maximize,
            tie_breaker_directions=tie_breaker_directions,
        ):
            best_value = number
            best_tie_values = tie_values
            best_label = label

    if best_label is None:
        return None
    return best_label


def _selector_two_arg_order_is_labels_first(first_values, second_values):
    first_metric = _selector_values_are_metric_compatible(first_values)
    second_metric = _selector_values_are_metric_compatible(second_values)
    first_text_label = _selector_values_contain_text_label(first_values)
    second_text_label = _selector_values_contain_text_label(second_values)
    if first_text_label and second_metric:
        return True
    if second_text_label and first_metric:
        return False
    if second_metric and not first_metric:
        return True
    return False


def _selector_values_are_metric_compatible(values):
    if not isinstance(values, (list, tuple)):
        return False
    for value in values:
        if is_missing_value(value):
            continue
        if _coerce_number(value) is None:
            return False
    return True


def _selector_values_contain_text_label(values):
    if not isinstance(values, (list, tuple)):
        return False
    return any(
        isinstance(value, str)
        and not is_missing_value(value)
        and _coerce_number(value) is None
        for value in values
    )


def _validate_selector_list_lengths(helper_name, labels, viable_flags, values, tie_breaker_lists):
    expected_length = len(labels)
    if len(values) != expected_length or len(viable_flags) != expected_length:
        raise ValueError(f"{helper_name} label, viability, and metric lists must have the same length")
    for tie_values in tie_breaker_lists:
        if len(tie_values) != expected_length:
            raise ValueError(f"{helper_name} tie-breaker lists must have the same length as labels")


def _selector_viability_enabled(value, helper_name):
    if is_missing_value(value):
        return False
    boolean_value = _coerce_boolean(value)
    if boolean_value is None:
        raise ValueError(f"{helper_name} viability flags must be boolean or boolean-like values")
    return boolean_value


def _selector_metric_number(value, helper_name, role):
    if is_missing_value(value):
        return None
    number = _coerce_number(value)
    if number is None:
        raise ValueError(f"{helper_name} {role} metric values must be numeric or null")
    return number


def _selector_tie_breaker_direction(node):
    try:
        source_text = ast.unparse(node)
    except Exception:
        source_text = ""
    names = [
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name)
    ]
    corpus = " ".join([source_text, *names]).lower()
    if not corpus:
        return "min"
    lower_is_better_markers = {
        "cost",
        "costs",
        "price",
        "prices",
        "payback",
        "complexity",
        "risk",
        "penalty",
        "penalties",
        "loss",
        "losses",
        "drop",
        "drops",
        "weight",
        "mass",
        "duration",
        "time",
        "score",
        "scores",
    }
    if any(marker in corpus for marker in lower_is_better_markers):
        return "min"
    higher_is_better_markers = {
        "margin",
        "margins",
        "reserve",
        "reserves",
        "headroom",
        "clearance",
    }
    if any(marker in corpus for marker in higher_is_better_markers):
        return "max"
    return "min"


def _selector_candidate_is_better(
    candidate_primary,
    candidate_ties,
    best_primary,
    best_ties,
    maximize=False,
    tie_breaker_directions=None,
):
    if best_primary is None:
        return True
    if maximize:
        if candidate_primary > best_primary:
            return True
        if candidate_primary < best_primary:
            return False
    else:
        if candidate_primary < best_primary:
            return True
        if candidate_primary > best_primary:
            return False

    tie_breaker_directions = tie_breaker_directions or []
    for index, (candidate_value, best_value) in enumerate(
        zip(candidate_ties, best_ties, strict=False)
    ):
        if candidate_value is None and best_value is None:
            continue
        if candidate_value is None:
            return False
        if best_value is None:
            return True
        direction = tie_breaker_directions[index] if index < len(tie_breaker_directions) else "min"
        if direction == "max":
            if candidate_value > best_value:
                return True
            if candidate_value < best_value:
                return False
        else:
            if candidate_value < best_value:
                return True
            if candidate_value > best_value:
                return False
    return False


def _eval_value_for_label_ignore_null_node(node, names, declared_names=None):
    declared_names = declared_names or set()
    selected_label = _eval_nullable_node(node.args[0], names, declared_names)
    if is_missing_value(selected_label):
        return None

    labels = _nullable_list_values_from_node(
        node.args[1],
        names,
        declared_names,
        "value_for_label_ignore_null",
        "labels",
    )
    values = _nullable_list_values_from_node(
        node.args[2],
        names,
        declared_names,
        "value_for_label_ignore_null",
        "values",
    )
    if labels is None or values is None:
        return None
    if len(labels) != len(values):
        raise ValueError("value_for_label_ignore_null label and value lists must have the same length")

    for label, value in zip(labels, values, strict=False):
        if is_missing_value(label):
            continue
        if _selector_labels_equal(selected_label, label):
            return None if is_missing_value(value) else value
    return None


def _safe_compare_values(op_type, left, right):
    if op_type in {ast.Eq, ast.NotEq}:
        numeric_equal = _numeric_values_equal_when_safe(left, right)
        if numeric_equal is not None:
            return numeric_equal if op_type is ast.Eq else not numeric_equal
    return ALLOWED_COMPAREOPS[op_type](left, right)


def _selector_labels_equal(left, right):
    numeric_equal = _numeric_values_equal_when_safe(left, right)
    if numeric_equal is not None:
        return numeric_equal
    return str(left) == str(right)


def _numeric_values_equal_when_safe(left, right):
    left_number = _coerce_number(left)
    right_number = _coerce_number(right)
    if left_number is None or right_number is None:
        return None
    if isinstance(left, str) and isinstance(right, str):
        return None
    return math.isclose(float(left_number), float(right_number), rel_tol=1e-12, abs_tol=1e-12)


def _numeric_values_from_nullable_list(node, names, declared_names=None, helper_name="min_ignore_null"):
    declared_names = declared_names or set()
    raw_values = _nullable_list_values_from_node(
        node,
        names,
        declared_names,
        helper_name,
        "values",
    )
    if raw_values is None:
        return []

    values = []
    for value in raw_values:
        if is_missing_value(value):
            continue
        number = _coerce_number(value)
        if number is None:
            raise ValueError(f"{helper_name} values must be numeric or null")
        values.append(number)
    return values


def _nullable_list_values_from_node(node, names, declared_names=None, helper_name="helper", argument_name="argument"):
    declared_names = declared_names or set()
    missing_names = _undefined_names_for_node(node, names, declared_names)
    if missing_names:
        raise KeyError(missing_names[0])

    if isinstance(node, (ast.List, ast.Tuple)):
        return [_eval_nullable_node(item, names, declared_names) for item in node.elts]

    value = _eval_nullable_node(node, names, declared_names)
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return list(value)
    raise ValueError(f"{helper_name} {argument_name} argument must be a list")


def _undefined_names_for_node(node, names, declared_names=None):
    declared_names = declared_names or set()
    missing = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Name):
            continue
        if child.id in names:
            continue
        if child.id in declared_names:
            continue
        if child.id in ALLOWED_FUNCTIONS or child.id in _DIALECT_NON_VARIABLE_NAMES:
            continue
        if _is_null_node(child):
            continue
        missing.append(child.id)
    return sorted(set(missing))


def _node_is_nullish(node, names, declared_names=None):
    if _is_null_node(node):
        return True
    if isinstance(node, ast.Name):
        if node.id in names:
            return is_missing_value(names.get(node.id))
        if node.id in (declared_names or set()):
            return True
        raise KeyError(node.id)
    try:
        return is_missing_value(_eval_nullable_node(node, names, declared_names))
    except KeyError:
        raise


def _eval_piecewise_node(node, names, declared_names=None):
    args = node.args
    has_default = len(args) % 2 == 1
    pair_count = (len(args) - 1) // 2 if has_default else len(args) // 2
    for index in range(pair_count):
        condition = _eval_node(args[index * 2], names, declared_names)
        if bool(condition):
            return _eval_nullable_node(args[index * 2 + 1], names, declared_names)
    if has_default:
        return _eval_nullable_node(args[-1], names, declared_names)
    return None


def _eval_nullable_node(node, names, declared_names=None):
    if _is_null_node(node):
        return None
    if _is_string_node(node):
        return node.value
    if isinstance(node, ast.Name) and node.id not in names and node.id in (declared_names or set()):
        return None
    return _eval_node(node, names, declared_names)


def _is_null_node(node):
    return (
        isinstance(node, ast.Name)
        and node.id in {"null", "None", "none"}
    ) or (
        isinstance(node, ast.Constant)
        and node.value is None
    )


def _output_name(mcm_request):
    requested_output = mcm_request.get("requested_output")
    if isinstance(requested_output, str) and requested_output.strip():
        return requested_output.strip()

    solve_for = mcm_request.get("solve_for")
    if isinstance(solve_for, list) and len(solve_for) == 1:
        return str(solve_for[0])

    objective = mcm_request.get("objective")
    if isinstance(objective, str) and objective.strip():
        return "objective_result"

    return "result"


def _coerce_number(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            return None
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, int):
        return value if value.bit_length() <= MAX_EVALUATED_INTEGER_BITS else None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            number = float(value.strip())
            return number if math.isfinite(number) else None
        except ValueError:
            return None
    return None


def _known_input_value(value):
    if value is None:
        return _MISSING_INPUT
    if isinstance(value, bool):
        return value
    if isinstance(value, (list, tuple)):
        known_values = []
        for item in value:
            if item is None:
                known_values.append(None)
                continue
            if isinstance(item, (list, tuple, dict)):
                return _MISSING_INPUT
            known_item = _known_input_value(item)
            if known_item is _MISSING_INPUT:
                known_values.append(None)
            else:
                known_values.append(known_item)
        return known_values

    number = _coerce_number(value)
    if number is not None:
        return number

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return _MISSING_INPUT
        lowered = text.lower()
        if lowered in {
            "unknown",
            "null",
            "none",
            "n/a",
            "na",
            "nan",
            "+nan",
            "-nan",
            "inf",
            "+inf",
            "-inf",
            "infinity",
            "+infinity",
            "-infinity",
        }:
            return _MISSING_INPUT
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return text

    return _MISSING_INPUT


def _known_input_value_for_unit(value, unit):
    if normalize_unit(unit) == "boolean":
        if isinstance(value, (list, tuple)):
            boolean_values = []
            for item in value:
                if item is None:
                    boolean_values.append(None)
                    continue
                boolean_value = _coerce_boolean(item)
                if boolean_value is None:
                    return _known_input_value(value)
                boolean_values.append(boolean_value)
            return boolean_values
        boolean_value = _coerce_boolean(value)
        if boolean_value is not None:
            return boolean_value
    return _known_input_value(value)


def _coerce_boolean(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isclose(float(value), 1.0, abs_tol=1e-12):
            return True
        if math.isclose(float(value), 0.0, abs_tol=1e-12):
            return False
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "y", "pass", "passed", "1"}:
            return True
        if lowered in {"false", "no", "n", "fail", "failed", "0"}:
            return False
    return None


def _normalize_status_value(value):
    if not isinstance(value, str):
        return None
    text = value.strip().upper()
    if text in {"PASS", "APPROVED", "ACCEPTED", "OK", "VALID", "TRUE"}:
        return "PASS"
    if text in {"FAIL", "FAILED", "REJECTED", "DENIED", "INVALID", "FALSE"}:
        return "FAIL"
    if text in {"UNKNOWN", "UNDETERMINED", "INDETERMINATE"}:
        return "UNKNOWN"
    token = re.sub(r"[^A-Z0-9]+", "_", text).strip("_")
    if token.startswith(("PASS_", "APPROVED_", "ACCEPTED_")):
        return "PASS"
    if token.startswith(("FAIL_", "FAILED_", "REJECTED_", "DENIED_", "NO_VIABLE_")):
        return "FAIL"
    return None


def _constraint_status_from_output(value):
    if isinstance(value, bool):
        return {
            "recognized": True,
            "status": "PASS" if value else "FAIL",
            "passes": value,
            "severity": "pass" if value else "fail",
            "unit": "boolean",
        }
    if value is None:
        return {
            "recognized": True,
            "status": "UNKNOWN",
            "passes": None,
            "severity": "unknown",
            "unit": "status_string",
        }
    if isinstance(value, str) and value.strip().lower() in {"null", "none", "n/a", "na"}:
        return {
            "recognized": True,
            "status": "UNKNOWN",
            "passes": None,
            "severity": "unknown",
            "unit": "status_string",
        }
    status = _normalize_status_value(value)
    if status is None:
        return {"recognized": False}
    return {
        "recognized": True,
        "status": status,
        "passes": True if status == "PASS" else False if status == "FAIL" else None,
        "severity": "pass" if status == "PASS" else "fail" if status == "FAIL" else "unknown",
        "unit": "status_string",
    }


def _is_status_value(value):
    return _constraint_status_from_output(value).get("recognized", False)


def _is_status_unit(unit):
    return normalize_unit(unit) == "status_string"


def _looks_like_status_output_name(name):
    lowered = str(name or "").lower()
    return (
        lowered.endswith("_status")
        or lowered.endswith("_pass")
        or _criterion_output_index(lowered) is not None
        or lowered in set(_overall_status_alias_names()).union({"status"})
    )


def _is_diagnostic_boolean_output_name(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return False
    return (
        lowered.startswith((
            "is_",
            "has_",
            "likely_cause_",
            "probable_cause_",
            "root_cause_",
            "eliminated_cause_",
            "ruled_out_cause_",
        ))
        or "_likely_cause_" in lowered
        or "_probable_cause_" in lowered
        or "_eliminated_cause_" in lowered
        or "_ruled_out_cause_" in lowered
        or "_diagnostic_" in lowered
        or "_symptom_" in lowered
    )


def _apply_value_based_unit_validation(lhs, value, unit_check, variable_meta):
    status_value = _normalize_status_value(value)
    if status_value is None:
        return

    meta = variable_meta.setdefault(lhs, {})
    meta["unit"] = "status_string"
    unit_check.update({
        "lhs_expected_unit": "status_string",
        "rhs_inferred_unit": "status_string",
        "status": "valid",
        "severity": "info",
        "message": f"Unit validation passed: output value {status_value} is a status string.",
    })


def _attach_constraint_checks_result(mcm_request, result):
    checks = check_constraints(mcm_request, result.get("outputs", {}), result)
    if checks.get("enabled"):
        result["constraint_checks"] = checks
        diagnostics = checks.get("diagnostics") or []
        if diagnostics:
            result.setdefault("diagnostics", []).extend(diagnostics)
    result.pop("_constraint_env", None)
    result.pop("_constraint_units", None)
    return result


def normalize_comparator(comparator: str) -> str | None:
    if not isinstance(comparator, str):
        return None
    text = comparator.strip().lower()
    direct = {"<=", "<", ">=", ">", "==", "!="}
    if text in direct:
        return text
    phrases = [
        ("less than or equal to", "<="),
        ("no more than", "<="),
        ("at most", "<="),
        ("below or equal to", "<="),
        ("greater than or equal to", ">="),
        ("at least", ">="),
        ("no less than", ">="),
        ("less than", "<"),
        ("below", "<"),
        ("greater than", ">"),
        ("above", ">"),
        ("equal to", "=="),
    ]
    for phrase, symbol in phrases:
        if text == phrase:
            return symbol
    return None


def parse_constraint_string(text: str, env: dict, variable_metadata: dict) -> dict | None:
    if not isinstance(text, str) or not text.strip():
        return None

    stripped = text.strip()
    if _is_qualitative_constraint_text(stripped):
        return None

    parsed_symbolic = _parse_symbolic_constraint_expression(stripped)
    if parsed_symbolic and _constraint_operands_are_known(parsed_symbolic["lhs"], parsed_symbolic["rhs"], env):
        parsed_symbolic.update({
            "name": _constraint_name_from_lhs(parsed_symbolic.get("lhs")),
            "source": "string",
            "expression": stripped,
        })
        return parsed_symbolic

    symbolic = re.search(
        r"\b(?P<lhs>[A-Za-z_]\w*)\b\s*(?P<comparator><=|>=|==|!=|<|>)\s*(?P<rhs>-?\d+(?:\.\d+)?|[A-Za-z_]\w*)",
        stripped,
    )
    if symbolic:
        lhs = symbolic.group("lhs")
        rhs = symbolic.group("rhs")
        if not _constraint_operands_are_known(lhs, rhs, env):
            return None
        return {
            "name": _constraint_name_from_lhs(symbolic.group("lhs")),
            "lhs": symbolic.group("lhs"),
            "comparator": symbolic.group("comparator"),
            "rhs": symbolic.group("rhs"),
            "source": "string",
            "expression": f"{symbolic.group('lhs')} {symbolic.group('comparator')} {symbolic.group('rhs')}",
        }

    phrases = [
        "less than or equal to",
        "no more than",
        "at most",
        "below or equal to",
        "greater than or equal to",
        "at least",
        "no less than",
        "less than",
        "below",
        "greater than",
        "above",
        "equal to",
    ]
    for phrase in phrases:
        pattern = (
            r"\b(?P<lhs>[A-Za-z_]\w*)\b.*?\b"
            + re.escape(phrase)
            + r"\b\s*(?P<rhs>-?\d+(?:\.\d+)?|[A-Za-z_]\w*)(?:\s*(?P<unit>[A-Za-z_/%]+))?"
        )
        match = re.search(pattern, stripped, re.IGNORECASE)
        if match:
            lhs = match.group("lhs")
            rhs = match.group("rhs")
            if not _constraint_operands_are_known(lhs, rhs, env):
                return None
            return {
                "name": _constraint_name_from_lhs(match.group("lhs")),
                "lhs": match.group("lhs"),
                "comparator": normalize_comparator(phrase),
                "rhs": match.group("rhs"),
                "rhs_unit": match.group("unit"),
                "source": "string",
                "expression": stripped,
            }

    return None


def _parse_symbolic_constraint_expression(text):
    try:
        tree = ast.parse(_normalize_boolean_operators(text), mode="eval")
    except SyntaxError:
        return None
    node = tree.body
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
        return None
    comparator = _comparator_symbol(node.ops[0])
    if not comparator:
        return None
    lhs = _simple_constraint_operand(node.left)
    rhs = _simple_constraint_operand(node.comparators[0])
    if lhs is None or rhs is None:
        return None
    return {
        "lhs": lhs,
        "comparator": comparator,
        "rhs": rhs,
    }


def evaluate_constraint(lhs_value, comparator, rhs_value) -> bool:
    comparator = normalize_comparator(comparator)
    if comparator == "<=":
        return lhs_value <= rhs_value
    if comparator == "<":
        return lhs_value < rhs_value
    if comparator == ">=":
        return lhs_value >= rhs_value
    if comparator == ">":
        return lhs_value > rhs_value
    if comparator == "==":
        return lhs_value == rhs_value
    if comparator == "!=":
        return lhs_value != rhs_value
    raise ValueError(f"Unsupported comparator: {comparator}")


def compute_constraint_margin(lhs_value, comparator, rhs_value) -> dict:
    comparator = normalize_comparator(comparator)
    if comparator in {"<=", "<"}:
        margin = rhs_value - lhs_value
    elif comparator in {">=", ">"}:
        margin = lhs_value - rhs_value
    elif comparator == "==":
        margin = lhs_value - rhs_value
    else:
        return {"margin": None, "margin_percent": None}

    margin_percent = (margin / rhs_value) * 100 if _is_number(rhs_value) and rhs_value != 0 else None
    return {"margin": margin, "margin_percent": margin_percent}


def check_constraints(mcm_request, outputs, result=None) -> dict:
    env, units = _constraint_environment(mcm_request, outputs, result)
    specs = _collect_constraint_specs(mcm_request, outputs, env)
    specs = _dedupe_constraint_specs(specs, env, units)
    policy_notes = _constraint_policy_notes(mcm_request)
    qualitative_notes = _qualitative_constraint_notes(mcm_request)
    margin_sensitive_rules = _margin_sensitive_rule_notes(mcm_request)
    diagnostics = []
    checks = []

    for spec in specs:
        check = _evaluate_constraint_spec(spec, env, units)
        checks.append(check)
        if check.get("severity") == "unknown":
            diagnostics.append(check.get("message", "Constraint could not be evaluated."))

    if not checks and _constraints_requested(mcm_request):
        diagnostics.append("No supported constraints were recognized.")

    enabled = bool(checks) or _constraints_requested(mcm_request)
    return {
        "enabled": enabled,
        "checks": checks,
        "summary": _constraint_summary(checks),
        "diagnostics": diagnostics,
        "constraint_policy_notes": policy_notes,
        "qualitative_constraint_notes": qualitative_notes,
        "margin_sensitive_rules": margin_sensitive_rules,
    }


def _constraint_environment(mcm_request, outputs, result=None):
    env = {}
    units = {}

    if isinstance(result, dict):
        stored_env = result.get("_constraint_env")
        stored_units = result.get("_constraint_units")
        if isinstance(stored_env, dict):
            env.update(stored_env)
        if isinstance(stored_units, dict):
            units.update(stored_units)

    if isinstance(outputs, dict):
        for name, output in outputs.items():
            if isinstance(output, dict):
                env[str(name)] = output.get("value")
                units[str(name)] = (
                    normalize_unit(output.get("unit"))
                    if output.get("unit") is not None
                    else _unit_from_name_suffix(name)
                )

    inputs = _extract_inputs(mcm_request)
    for name, value in inputs.items():
        env.setdefault(name, value)

    variables = mcm_request.get("variables") if isinstance(mcm_request, dict) else None
    if isinstance(variables, dict):
        for name, meta in variables.items():
            if isinstance(meta, dict):
                known_value = _known_input_value(meta.get("value"))
                if known_value is not _MISSING_INPUT:
                    env.setdefault(str(name), known_value)
                raw_unit = meta.get("unit")
                if raw_unit not in (None, ""):
                    units.setdefault(str(name), normalize_unit(raw_unit))
                else:
                    suffix_unit = _unit_from_name_suffix(name)
                    if suffix_unit:
                        units.setdefault(str(name), suffix_unit)
    return env, units


def _collect_constraint_specs(mcm_request, outputs, env):
    specs = []
    constraints = mcm_request.get("constraints") if isinstance(mcm_request, dict) else None
    if isinstance(constraints, list):
        for index, constraint in enumerate(constraints, start=1):
            if isinstance(constraint, dict):
                comparator = normalize_comparator(str(constraint.get("comparator", "")))
                specs.append({
                    "name": constraint.get("name") or f"constraint_{index}",
                    "lhs": constraint.get("lhs"),
                    "comparator": comparator,
                    "rhs": constraint.get("rhs"),
                    "unit": constraint.get("unit"),
                    "description": constraint.get("description"),
                    "source": "structured",
                    "expression": _constraint_expression(constraint.get("lhs"), comparator, constraint.get("rhs")),
                })
            elif isinstance(constraint, str):
                if _is_constraint_policy_note(constraint):
                    continue
                parsed = parse_constraint_string(constraint, env, {})
                if parsed:
                    specs.append(parsed)

    specs.extend(_constraints_from_equations(mcm_request))
    specs.extend(_status_constraint_specs(mcm_request, env))
    specs.extend(_auto_constraint_specs(mcm_request, outputs, env))
    return specs


def _dedupe_constraint_specs(specs, env=None, units=None):
    priority = {"structured": 0, "equation": 1, "auto": 2, "string": 3, "status_output": 4}
    status_indexes = {
        spec.get("criterion_index")
        for spec in specs
        if spec.get("source") == "status_output" and spec.get("criterion_index") is not None
    }
    evaluated_numeric_indexes = set()
    if isinstance(env, dict) and isinstance(units, dict):
        for spec in specs:
            if spec.get("source") == "status_output":
                continue
            spec_index = spec.get("criterion_index")
            if spec_index is None:
                spec_index = _criterion_output_index(spec.get("boolean_output") or spec.get("name") or spec.get("lhs"))
            if spec_index is None:
                continue
            if not _spec_has_arithmetic_operand(spec):
                continue
            check = _evaluate_constraint_spec(spec, env, units)
            if check.get("severity") != "unknown":
                evaluated_numeric_indexes.add(spec_index)

    selected = {}
    order = []
    for spec in specs:
        spec_index = spec.get("criterion_index")
        if spec_index is None:
            spec_index = _criterion_output_index(spec.get("boolean_output") or spec.get("name") or spec.get("lhs"))
        if spec.get("source") == "status_output" and spec_index in evaluated_numeric_indexes:
            continue
        if spec.get("source") != "status_output" and spec_index in status_indexes and spec_index not in evaluated_numeric_indexes:
            continue
        key = (spec.get("lhs"), spec.get("comparator"), str(spec.get("rhs")))
        if key not in selected:
            selected[key] = spec
            order.append(key)
            continue
        current = selected[key]
        if priority.get(spec.get("source"), 9) < priority.get(current.get("source"), 9):
            selected[key] = spec
    return [selected[key] for key in order]


def _spec_has_arithmetic_operand(spec):
    return (
        _looks_like_constraint_arithmetic_expression(spec.get("lhs"))
        or _looks_like_constraint_arithmetic_expression(spec.get("rhs"))
    )


def _status_constraint_specs(mcm_request, env):
    descriptions = {}
    equations = {}
    output_names = set()
    variables = mcm_request.get("variables") if isinstance(mcm_request, dict) else None
    if isinstance(variables, dict):
        for name, meta in variables.items():
            if isinstance(meta, dict) and meta.get("description"):
                descriptions[str(name)] = str(meta.get("description"))

    raw_equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    if isinstance(raw_equations, list):
        for equation in raw_equations:
            expression = _equation_expression(equation)
            parsed = _split_assignment(expression) if expression else None
            if parsed:
                lhs, _ = parsed
                equations[lhs] = expression

    solve_for = mcm_request.get("solve_for") if isinstance(mcm_request, dict) else None
    if isinstance(solve_for, list):
        output_names.update(str(name) for name in solve_for)
    output_names.update(equations)

    specs = []
    for name, value in env.items():
        index = _criterion_output_index(name)
        if index is None:
            continue
        status_data = _constraint_status_from_output(value)
        if not status_data.get("recognized"):
            continue
        if output_names and str(name) not in output_names:
            continue
        specs.append({
            "name": str(name),
            "lhs": str(name),
            "criterion_index": index,
            "source": "status_output",
            "status_value": status_data.get("status"),
            "raw_value": value,
            "status_unit": status_data.get("unit"),
            "description": descriptions.get(str(name)),
            "expression": equations.get(str(name)) or str(name),
        })
    return specs


def _constraints_from_equations(mcm_request):
    equations = mcm_request.get("equations") if isinstance(mcm_request, dict) else None
    if not isinstance(equations, list):
        return []
    mode = normalize_eas_mode(mcm_request.get("mode")) if isinstance(mcm_request, dict) else None
    specs = []
    for index, equation in enumerate(equations, start=1):
        expression = _equation_expression(equation)
        if not expression:
            continue
        parsed = _split_assignment(expression)
        if not parsed:
            continue
        lhs, rhs = parsed
        if mode == "diagnose-root-cause" and _is_diagnostic_boolean_output_name(lhs):
            continue
        if _looks_like_unit_output(lhs) or "dim(" in rhs or "units(" in rhs:
            continue
        if "margin_sensitive" in lhs or lhs in {
            "any_known_constraint_fail",
            "any_constraint_unknown",
            "overall_constraint_status",
        }:
            continue
        try:
            tree = ast.parse(_normalize_boolean_operators(rhs), mode="eval")
        except SyntaxError:
            continue
        node = tree.body
        if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
            continue
        comparator = _comparator_symbol(node.ops[0])
        if not comparator:
            continue
        specs.append({
            "name": _equation_name(equation, index),
            "lhs": _simple_constraint_operand(node.left),
            "comparator": comparator,
            "rhs": _simple_constraint_operand(node.comparators[0]),
            "source": "equation",
            "expression": rhs,
            "description": _equation_purpose(equation),
            "boolean_output": lhs,
            "criterion_index": _criterion_output_index(lhs),
        })
    return specs


def _auto_constraint_specs(mcm_request, outputs, env):
    specs = []
    if "cooling_time_hours" in outputs and "cooldown_requirement_hours" in env:
        specs.append({
            "name": "cooldown_requirement",
            "lhs": "cooling_time_hours",
            "comparator": "<=",
            "rhs": "cooldown_requirement_hours",
            "unit": "h",
            "description": "Cooldown must be completed within the required time.",
            "source": "auto",
            "expression": "cooling_time_hours <= cooldown_requirement_hours",
        })
    if "fuse_factor_of_safety" in outputs and "required_factor_of_safety" in env:
        specs.append({
            "name": "fuse_factor_of_safety_requirement",
            "lhs": "fuse_factor_of_safety",
            "comparator": ">=",
            "rhs": "required_factor_of_safety",
            "description": "Fuse factor of safety must meet or exceed requirement.",
            "source": "auto",
            "expression": "fuse_factor_of_safety >= required_factor_of_safety",
        })
    if "factor_of_safety" in outputs and "required_factor_of_safety" in env:
        specs.append({
            "name": "factor_of_safety_requirement",
            "lhs": "factor_of_safety",
            "comparator": ">=",
            "rhs": "required_factor_of_safety",
            "description": "Factor of safety must meet or exceed requirement.",
            "source": "auto",
            "expression": "factor_of_safety >= required_factor_of_safety",
        })
    if "current_A" in outputs and "fuse_capacity_A" in env:
        specs.append({
            "name": "fuse_current_capacity",
            "lhs": "current_A",
            "comparator": "<=",
            "rhs": "fuse_capacity_A",
            "unit": "A",
            "description": "Current must not exceed fuse capacity.",
            "source": "auto",
            "expression": "current_A <= fuse_capacity_A",
        })
    if ("bath_surface_temperature_C" in env or "max_safe_surface_temperature_C" in env) and (
        "bath_surface_temperature_C" in env or "max_safe_surface_temperature_C" in env
    ):
        specs.append({
            "name": "surface_temperature_constraint",
            "lhs": "bath_surface_temperature_C",
            "comparator": "<=",
            "rhs": "max_safe_surface_temperature_C",
            "unit": "C",
            "description": "Bath surface temperature must not exceed the maximum safe surface temperature.",
            "source": "auto",
            "expression": "bath_surface_temperature_C <= max_safe_surface_temperature_C",
        })
    if _canonical_formula_operation(mcm_request) == "requirement_check" and "passes" in outputs:
        comparator = normalize_comparator(str(mcm_request.get("comparator", "")))
        if comparator:
            specs.append({
                "name": "requirement_check",
                "lhs": "value",
                "comparator": comparator,
                "rhs": "limit",
                "description": "Requirement-check handler constraint.",
                "source": "auto",
                "expression": f"value {comparator} limit",
            })
    return specs


def _evaluate_constraint_spec(spec, env, units):
    if spec.get("source") == "status_output":
        return _evaluate_status_constraint_spec(spec)

    if spec.get("unrecognized"):
        return _unknown_constraint(spec, "Constraint text was not recognized as a supported deterministic check.")

    comparator = normalize_comparator(str(spec.get("comparator", "")))
    if not comparator:
        return _unknown_constraint(spec, "Constraint comparator is missing or unsupported.")

    lhs_token = spec.get("lhs")
    rhs_token = spec.get("rhs")
    lhs_value, lhs_unit, lhs_missing = _resolve_constraint_value(lhs_token, env, units, spec.get("unit"))
    rhs_value, rhs_unit, rhs_missing = _resolve_constraint_value(rhs_token, env, units, spec.get("rhs_unit") or spec.get("unit"))
    if (
        lhs_unit
        and rhs_missing is None
        and _coerce_number(rhs_token) is not None
        and not spec.get("rhs_unit")
        and not spec.get("unit")
    ):
        rhs_unit = lhs_unit
    if lhs_unit and rhs_missing is None and not rhs_unit and _looks_like_constraint_arithmetic_expression(rhs_token):
        rhs_unit = lhs_unit
    if rhs_unit and lhs_missing is None and not lhs_unit and _looks_like_constraint_arithmetic_expression(lhs_token):
        lhs_unit = rhs_unit

    if lhs_missing or rhs_missing:
        status_check = _status_constraint_check_from_boolean_output(spec, env)
        if status_check:
            return status_check
        missing = [item for item in (lhs_missing, rhs_missing) if item]
        label = "values" if len(missing) > 1 else "value"
        return _unknown_constraint(spec, f"Constraint references unavailable {label}: {', '.join(missing)}.")

    unit_check = _constraint_unit_validation(lhs_unit, rhs_unit, comparator)
    if unit_check.get("status") != "valid":
        status_check = _status_constraint_check_from_boolean_output(spec, env)
        if status_check:
            return status_check
        check = _unknown_constraint(spec, unit_check.get("message", "Constraint unit compatibility is unknown."))
        check["unit_validation"] = unit_check
        check.update({
            "lhs_value": lhs_value,
            "lhs_unit": lhs_unit,
            "rhs_value": rhs_value,
            "rhs_unit": rhs_unit,
            "comparator": comparator,
        })
        return check

    try:
        passes = evaluate_constraint(lhs_value, comparator, rhs_value)
    except Exception as e:
        return _unknown_constraint(spec, f"Constraint could not be evaluated: {e}")

    margin_data = compute_constraint_margin(lhs_value, comparator, rhs_value)
    margin = margin_data.get("margin")
    margin_percent = margin_data.get("margin_percent")
    severity = "pass" if passes else "fail"
    margin_sensitive = bool(passes and margin_percent is not None and margin_percent > 0 and margin_percent <= 10)
    if margin_sensitive:
        message = f"Constraint passes with a margin-sensitive positive margin of {margin_percent:.3g}%."
    elif passes:
        message = "Constraint passed."
    else:
        message = "Constraint failed."

    return {
        "name": spec.get("name") or _constraint_name_from_lhs(lhs_token),
        "expression": spec.get("expression") or _constraint_expression(lhs_token, comparator, rhs_token),
        "boolean_output": spec.get("boolean_output"),
        "lhs": lhs_token,
        "lhs_value": lhs_value,
        "lhs_unit": lhs_unit,
        "comparator": comparator,
        "rhs": rhs_token,
        "rhs_value": rhs_value,
        "rhs_unit": rhs_unit,
        "passes": passes,
        "margin": margin,
        "margin_unit": lhs_unit if margin is not None else None,
        "margin_percent": margin_percent,
        "severity": severity,
        "message": message,
        "source": spec.get("source"),
        "description": spec.get("description"),
        "unit_validation": unit_check,
        "margin_sensitive": margin_sensitive,
    }


def _status_constraint_check_from_boolean_output(spec, env):
    boolean_output = spec.get("boolean_output")
    if not boolean_output or not isinstance(env, dict) or boolean_output not in env:
        return None
    status_data = _constraint_status_from_output(env.get(boolean_output))
    if not status_data.get("recognized"):
        return None
    return _evaluate_status_constraint_spec({
        "name": boolean_output,
        "lhs": boolean_output,
        "source": "status_output",
        "raw_value": env.get(boolean_output),
        "status_unit": status_data.get("unit"),
        "description": spec.get("description"),
        "expression": spec.get("expression") or _constraint_expression(
            spec.get("lhs"),
            spec.get("comparator"),
            spec.get("rhs"),
        ),
    })


def _evaluate_status_constraint_spec(spec):
    status_data = _constraint_status_from_output(spec.get("raw_value"))
    if not status_data.get("recognized"):
        status_data = _constraint_status_from_output(spec.get("status_value"))
    status_value = status_data.get("status", "UNKNOWN")
    passes = status_data.get("passes")
    severity = status_data.get("severity", "unknown")
    description = spec.get("description")
    if status_value == "PASS":
        message = f"Status output {spec.get('name')} is PASS."
    elif status_value == "FAIL":
        message = f"Status output {spec.get('name')} is FAIL."
    else:
        message = f"Status output {spec.get('name')} is UNKNOWN."
    if description:
        message = f"{message} {description}"

    return {
        "name": spec.get("name"),
        "expression": spec.get("expression"),
        "boolean_output": spec.get("boolean_output"),
        "lhs": spec.get("lhs"),
        "lhs_value": spec.get("raw_value") if "raw_value" in spec else status_value,
        "lhs_unit": spec.get("status_unit") or status_data.get("unit") or "status_string",
        "comparator": "status",
        "rhs": None,
        "rhs_value": None,
        "rhs_unit": None,
        "passes": passes,
        "margin": None,
        "margin_unit": None,
        "margin_percent": None,
        "severity": severity,
        "message": message,
        "source": "status_output",
        "description": description,
        "unit_validation": {
            "status": "valid",
            "severity": "info",
            "message": "Status output mapped directly to a Layer 6 constraint check.",
        },
        "margin_sensitive": False,
    }


def _unknown_constraint(spec, message):
    return {
        "name": spec.get("name"),
        "expression": spec.get("expression"),
        "boolean_output": spec.get("boolean_output"),
        "lhs": spec.get("lhs"),
        "lhs_value": None,
        "lhs_unit": None,
        "comparator": spec.get("comparator"),
        "rhs": spec.get("rhs"),
        "rhs_value": None,
        "rhs_unit": None,
        "passes": None,
        "margin": None,
        "margin_unit": None,
        "margin_percent": None,
        "severity": "unknown",
        "message": message,
        "source": spec.get("source"),
        "description": spec.get("description"),
        "unit_validation": None,
    }


def _resolve_constraint_value(token, env, units, explicit_unit=None):
    if token is None:
        return None, normalize_unit(explicit_unit) if explicit_unit else None, "missing operand"
    if isinstance(token, (int, float)) and not isinstance(token, bool):
        return token, normalize_unit(explicit_unit) if explicit_unit else "dimensionless", None

    text = str(token).strip()
    if text in {"True", "true"}:
        return True, "boolean", None
    if text in {"False", "false"}:
        return False, "boolean", None
    number = _coerce_number(text)
    if number is not None:
        return number, normalize_unit(explicit_unit) if explicit_unit else "dimensionless", None
    if text in env:
        value = env[text]
        if is_missing_value(value):
            return None, normalize_unit(explicit_unit) if explicit_unit else units.get(text), text
        return value, normalize_unit(explicit_unit) if explicit_unit else units.get(text), None
    boolean_expression_value = _resolve_constraint_boolean_expression(text, env, units, explicit_unit)
    if boolean_expression_value:
        return boolean_expression_value
    expression_value = _resolve_constraint_arithmetic_expression(text, env, units, explicit_unit)
    if expression_value:
        return expression_value
    return None, normalize_unit(explicit_unit) if explicit_unit else None, text


def _resolve_constraint_boolean_expression(text, env, units, explicit_unit=None):
    if not isinstance(text, str) or "is_null" not in text:
        return None
    try:
        expression = _normalize_boolean_operators(text)
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return None

    missing = _missing_names_for_constraint_null_expression(tree.body, env)
    if missing is None:
        return None
    if missing:
        return None, normalize_unit(explicit_unit) if explicit_unit else "boolean", ", ".join(missing)

    try:
        value = _safe_eval(expression, env)
    except Exception:
        return None
    if not isinstance(value, bool):
        return None
    return value, normalize_unit(explicit_unit) if explicit_unit else "boolean", None


def _missing_names_for_constraint_null_expression(node, env):
    if _is_is_null_call(node):
        if not node.args:
            return None
        return _missing_names_for_is_null_argument(node.args[0], env)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return _missing_names_for_constraint_null_expression(node.operand, env)
    return None


def _missing_names_for_is_null_argument(node, env):
    names = sorted({
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name)
        and child.id not in ALLOWED_FUNCTIONS
        and child.id not in _DIALECT_NON_VARIABLE_NAMES
    })
    return [name for name in names if name not in env]


def _resolve_constraint_arithmetic_expression(text, env, units, explicit_unit=None):
    if not isinstance(text, str) or not _looks_like_constraint_arithmetic_expression(text):
        return None
    try:
        expression = _normalize_boolean_operators(text)
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return None
    if not _is_constraint_arithmetic_node(tree.body):
        return None

    names = {
        node.id
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Name)
            and node.id not in ALLOWED_FUNCTIONS
            and node.id not in _DIALECT_NON_VARIABLE_NAMES
        )
    }
    missing = sorted(name for name in names if name not in env or is_missing_value(env.get(name)))
    if missing:
        return None, normalize_unit(explicit_unit) if explicit_unit else None, ", ".join(missing)

    try:
        value = _safe_eval(expression, env)
    except Exception:
        return None
    if not _is_number(value):
        return None

    unit = normalize_unit(explicit_unit) if explicit_unit else None
    if not unit:
        inferred = infer_rhs_unit(expression, units)
        if inferred.get("status") == "valid":
            unit = inferred.get("unit")
    return value, unit, None


def _looks_like_constraint_arithmetic_expression(token):
    if not isinstance(token, str):
        return False
    text = token.strip()
    if not text:
        return False
    if text in {"True", "true", "False", "false"}:
        return False
    if _coerce_number(text) is not None:
        return False
    return any(operator_text in text for operator_text in ("+", "-", "*", "/", "(", ")"))


def _is_constraint_arithmetic_node(node):
    if _is_numeric_constant(node):
        return True
    if isinstance(node, ast.Name):
        return _is_safe_variable_name(node.id)
    if isinstance(node, ast.Call):
        return _is_constraint_numeric_call_node(node)
    if isinstance(node, (ast.List, ast.Tuple)):
        return all(_is_constraint_arithmetic_node(item) for item in node.elts)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _is_constraint_arithmetic_node(node.operand)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        return _is_constraint_arithmetic_node(node.left) and _is_constraint_arithmetic_node(node.right)
    return False


def _is_constraint_numeric_call_node(node):
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return False
    if node.keywords:
        return False
    if node.func.id not in {"abs", "min", "max", "round", "floor", "ceil", "sqrt"}:
        return False
    return bool(node.args) and all(_is_constraint_arithmetic_node(arg) for arg in node.args)


def is_missing_value(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"unknown", "null", "none", "n/a", "na"}
    return False


def _constraint_unit_validation(lhs_unit, rhs_unit, comparator):
    lhs_unit = normalize_unit(lhs_unit) if lhs_unit else None
    rhs_unit = normalize_unit(rhs_unit) if rhs_unit else None
    if not lhs_unit and not rhs_unit:
        return {
            "status": "valid",
            "severity": "info",
            "message": "Constraint units were not declared on either side; numeric comparison was evaluated without unit validation.",
        }
    if not lhs_unit or not rhs_unit:
        return {
            "status": "unknown",
            "severity": "info",
            "message": "Constraint unit compatibility is unknown because one side lacks units.",
        }
    if lhs_unit == rhs_unit:
        return {
            "status": "valid",
            "severity": "info",
            "message": f"Constraint units are compatible: {lhs_unit}.",
        }
    if _units_validation_compatible(lhs_unit, rhs_unit):
        return {
            "status": "valid",
            "severity": "info",
            "message": f"Constraint units are dimensionally compatible: {lhs_unit} vs {rhs_unit}.",
        }
    if {lhs_unit, rhs_unit} == {"percent", "dimensionless"}:
        return {
            "status": "valid",
            "severity": "info",
            "message": "Percent threshold is compatible with a dimensionless numeric literal.",
        }
    if lhs_unit == "boolean" or rhs_unit == "boolean":
        if lhs_unit == rhs_unit and comparator in {"==", "!="}:
            return {"status": "valid", "severity": "info", "message": "Boolean equality/inequality constraint is valid."}
        return {
            "status": "unknown",
            "severity": "warning",
            "message": f"Boolean constraints only support equality/inequality with boolean operands, got {lhs_unit} and {rhs_unit}.",
        }
    return {
        "status": "unknown",
        "severity": "warning",
        "message": f"Constraint units are incompatible or unsupported: {lhs_unit} vs {rhs_unit}.",
    }


def _constraint_summary(checks):
    passed = sum(1 for check in checks if check.get("severity") == "pass")
    failed_checks = [check for check in checks if check.get("severity") == "fail"]
    unknown = sum(1 for check in checks if check.get("severity") == "unknown")
    if failed_checks:
        overall_pass = False
    elif checks and unknown == 0:
        overall_pass = True
    else:
        overall_pass = None

    margin_sensitive = [
        {
            "name": check.get("name"),
            "boolean_output": check.get("boolean_output"),
            "lhs": check.get("lhs"),
            "expression": check.get("expression"),
            "margin": check.get("margin"),
            "margin_percent": check.get("margin_percent"),
            "message": check.get("message"),
        }
        for check in checks
        if check.get("margin_sensitive")
    ]

    notes = []
    if margin_sensitive:
        notes.append("One or more passing constraints have <=10% positive margin.")
    if unknown:
        notes.append("One or more constraints could not be evaluated deterministically.")

    return {
        "total": len(checks),
        "passed": passed,
        "failed": len(failed_checks),
        "unknown": unknown,
        "overall_pass": overall_pass,
        "blocking_failures": [
            {
                "name": check.get("name"),
                "boolean_output": check.get("boolean_output"),
                "lhs": check.get("lhs"),
                "expression": check.get("expression"),
                "margin": check.get("margin"),
                "margin_percent": check.get("margin_percent"),
                "message": check.get("message"),
            }
            for check in failed_checks
        ],
        "margin_sensitive_passes": margin_sensitive,
        "notes": notes,
    }


def _constraints_requested(mcm_request):
    constraints = mcm_request.get("constraints") if isinstance(mcm_request, dict) else None
    return isinstance(constraints, list) and bool(constraints)


def _is_constraint_policy_note(text):
    lowered = str(text).lower()
    policy_markers = [
        "if a constraint cannot be evaluated",
        "mark it as unknown rather than assuming pass",
        "marked unknown rather than assumed to pass",
        "rather than assuming pass",
        "rather than assumed to pass",
        "margin-sensitive if",
        "pass is margin-sensitive",
    ]
    return any(marker in lowered for marker in policy_markers) or _is_qualitative_constraint_text(text)


def _is_qualitative_constraint_text(text):
    stripped = str(text).strip()
    lowered = stripped.lower()
    leading_verbs = ("use ", "do ", "treat ", "assume ", "preserve ")
    qualitative_markers = (
        "do not use",
        "do not invent",
        "supplied glycol properties",
        "pure water properties",
        "temperature difference in k",
        "numerically equal to degc difference",
        "alternate properties",
    )
    return lowered.startswith(leading_verbs) or any(marker in lowered for marker in qualitative_markers)


def _constraint_operands_are_known(lhs, rhs, env):
    lhs_value = _resolve_constraint_arithmetic_expression(str(lhs), env, {}, None)
    if lhs not in env and lhs_value is None:
        return False
    if _coerce_number(rhs) is not None:
        return True
    if rhs in env:
        return True
    rhs_value = _resolve_constraint_arithmetic_expression(str(rhs), env, {}, None)
    return rhs_value is not None and rhs_value[2] is None


def _constraint_policy_notes(mcm_request):
    constraints = mcm_request.get("constraints") if isinstance(mcm_request, dict) else None
    if not isinstance(constraints, list):
        return []
    return [
        constraint for constraint in constraints
        if isinstance(constraint, str) and _is_missing_data_policy_note(constraint)
    ]


def _qualitative_constraint_notes(mcm_request):
    constraints = mcm_request.get("constraints") if isinstance(mcm_request, dict) else None
    if not isinstance(constraints, list):
        return []
    return [
        constraint for constraint in constraints
        if isinstance(constraint, str) and _is_qualitative_constraint_text(constraint)
    ]


def _margin_sensitive_rule_notes(mcm_request):
    constraints = mcm_request.get("constraints") if isinstance(mcm_request, dict) else None
    if not isinstance(constraints, list):
        return []
    return [
        constraint for constraint in constraints
        if isinstance(constraint, str) and _is_margin_sensitive_rule_text(constraint)
    ]


def _is_missing_data_policy_note(text):
    lowered = str(text).lower()
    return (
        "constraint cannot be evaluated" in lowered
        or "missing required input data" in lowered
        or "rather than assumed to pass" in lowered
        or "rather than assuming pass" in lowered
    )


def _is_margin_sensitive_rule_text(text):
    lowered = str(text).lower()
    return "margin-sensitive if" in lowered or "pass is margin-sensitive" in lowered


def _comparator_symbol(node):
    for symbol, op_type in ALLOWED_COMPARATOR_SYMBOLS.items():
        if isinstance(node, op_type):
            return symbol
    return None


def _simple_constraint_operand(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant):
        return node.value
    return ast.unparse(node) if hasattr(ast, "unparse") else None


def _constraint_expression(lhs, comparator, rhs):
    if lhs is None or comparator is None or rhs is None:
        return None
    return f"{lhs} {comparator} {rhs}"


def _constraint_name_from_lhs(lhs):
    return f"{lhs}_constraint" if lhs else "constraint"


def _attach_sensitivity_result(mcm_request, baseline_result):
    sensitivity = parse_sensitivity_request(mcm_request)
    if not sensitivity.get("enabled"):
        return baseline_result

    analysis = run_sensitivity_analysis(mcm_request, baseline_result, sensitivity)
    baseline_result["sensitivity_analysis"] = analysis
    if analysis.get("diagnostics"):
        baseline_result.setdefault("diagnostics", []).extend(analysis["diagnostics"])
    return baseline_result


def parse_sensitivity_request(mcm_request) -> dict:
    if not isinstance(mcm_request, dict):
        return {"enabled": False}

    raw = mcm_request.get("sensitivity")
    style = "sensitivity"
    if not isinstance(raw, dict):
        raw = mcm_request.get("sensitivity_analysis")
        style = "sensitivity_analysis"
    if not isinstance(raw, dict) or raw.get("enabled") is not True:
        return {"enabled": False}

    diagnostics = []
    default_percent = _coerce_number(raw.get("default_percent"))
    if default_percent is None:
        default_percent = _coerce_number(raw.get("percent"))

    explicit_default = default_percent is not None
    if default_percent is None:
        default_percent = 25.0
        diagnostics.append("Default +/-25% sensitivity was used because no sensitivity range was provided.")

    outputs = raw.get("outputs")
    if not isinstance(outputs, list):
        outputs = []
    outputs = [str(name) for name in outputs]

    variables = {}
    if isinstance(raw.get("variables"), dict):
        for name, spec in raw["variables"].items():
            if isinstance(spec, dict):
                percent = _coerce_number(spec.get("percent"))
                absolute = _coerce_number(spec.get("absolute"))
            else:
                percent = _coerce_number(spec)
                absolute = None
            if percent is not None:
                variables[str(name)] = {"type": "percent", "amount": percent}
            elif absolute is not None:
                variables[str(name)] = {"type": "absolute", "amount": absolute}
            else:
                variables[str(name)] = {"type": "percent", "amount": default_percent}
                if explicit_default:
                    diagnostics.append(f"Default +/-{default_percent:g}% sensitivity was used for {name}.")

    input_names = raw.get("inputs")
    if isinstance(input_names, list):
        for name in input_names:
            variables.setdefault(str(name), {"type": "percent", "amount": default_percent})

    return {
        "enabled": True,
        "style": style,
        "default_percent": default_percent,
        "variables": variables,
        "outputs": outputs,
        "diagnostics": diagnostics,
    }


def run_sensitivity_analysis(mcm_request, baseline_result, sensitivity) -> dict:
    diagnostics = list(sensitivity.get("diagnostics", []))
    baseline_outputs = baseline_result.get("outputs") if isinstance(baseline_result, dict) else {}
    if not isinstance(baseline_outputs, dict):
        baseline_outputs = {}

    requested_outputs = sensitivity.get("outputs") or list(baseline_outputs.keys())
    available_outputs = [name for name in requested_outputs if name in baseline_outputs]
    missing_outputs = [name for name in requested_outputs if name not in baseline_outputs]

    if baseline_result.get("status") not in {"computed", "partial"}:
        diagnostics.append(f"Sensitivity skipped because baseline status was {baseline_result.get('status')}.")
        return _sensitivity_skipped_result(sensitivity, baseline_outputs, diagnostics, missing_outputs)

    if missing_outputs:
        diagnostics.append("Sensitivity skipped because requested baseline outputs were missing: " + ", ".join(missing_outputs))
        return _sensitivity_skipped_result(sensitivity, baseline_outputs, diagnostics, missing_outputs)

    inputs = _extract_inputs(mcm_request)
    variables = dict(sensitivity.get("variables") or {})
    if not variables:
        variables = _default_sensitivity_variables(mcm_request, inputs, sensitivity.get("default_percent", 25.0))
        if variables:
            diagnostics.append("Sensitivity inputs were selected from numeric document-derived variables.")

    if not variables:
        diagnostics.append("Sensitivity skipped because no numeric sensitivity inputs were available.")
        return _sensitivity_skipped_result(sensitivity, baseline_outputs, diagnostics, missing_outputs)

    cases = []
    for input_name, spec in variables.items():
        if input_name not in inputs:
            diagnostics.append(f"Sensitivity input skipped because it has no numeric baseline value: {input_name}")
            continue
        case = _run_sensitivity_case(mcm_request, input_name, inputs[input_name], spec, available_outputs, baseline_outputs)
        cases.append(case)

    if not cases:
        diagnostics.append("Sensitivity skipped because no perturbation cases could be evaluated.")
        return _sensitivity_skipped_result(sensitivity, baseline_outputs, diagnostics, missing_outputs)

    return {
        "enabled": True,
        "baseline_outputs": _select_output_values(baseline_outputs, available_outputs),
        "cases": cases,
        "summary": summarize_sensitivity_results(cases),
        "diagnostics": diagnostics,
    }


def _sensitivity_skipped_result(sensitivity, baseline_outputs, diagnostics, missing_outputs=None):
    return {
        "enabled": False,
        "baseline_outputs": baseline_outputs,
        "cases": [],
        "summary": {
            "most_sensitive_output": None,
            "largest_relative_change_percent": None,
            "pass_fail_flips": [],
            "notes": ["Sensitivity analysis was skipped."],
        },
        "diagnostics": diagnostics,
        "missing_outputs": missing_outputs or [],
    }


def _default_sensitivity_variables(mcm_request, inputs, default_percent):
    variables = mcm_request.get("variables") if isinstance(mcm_request, dict) else None
    if not isinstance(variables, dict):
        return {}

    selected = {}
    for name, meta in variables.items():
        if str(name) not in inputs or not isinstance(meta, dict):
            continue
        if meta.get("source") != "document-derived":
            continue
        if meta.get("source") == "computed":
            continue
        if normalize_unit(meta.get("unit")) == "boolean":
            continue
        selected[str(name)] = {"type": "percent", "amount": default_percent}
    return selected


def _run_sensitivity_case(mcm_request, input_name, baseline_value, spec, outputs, baseline_outputs):
    perturbation_type = spec.get("type", "percent")
    amount = _coerce_number(spec.get("amount"))
    if amount is None:
        amount = 25.0
        perturbation_type = "percent"

    low_value, high_value = perturb_numeric_input(baseline_value, perturbation_type, amount)
    low_request = clone_request_with_perturbation(mcm_request, input_name, low_value)
    high_request = clone_request_with_perturbation(mcm_request, input_name, high_value)

    low_result = _process_without_sensitivity(low_request)
    high_result = _process_without_sensitivity(high_request)
    low_outputs = _select_output_values(low_result.get("outputs", {}), outputs)
    high_outputs = _select_output_values(high_result.get("outputs", {}), outputs)
    deltas, flips = _sensitivity_output_deltas(baseline_outputs, low_result.get("outputs", {}), high_result.get("outputs", {}), outputs)

    return {
        "varied_input": input_name,
        "perturbation_type": perturbation_type,
        "perturbation_amount": amount,
        "baseline_input_value": baseline_value,
        "low_input_value": low_value,
        "high_input_value": high_value,
        "low_status": low_result.get("status"),
        "high_status": high_result.get("status"),
        "low_outputs": low_outputs,
        "high_outputs": high_outputs,
        "output_deltas": deltas,
        "pass_fail_flips": flips,
        "diagnostics": {
            "low": low_result.get("diagnostics", []),
            "high": high_result.get("diagnostics", []),
        },
    }


def perturb_numeric_input(value, perturbation_type, amount):
    if perturbation_type == "absolute":
        return value - amount, value + amount
    percent = amount / 100
    return value * (1 - percent), value * (1 + percent)


def clone_request_with_perturbation(mcm_request, input_name, value):
    clone = copy.deepcopy(mcm_request)
    clone.pop("sensitivity", None)
    clone.pop("sensitivity_analysis", None)

    inputs = clone.get("inputs")
    if isinstance(inputs, dict) and input_name in inputs:
        inputs[input_name] = value

    variables = clone.get("variables")
    if isinstance(variables, dict) and isinstance(variables.get(input_name), dict):
        variables[input_name]["value"] = value
    elif isinstance(inputs, dict):
        inputs[input_name] = value
    else:
        clone["inputs"] = {input_name: value}

    return clone


def _select_output_values(outputs, names):
    selected = {}
    if not isinstance(outputs, dict):
        return selected
    for name in names:
        if name in outputs:
            output = outputs[name]
            if isinstance(output, dict):
                selected[name] = {
                    "value": output.get("value"),
                    "unit": output.get("unit"),
                    "source": output.get("source"),
                }
            else:
                selected[name] = {"value": output, "unit": None, "source": None}
    return selected


def _sensitivity_output_deltas(baseline_outputs, low_outputs, high_outputs, names):
    deltas = {}
    flips = []
    for name in names:
        baseline = _output_value(baseline_outputs.get(name))
        low = _output_value(low_outputs.get(name))
        high = _output_value(high_outputs.get(name))
        unit = _output_unit(baseline_outputs.get(name))

        if isinstance(baseline, bool):
            low_changed = isinstance(low, bool) and low != baseline
            high_changed = isinstance(high, bool) and high != baseline
            deltas[name] = {
                "type": "boolean",
                "baseline": baseline,
                "low": low,
                "high": high,
                "low_changed": low_changed,
                "high_changed": high_changed,
                "unit": unit,
            }
            if low_changed:
                flips.append({"output": name, "case": "low", "baseline": baseline, "perturbed": low})
            if high_changed:
                flips.append({"output": name, "case": "high", "baseline": baseline, "perturbed": high})
        elif _is_number(baseline):
            low_delta = low - baseline if _is_number(low) else None
            high_delta = high - baseline if _is_number(high) else None
            deltas[name] = {
                "type": "numeric",
                "baseline": baseline,
                "low": low,
                "high": high,
                "low_delta": low_delta,
                "high_delta": high_delta,
                "low_delta_percent": _percent_delta(low_delta, baseline),
                "high_delta_percent": _percent_delta(high_delta, baseline),
                "unit": unit,
            }
    return deltas, flips


def summarize_sensitivity_results(cases):
    largest = None
    pass_fail_flips = []
    for case in cases:
        pass_fail_flips.extend(
            dict(flip, varied_input=case.get("varied_input"))
            for flip in case.get("pass_fail_flips", [])
        )
        for output_name, delta in case.get("output_deltas", {}).items():
            if delta.get("type") != "numeric":
                continue
            for key in ("low_delta_percent", "high_delta_percent"):
                value = delta.get(key)
                if value is None:
                    continue
                magnitude = abs(value)
                if largest is None or magnitude > largest["magnitude"]:
                    largest = {
                        "output": output_name,
                        "magnitude": magnitude,
                        "signed": value,
                        "varied_input": case.get("varied_input"),
                    }

    notes = []
    if pass_fail_flips:
        notes.append("One or more boolean outputs changed under perturbation.")
    else:
        notes.append("No requested boolean output changed under perturbation.")

    return {
        "most_sensitive_output": largest.get("output") if largest else None,
        "largest_relative_change_percent": largest.get("magnitude") if largest else None,
        "most_sensitive_input": largest.get("varied_input") if largest else None,
        "pass_fail_flips": pass_fail_flips,
        "notes": notes,
    }


def _output_value(output):
    if isinstance(output, dict):
        return output.get("value")
    return output


def _output_unit(output):
    if isinstance(output, dict):
        return output.get("unit")
    return None


def _attach_run_health_summary(mcm_request, result):
    result["mcm_run_health"] = summarize_run_health(result, mcm_required=True)
    categories = result["mcm_run_health"].get("diagnostic_categories") or []
    if categories:
        result["diagnostic_categories"] = categories
    return result


def summarize_run_health(mcm_result=None, mcm_required=True):
    """
    Build a compact, machine-readable EAS/MCM health summary.

    This is intentionally read-only. It does not change computed outputs,
    validation decisions, or status policy; it only summarizes an existing
    MCM result for UI/reporting consumers.
    """

    result = mcm_result if isinstance(mcm_result, dict) else {}
    outputs = result.get("outputs") if isinstance(result.get("outputs"), dict) else {}
    status = str(result.get("status") or ("unknown" if mcm_required else "not_required"))
    executed_count = _count_result_items(result.get("equations_executed"))
    skipped_count = _count_result_items(result.get("equations_skipped"))
    missing_variables_count = _count_result_items(result.get("missing_variables"))
    missing_outputs_count = _count_result_items(result.get("missing_outputs"))
    invalid_unit_outputs_count = _count_result_items(result.get("invalid_unit_outputs"))
    unit_warnings_count = _count_result_items(result.get("unit_warnings"))

    constraint_summary = _health_constraint_summary(result, outputs)
    screening_summary = _health_screening_summary(result, outputs, constraint_summary)
    diagnostic_summary = _health_diagnostic_summary(result, outputs)
    selection_summary = _health_selection_summary(result, outputs, constraint_summary)
    diagnostic_categories = _health_diagnostic_categories(
        result,
        status,
        mcm_required,
        skipped_count,
        missing_variables_count,
        missing_outputs_count,
        invalid_unit_outputs_count,
    )
    blocking_failures = (
        []
        if not mcm_required and status == "not_required"
        else _health_blocking_failures(
            result,
            constraint_summary,
            diagnostic_categories,
            screening_summary,
            diagnostic_summary,
            selection_summary,
        )
    )
    recommended_option_name = _health_output_value(outputs, _health_recommended_name_candidates())
    recommended_concept_name = _health_output_value(outputs, _health_recommended_concept_name_candidates())
    recommended_name = recommended_option_name or recommended_concept_name
    overall_recommendation_status = _health_recommendation_status(outputs, recommended_name)
    readiness_label = _health_readiness_label(
        status,
        mcm_required,
        skipped_count,
        missing_variables_count,
        missing_outputs_count,
        invalid_unit_outputs_count,
        unit_warnings_count,
        constraint_summary.get("failed", 0),
        constraint_summary.get("unknown", 0),
    )
    computed_clean = (
        status == "computed"
        and skipped_count == 0
        and missing_variables_count == 0
        and missing_outputs_count == 0
        and invalid_unit_outputs_count == 0
        and constraint_summary.get("failed", 0) == 0
        and constraint_summary.get("unknown", 0) == 0
        and not blocking_failures
    )

    return {
        "mcm_required": bool(mcm_required),
        "mcm_status": status,
        "mcm_computed_ok": computed_clean,
        "equations_executed_count": executed_count,
        "equations_skipped_count": skipped_count,
        "missing_variables_count": missing_variables_count,
        "missing_outputs_count": missing_outputs_count,
        "invalid_unit_outputs_count": invalid_unit_outputs_count,
        "unit_warnings_count": unit_warnings_count,
        "constraint_total": constraint_summary.get("total", 0),
        "constraint_passed": constraint_summary.get("passed", 0),
        "constraint_failed": constraint_summary.get("failed", 0),
        "constraint_unknown": constraint_summary.get("unknown", 0),
        "overall_release_status": _health_output_value(outputs, _health_release_status_names()),
        "overall_recommendation_status": overall_recommendation_status,
        "recommended_option_name": recommended_option_name,
        "recommended_concept_name": recommended_concept_name,
        "selected_configuration_label": _health_output_value(outputs, (
            "selected_configuration_label",
            "recommended_configuration_label",
        )),
        "selected_config_label": _health_output_value(outputs, ("selected_config_label",)),
        "selected_solution": selection_summary.get("selected_solution")
        or screening_summary.get("selected_solution")
        or _health_output_value(outputs, _health_selected_solution_candidates()),
        "selection_status": selection_summary.get("selection_status"),
        "selected_solution_pass": (
            selection_summary.get("selected_solution_pass")
            if selection_summary.get("selected_solution_pass") is not None
            else screening_summary.get("selected_solution_pass")
        ),
        "selected_conductor_AWG": selection_summary.get("selected_conductor_AWG"),
        "selected_power_supply_A": selection_summary.get("selected_power_supply_A"),
        "selected_fuse_A": selection_summary.get("selected_fuse_A"),
        "rejected_option_failures": (
            selection_summary.get("rejected_option_failures")
            or screening_summary.get("rejected_option_failures")
        ),
        "rejected_alternative_failures": (
            selection_summary.get("rejected_alternative_failures")
            or screening_summary.get("rejected_option_failures")
        ),
        "selected_candidate_failures": (
            selection_summary.get("selected_candidate_failures")
            if selection_summary
            else screening_summary.get("selected_candidate_failures")
        ),
        "selected_configuration_key": selection_summary.get("selected_configuration_key")
        or screening_summary.get("selected_configuration_key")
        or _health_output_value(outputs, ("selected_configuration_key", "selected_config_key")),
        "selected_candidate_key": selection_summary.get("selected_candidate_key")
        or screening_summary.get("selected_candidate_key"),
        "viable_candidates": screening_summary.get("viable_candidates"),
        "viable_non_selected_alternatives": (
            selection_summary.get("viable_non_selected_alternatives")
            or screening_summary.get("viable_non_selected_alternatives")
        ),
        "selected_option_margin_sensitive_warnings": selection_summary.get("selected_option_margin_sensitive_warnings"),
        "blocking_failures": blocking_failures,
        "screening_status": screening_summary.get("screening_status"),
        "viable_candidates_count": screening_summary.get("viable_candidates_count"),
        "rejected_candidates_count": screening_summary.get("rejected_candidates_count"),
        "selected_candidate_all_criteria_pass": screening_summary.get("selected_candidate_all_criteria_pass"),
        "rejected_candidate_failures": screening_summary.get("rejected_candidate_failures"),
        "diagnostic_status": diagnostic_summary.get("diagnostic_status"),
        "supported_root_cause_flags": diagnostic_summary.get("supported_root_cause_flags"),
        "eliminated_cause_flags": diagnostic_summary.get("eliminated_cause_flags"),
        "unresolved_cause_flags": diagnostic_summary.get("unresolved_cause_flags"),
        "primary_root_cause": diagnostic_summary.get("primary_root_cause"),
        "diagnostic_evidence_count": diagnostic_summary.get("diagnostic_evidence_count"),
        "diagnostic_categories": diagnostic_categories,
        "readiness_label": readiness_label,
    }


def _count_result_items(value):
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return len(value)
    if value in (None, ""):
        return 0
    return 1


def _health_constraint_summary(result, outputs):
    checks = result.get("constraint_checks") if isinstance(result, dict) else None
    summary = checks.get("summary") if isinstance(checks, dict) else None
    if isinstance(summary, dict) and summary.get("total", 0):
        return {
            "total": int(summary.get("total") or 0),
            "passed": int(summary.get("passed") or 0),
            "failed": int(summary.get("failed") or 0),
            "unknown": int(summary.get("unknown") or 0),
            "blocking_failures": summary.get("blocking_failures") or [],
            "margin_sensitive_passes": summary.get("margin_sensitive_passes") or [],
        }

    criteria = []
    for name, output in outputs.items():
        index = _criterion_output_index(name)
        if index is None:
            continue
        value = output.get("value") if isinstance(output, dict) else output
        status_value = _constraint_status_from_output(value)
        if status_value.get("recognized"):
            criteria.append((name, status_value))

    failed = [
        {"name": name, "message": "Criterion output evaluated to FAIL."}
        for name, output in outputs.items()
        if _criterion_output_index(name) is not None
        and _constraint_status_from_output(output.get("value") if isinstance(output, dict) else output).get("passes") is False
    ]
    passed = sum(1 for _, item in criteria if item.get("passes") is True)
    unknown = sum(1 for _, item in criteria if item.get("passes") is None)
    return {
        "total": len(criteria),
        "passed": passed,
        "failed": len(failed),
        "unknown": unknown,
        "blocking_failures": failed,
        "margin_sensitive_passes": [],
    }


def _health_screening_summary(result, outputs, constraint_summary):
    mode = normalize_eas_mode(result.get("mode") if isinstance(result, dict) else None)
    if mode not in {"suggest-improvements", "explore-novel-solution"}:
        return {}

    recommended_name = _health_output_value(outputs, _health_recommended_name_candidates())
    candidate_summary = _screening_candidate_summary(outputs, recommended_name)
    if is_missing_value(recommended_name):
        recommended_name = candidate_summary.get("selected_solution")
    recommendation_status = str(_health_recommendation_status(outputs, recommended_name) or "").strip().upper()
    viable_count = _screening_viable_candidate_count(outputs)
    if viable_count == 0 and candidate_summary.get("viable_candidates"):
        viable_count = len(candidate_summary.get("viable_candidates") or [])
    rejected_count = _screening_rejected_candidate_count(outputs)
    if rejected_count == 0 and candidate_summary.get("rejected_option_failures"):
        rejected_count = len(candidate_summary.get("rejected_option_failures") or [])
    has_viable_recommendation = bool(recommended_name) or recommendation_status == "PASS" or viable_count > 0
    selected_prefixes = _screening_selected_prefixes(recommended_name)
    selected_all_pass = (
        candidate_summary.get("selected_solution_pass")
        if candidate_summary.get("selected_solution_pass") is not None
        else _screening_selected_candidate_all_criteria_pass(outputs, selected_prefixes, recommendation_status)
    )
    fallback_rejected_failures, fallback_selected_failures = _split_screening_constraint_failures(
        constraint_summary.get("blocking_failures") or [],
        selected_prefixes,
    )
    grouped_rejected_failures = candidate_summary.get("rejected_option_failures") or []
    rejected_candidate_failures = fallback_rejected_failures or grouped_rejected_failures
    rejected_option_failures = grouped_rejected_failures or fallback_rejected_failures
    selected_failures = candidate_summary.get("selected_candidate_failures") or fallback_selected_failures

    if has_viable_recommendation and selected_failures:
        screening_status = "selected_candidate_failed_criteria"
    elif has_viable_recommendation:
        screening_status = "screening_pass"
    elif recommendation_status == "FAIL" or rejected_count > 0 or constraint_summary.get("failed", 0):
        screening_status = "no_viable_candidate"
    else:
        screening_status = "screening_unknown"

    return {
        "screening_status": screening_status,
        "viable_candidates": candidate_summary.get("viable_candidates") or [],
        "viable_candidates_count": viable_count,
        "rejected_candidates_count": rejected_count,
        "recommended_option_name": recommended_name,
        "selected_solution": candidate_summary.get("selected_solution") or recommended_name,
        "selected_solution_pass": candidate_summary.get("selected_solution_pass"),
        "selected_candidate_key": candidate_summary.get("selected_candidate_key"),
        "selected_candidate_all_criteria_pass": selected_all_pass,
        "rejected_candidate_failures": rejected_candidate_failures,
        "rejected_option_failures": rejected_option_failures,
        "selected_candidate_failures": selected_failures,
        "viable_non_selected_alternatives": candidate_summary.get("viable_non_selected_alternatives") or [],
    }


def _screening_viable_candidate_count(outputs):
    explicit = _screening_explicit_count(outputs, (
        "total_viable_candidates_count",
        "total_viable_concepts_count",
        "total_viable_options_count",
        "viable_candidates_count",
        "viable_concepts_count",
        "viable_options_count",
        "passed_candidates_count",
        "passed_concepts_count",
        "passed_options_count",
    ))
    if explicit is not None:
        return explicit
    return sum(1 for _, value in _screening_viability_outputs(outputs) if value is True)


def _screening_rejected_candidate_count(outputs):
    explicit = _screening_explicit_count(outputs, (
        "rejected_candidates_count",
        "rejected_concepts_count",
        "rejected_options_count",
        "non_viable_candidates_count",
        "non_viable_concepts_count",
        "non_viable_options_count",
        "failed_candidates_count",
        "failed_concepts_count",
        "failed_options_count",
    ))
    if explicit is not None:
        return explicit
    return sum(1 for _, value in _screening_viability_outputs(outputs) if value is False)


def _screening_explicit_count(outputs, candidates):
    value = _health_output_value(outputs, candidates)
    if value in (None, ""):
        return None
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def _screening_viability_outputs(outputs):
    items = []
    for name, output in outputs.items():
        lowered = str(name or "").strip().lower()
        if "count" in lowered:
            continue
        if not (
            lowered.endswith("_is_viable")
            or lowered.endswith("_viable")
            or "_is_viable_" in lowered
            or lowered.endswith("_overall_option_pass")
            or lowered.endswith("_overall_candidate_pass")
            or lowered.endswith("_overall_concept_pass")
            or lowered.endswith("_overall_criteria_pass")
            or lowered.endswith("_all_criteria_pass")
        ):
            continue
        value = _output_value(output)
        if isinstance(value, bool):
            items.append((lowered, value))
    return items


def _screening_candidate_summary(outputs, recommended_name=None):
    candidates = {}
    for name, output in outputs.items():
        identity = _screening_candidate_identity_from_name(name)
        if not identity:
            continue
        prefix = identity["prefix"]
        candidate = candidates.setdefault(prefix, {
            "prefix": prefix,
            "kind": identity["kind"],
            "key": identity["key"],
            "label": _screening_candidate_label(identity),
            "criteria": [],
            "metrics": [],
            "overall_pass": None,
            "overall_field": None,
        })
        value = _output_value(output)
        status = _constraint_status_from_output(value)
        if _screening_candidate_overall_pass_name(name) and status.get("recognized"):
            candidate["overall_pass"] = status.get("passes")
            candidate["overall_field"] = str(name)
        if _screening_candidate_criterion_name(name) and status.get("recognized"):
            criterion_label = _screening_criterion_label(name)
            candidate["criteria"].append({
                "name": str(name),
                "criterion": criterion_label,
                "passes": status.get("passes"),
            })
        metric = _screening_candidate_metric_value(name, value)
        if metric is not None:
            candidate["metrics"].append({
                "name": str(name),
                "value": metric,
                "unit": _output_unit(output),
            })

    if not candidates:
        return {}

    for candidate in candidates.values():
        failed_criteria = [
            item
            for item in candidate["criteria"]
            if item.get("passes") is False
        ]
        unknown_criteria = [
            item
            for item in candidate["criteria"]
            if item.get("passes") is None
        ]
        if candidate["overall_pass"] is None and candidate["criteria"]:
            if failed_criteria:
                candidate["overall_pass"] = False
            elif unknown_criteria:
                candidate["overall_pass"] = None
            else:
                candidate["overall_pass"] = True
        candidate["failed_criteria"] = failed_criteria

    selected = _screening_selected_candidate(candidates, recommended_name)
    selected_prefix = selected.get("prefix") if selected else None
    viable_candidates = [
        _screening_candidate_item(candidate)
        for candidate in candidates.values()
        if candidate.get("overall_pass") is True
    ]
    rejected_failures = []
    viable_non_selected = []
    for candidate in candidates.values():
        if candidate.get("prefix") == selected_prefix:
            continue
        if candidate.get("overall_pass") is True:
            viable_non_selected.append(_screening_candidate_item(candidate))
            continue
        if candidate.get("overall_pass") is False or candidate.get("failed_criteria"):
            rejected_failures.append(_screening_rejected_candidate_item(candidate))

    selected_solution = selected.get("label") if selected else None
    selected_pass = selected.get("overall_pass") if selected else None
    selected_failures = []
    if selected and selected.get("overall_pass") is False:
        selected_failures.append(_screening_rejected_candidate_item(selected))

    return {
        "selected_solution": selected_solution,
        "selected_solution_pass": selected_pass,
        "selected_candidate_key": _screening_display_candidate_key(selected) if selected else None,
        "viable_candidates": viable_candidates,
        "rejected_option_failures": rejected_failures,
        "selected_candidate_failures": selected_failures,
        "viable_non_selected_alternatives": viable_non_selected,
    }


def _screening_candidate_identity_from_name(name):
    lowered = str(name or "").strip().lower()
    if not lowered:
        return None
    if lowered == "baseline" or lowered.startswith("baseline_"):
        return {"prefix": "baseline", "kind": "baseline", "key": "baseline"}
    match = re.match(r"^(option|concept|candidate|alternative)_([a-z0-9]+)(?:_|$)", lowered)
    if not match:
        return None
    return {
        "prefix": f"{match.group(1)}_{match.group(2)}",
        "kind": match.group(1),
        "key": match.group(2),
    }


def _screening_candidate_label(identity):
    if not identity:
        return None
    kind = str(identity.get("kind") or "").strip().lower()
    key = str(identity.get("key") or "").strip()
    if kind == "baseline":
        return "Baseline"
    if not kind or not key:
        return None
    return f"{kind.title()} {_screening_display_key(key)}"


def _screening_display_key(key):
    text = str(key or "").strip()
    return text.upper() if len(text) == 1 and text.isalpha() else text.replace("_", " ").title()


def _screening_candidate_overall_pass_name(name):
    lowered = str(name or "").strip().lower()
    return (
        lowered.endswith("_is_viable")
        or lowered.endswith("_viable")
        or lowered.endswith("_overall_option_pass")
        or lowered.endswith("_overall_candidate_pass")
        or lowered.endswith("_overall_concept_pass")
        or lowered.endswith("_overall_criteria_pass")
        or lowered.endswith("_all_criteria_pass")
    )


def _screening_candidate_criterion_name(name):
    lowered = str(name or "").strip().lower()
    if _screening_candidate_overall_pass_name(lowered):
        return False
    return _criterion_output_index(lowered) is not None and (
        "pass" in lowered or "criterion" in lowered or "criteria" in lowered
    )


def _screening_criterion_label(name):
    index = _criterion_output_index(name)
    return f"C{index}" if index is not None else _selection_humanize_name(name)


def _screening_candidate_metric_value(name, value):
    lowered = str(name or "").strip().lower()
    if not any(token in lowered for token in ("score", "cost")):
        return None
    if any(token in lowered for token in ("pass", "status", "count")):
        return None
    return _coerce_number(value)


def _screening_selected_candidate(candidates, recommended_name=None):
    recommended_identity = _screening_candidate_identity_from_label(recommended_name)
    if recommended_identity:
        for candidate in candidates.values():
            if _screening_candidate_matches_identity(candidate, recommended_identity):
                return candidate
    viable = [candidate for candidate in candidates.values() if candidate.get("overall_pass") is True]
    if not viable:
        return None
    scored = [
        (candidate["metrics"][0]["value"], candidate)
        for candidate in viable
        if candidate.get("metrics")
    ]
    if scored:
        return min(scored, key=lambda item: item[0])[1]
    return viable[0]


def _screening_candidate_identity_from_label(label):
    if is_missing_value(label):
        return None
    tokens = _name_tokens(label)
    if not tokens:
        return None
    if tokens[0] == "baseline":
        return {"kind": "baseline", "key": "baseline"}
    if tokens[0] in {"option", "concept", "candidate", "alternative"} and len(tokens) >= 2:
        return {"kind": tokens[0], "key": tokens[1]}
    if len(tokens[0]) == 1 and tokens[0].isalpha():
        return {"kind": None, "key": tokens[0]}
    return None


def _screening_candidate_matches_identity(candidate, identity):
    if not candidate or not identity:
        return False
    candidate_kind = str(candidate.get("kind") or "").lower()
    candidate_key = str(candidate.get("key") or "").lower()
    identity_kind = str(identity.get("kind") or "").lower()
    identity_key = str(identity.get("key") or "").lower()
    if identity_kind and candidate_kind != identity_kind:
        if not (identity_kind == "baseline" and candidate_kind == "baseline"):
            return False
    return candidate_key == identity_key


def _screening_candidate_item(candidate):
    if not candidate:
        return {}
    return {
        "candidate_kind": candidate.get("kind"),
        "candidate_key": candidate.get("key"),
        "candidate_label": candidate.get("label"),
        "selected": False,
        "metrics": candidate.get("metrics") or [],
    }


def _screening_rejected_candidate_item(candidate):
    failed = candidate.get("failed_criteria") or []
    reasons = []
    failed_fields = []
    for item in failed:
        field = item.get("name")
        reason = item.get("criterion")
        if field:
            failed_fields.append(field)
        if reason and reason not in reasons:
            reasons.append(reason)
    if not reasons and candidate.get("overall_pass") is False:
        reasons.append("overall criteria")
    return {
        "candidate_kind": candidate.get("kind"),
        "candidate_key": candidate.get("key"),
        "candidate_label": candidate.get("label"),
        "failed_fields": failed_fields or ([candidate.get("overall_field")] if candidate.get("overall_field") else []),
        "reasons": reasons,
    }


def _screening_display_candidate_key(candidate):
    if not candidate:
        return None
    if candidate.get("kind") == "baseline":
        return "Baseline"
    return _screening_display_key(candidate.get("key"))


def _screening_selected_prefixes(recommended_name):
    text = str(recommended_name or "").strip().lower()
    if not text:
        return set()
    tokens = [token for token in re.split(r"[_\W]+", text) if token]
    if not tokens:
        return set()
    if tokens[0] == "baseline":
        return {"baseline"}
    if tokens[0] in {"candidate", "concept", "option"} and len(tokens) >= 2:
        return {f"{tokens[0]}_{tokens[1]}"}
    if len(tokens[0]) == 1 and tokens[0].isalpha():
        letter = tokens[0]
        return {f"candidate_{letter}", f"concept_{letter}", f"option_{letter}"}
    return set()


def _split_screening_constraint_failures(failures, selected_prefixes):
    rejected = []
    selected = []
    for item in failures:
        prefix = _screening_failure_prefix(item)
        if selected_prefixes and prefix in selected_prefixes:
            selected.append(item)
        else:
            rejected.append(item)
    return rejected, selected


def _screening_failure_prefix(item):
    if isinstance(item, dict):
        text = item.get("name") or item.get("item") or item.get("expression") or ""
    else:
        text = str(item)
    lowered = str(text or "").strip().lower()
    tokens = [token for token in re.split(r"[_\W]+", lowered) if token]
    if tokens and tokens[0] == "baseline":
        return "baseline"
    if len(tokens) >= 2 and tokens[0] in {"candidate", "concept", "option"}:
        return f"{tokens[0]}_{tokens[1]}"
    return ""


def _screening_selected_candidate_all_criteria_pass(outputs, selected_prefixes, recommendation_status):
    if not selected_prefixes:
        return True if recommendation_status == "PASS" else None
    found = False
    unknown = False
    for name, output in outputs.items():
        prefix = _screening_failure_prefix({"name": name})
        if prefix not in selected_prefixes:
            continue
        lowered = str(name or "").strip().lower()
        if not ("pass" in lowered or "viable" in lowered or "status" in lowered):
            continue
        status = _constraint_status_from_output(_output_value(output))
        if not status.get("recognized"):
            continue
        found = True
        if status.get("passes") is False:
            return False
        if status.get("passes") is None:
            unknown = True
    if found:
        return None if unknown else True
    return True if recommendation_status == "PASS" else None


def _health_selection_summary(result, outputs, constraint_summary):
    mode = normalize_eas_mode(result.get("mode") if isinstance(result, dict) else None)
    if mode != "solve-problem":
        return {}

    selected_values = _selection_selected_values(outputs)
    generic_selected_values = _generic_selected_solution_values(outputs)
    selected_configuration_key = _health_output_value(outputs, (
        "selected_configuration_key",
        "selected_config_key",
    ))
    selected_solution = _health_output_value(outputs, _health_selected_solution_candidates())
    if is_missing_value(selected_solution):
        selected_solution = _selection_selected_label_value(outputs)
    if is_missing_value(selected_solution):
        selected_solution = _selection_composite_solution_label(selected_values)
    if is_missing_value(selected_solution):
        selected_solution = _generic_selected_solution_label(generic_selected_values)
    component_selection_present = any(
        not is_missing_value(value)
        for value in selected_values.values()
    )
    selected_identity = (
        None
        if component_selection_present
        else _selection_selected_candidate_identity(
            outputs,
            selected_solution,
            generic_selected_values,
            selected_configuration_key=selected_configuration_key,
        )
    )
    scoped_candidate_criteria = _selection_candidate_scoped_criteria(outputs)
    requires_full_candidate_mapping = any(
        scope.get("full_key") for _, _, scope in scoped_candidate_criteria
    )

    selected_exists = (not is_missing_value(selected_solution)) or any(
        not is_missing_value(value)
        for value in selected_values.values()
    ) or any(
        not is_missing_value(item.get("value"))
        for item in generic_selected_values
    )
    pass_flags = _selection_pass_flags(outputs)
    selected_pass = _selection_pass_status(pass_flags)
    raw_selection_status = _health_output_value(outputs, (
        "selection_status",
        "overall_selection_status",
    ))
    selected_metric_present = _selection_selected_metric_present(outputs)
    if selected_pass is None:
        status_pass = _selection_status_pass_from_value(raw_selection_status)
        if status_pass is False:
            selected_pass = False
        elif status_pass is True and selected_exists and selected_metric_present:
            selected_pass = True
    rejected_failures, selected_failures = _split_selection_constraint_failures(
        constraint_summary.get("blocking_failures") or [],
        selected_values,
        generic_selected_values,
        selected_solution,
        selected_identity,
    )
    criteria_found, criteria_unknown, criteria_failures = _selection_selected_candidate_criteria_state(
        scoped_candidate_criteria,
        selected_identity,
    )
    viable_non_selected = _selection_viable_non_selected_alternatives(
        scoped_candidate_criteria,
        selected_identity,
    )
    selected_failures = _dedupe_health_failures([*selected_failures, *criteria_failures])
    selected_mapping_unknown = bool(
        selected_exists
        and scoped_candidate_criteria
        and not criteria_found
        and (
            selected_identity is None
            or (requires_full_candidate_mapping and not selected_identity.get("full_key"))
        )
        and not any(not is_missing_value(value) for value in selected_values.values())
    )
    if selected_mapping_unknown:
        selected_pass = None
    elif selected_failures:
        selected_pass = False
    elif criteria_found and selected_pass is None:
        selected_pass = None if criteria_unknown else True
    selected_margin_warnings = [
        item
        for item in constraint_summary.get("margin_sensitive_passes") or []
        if _selection_failure_targets_selected(
            item,
            selected_values,
            generic_selected_values,
            selected_solution,
            selected_identity,
        )
    ]

    selection_status = None
    if selected_mapping_unknown:
        selection_status = "selection_unknown"
    elif selected_exists and selected_pass is True:
        selection_status = "selection_pass"
    elif selected_exists and selected_pass is False:
        selection_status = "selected_option_failed_criteria"
    elif (
        (not selected_exists and constraint_summary.get("failed", 0))
        or _selection_status_indicates_no_viable_value(raw_selection_status)
    ):
        selection_status = "selection_no_viable_option"
    elif selected_exists:
        selection_status = "selection_unknown"

    return {
        "selection_status": selection_status,
        "selected_solution_pass": selected_pass,
        "selected_solution": selected_solution,
        "selected_conductor_AWG": selected_values.get("selected_conductor_AWG"),
        "selected_power_supply_A": selected_values.get("selected_power_supply_A"),
        "selected_fuse_A": selected_values.get("selected_fuse_A"),
        "selection_pass_flags": pass_flags,
        "rejected_option_failures": rejected_failures,
        "rejected_alternative_failures": rejected_failures,
        "selected_option_failures": selected_failures,
        "selected_candidate_failures": selected_failures,
        "selected_candidate_key": _selection_identity_display_key(selected_identity),
        "selected_configuration_key": selected_configuration_key,
        "viable_non_selected_alternatives": viable_non_selected,
        "selected_option_margin_sensitive_warnings": selected_margin_warnings,
    }


def _selection_selected_values(outputs):
    return {
        "selected_conductor_AWG": _health_output_value(outputs, (
            "selected_conductor_AWG",
            "selected_conductor_awg",
        )),
        "selected_power_supply_A": _health_output_value(outputs, (
            "selected_power_supply_A",
            "selected_power_supply_rating_A",
            "selected_ps_rating_A",
            "selected_ps_A",
            "selected_ps_amps",
            "selected_power_supply_amps",
        )),
        "selected_fuse_A": _health_output_value(outputs, (
            "selected_fuse_A",
            "selected_fuse_rating_A",
            "selected_fuse_amps",
        )),
    }


def _selection_composite_solution_label(selected_values):
    parts = []
    conductor = selected_values.get("selected_conductor_AWG")
    power_supply = selected_values.get("selected_power_supply_A")
    fuse = selected_values.get("selected_fuse_A")
    if not is_missing_value(conductor):
        parts.append(f"conductor={conductor} AWG")
    if not is_missing_value(power_supply):
        parts.append(f"power_supply={power_supply} A")
    if not is_missing_value(fuse):
        parts.append(f"fuse={fuse} A")
    return "; ".join(parts) if parts else None


def _generic_selected_solution_values(outputs):
    items = []
    for name, output in outputs.items():
        lowered = str(name or "").strip().lower()
        if not _is_generic_selected_solution_output_name(lowered):
            continue
        value = _output_value(output)
        if is_missing_value(value):
            continue
        items.append({"name": str(name), "value": value})
    return items


def _is_generic_selected_solution_output_name(lowered):
    if not lowered.startswith("selected_"):
        return False
    excluded_tokens = {
        "pass",
        "status",
        "key",
        "margin",
        "warning",
        "warnings",
        "failure",
        "failures",
        "count",
        "cost",
        "price",
        "score",
        "runtime",
        "duration",
        "velocity",
        "speed",
        "flow",
        "airflow",
        "pressure",
        "static",
        "fpm",
        "conductor",
        "awg",
        "power",
        "supply",
        "ps",
        "fuse",
    }
    tokens = _selection_name_tokens(lowered)
    return not tokens.intersection(excluded_tokens)


def _generic_selected_solution_label(items):
    parts = []
    for item in items:
        name = _selection_humanize_name(str(item.get("name") or "selected solution"))
        value = item.get("value")
        if is_missing_value(value):
            continue
        parts.append(f"{name}={value}")
    return "; ".join(parts) if parts else None


def _selection_selected_label_value(outputs):
    if not isinstance(outputs, dict):
        return None
    for name, output in outputs.items():
        lowered = str(name or "").strip().lower()
        if not lowered.startswith("selected_"):
            continue
        tokens = _selection_name_tokens(lowered)
        if tokens.intersection({"pass", "status", "key", "failure", "failures", "warning", "warnings"}):
            continue
        if not (lowered.endswith(("_label", "_name", "_str", "_string")) or tokens.intersection({"label", "name"})):
            continue
        value = _output_value(output)
        if not is_missing_value(value):
            return value
    return None


def _selection_humanize_name(name):
    return re.sub(r"\s+", " ", re.sub(r"[_\-]+", " ", str(name or ""))).strip().title()


def _selection_pass_flags(outputs):
    flag_names = (
        "overall_design_pass",
        "selected_design_pass",
        "selected_solution_pass",
        "selected_solution_viable",
        "selected_option_pass",
        "selected_option_viable",
        "selected_candidate_pass",
        "selected_candidate_viable",
        "selected_config_pass",
        "selected_config_viable",
        "overall_selection_pass",
        "overall_selection_status_pass",
        "overall_release_status",
        "overall_result_status",
        "release_status",
        "overall_status",
        "conductor_selection_pass",
        "power_supply_selection_pass",
        "ps_selection_pass",
        "fuse_selection_pass",
    )
    flags = {}
    for name in flag_names:
        value = _health_output_value(outputs, (name,))
        if value is None:
            continue
        status = _constraint_status_from_output(value)
        if status.get("recognized"):
            flags[name] = status.get("passes")
    return flags


def _selection_pass_status(flags):
    if not flags:
        return None
    if any(value is False for value in flags.values()):
        return False
    if any(value is None for value in flags.values()):
        return None
    has_overall_flag = any(
        name in flags
        for name in (
            "overall_design_pass",
            "selected_design_pass",
            "selected_solution_pass",
            "selected_solution_viable",
            "selected_option_pass",
            "selected_option_viable",
            "selected_candidate_pass",
            "selected_candidate_viable",
            "selected_config_pass",
            "selected_config_viable",
            "overall_selection_pass",
            "overall_selection_status_pass",
            "overall_release_status",
            "overall_result_status",
            "release_status",
            "overall_status",
        )
    )
    component_flags = [
        name
        for name in flags
        if name in {
            "conductor_selection_pass",
            "power_supply_selection_pass",
            "ps_selection_pass",
            "fuse_selection_pass",
        }
    ]
    if has_overall_flag or len(component_flags) >= 2:
        return True
    return None


def _selection_selected_metric_present(outputs):
    metric_names = (
        "selected_total_installed_cost",
        "selected_total_installed_cost_USD",
        "selected_total_installed_cost_usd",
        "selected_installed_cost",
        "selected_installed_cost_USD",
        "selected_installed_cost_usd",
        "selected_cost",
        "selected_cost_USD",
        "selected_cost_usd",
        "selected_score",
        "selected_option_score",
        "selected_candidate_score",
        "best_total_installed_cost",
        "best_total_installed_cost_USD",
        "best_total_installed_cost_usd",
        "lowest_cost_among_viable",
        "lowest_cost_among_viable_USD",
        "lowest_cost_among_viable_usd",
    )
    return not is_missing_value(_health_output_value(outputs, metric_names))


def _selection_status_pass_from_value(value):
    if _selection_status_indicates_no_viable_value(value):
        return False
    if _selection_status_indicates_viable_value(value):
        return True
    status = _constraint_status_from_output(value)
    if status.get("recognized"):
        return status.get("passes")
    return None


def _selection_status_indicates_viable_value(value):
    token = _selection_status_token(value)
    if not token or _selection_status_indicates_no_viable_value(token):
        return False
    return (
        token in {
            "selection_pass",
            "viable_option_found",
            "viable_options_found",
            "viable_solution_found",
            "viable_solutions_found",
            "pass_viable_option_found",
            "pass_viable_solution_found",
            "pass_configuration_selected",
            "configuration_selected",
            "candidate_selected",
            "option_selected",
        }
        or (token.startswith("pass_") and "viable" in token and "found" in token)
        or (token.startswith("pass_") and "selected" in token)
        or ("viable" in token and "found" in token)
    )


def _selection_status_indicates_no_viable_value(value):
    token = _selection_status_token(value)
    return bool(token) and (
        token in {
            "selection_no_viable_option",
            "no_viable_option",
            "no_viable_options",
            "no_viable_option_found",
            "no_viable_options_found",
            "no_viable_solution",
            "no_viable_solutions",
            "no_viable_solution_found",
            "no_viable_solutions_found",
        }
        or token.startswith("no_viable_")
    )


def _selection_status_token(value):
    text = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _selection_selected_candidate_identity(outputs, selected_solution, generic_selected_values, selected_configuration_key=None):
    identities = []

    def add_identity(value):
        identity = _selection_candidate_identity_from_text(value)
        if identity:
            identities.append(identity)

    add_identity(selected_configuration_key)
    for name in (
        "selected_configuration_key",
        "selected_config_key",
        "selected_candidate_key",
        "selected_option_key",
        "selected_concept_key",
    ):
        add_identity(_health_output_value(outputs, (name,)))
    add_identity(selected_solution)
    for name in _health_selected_solution_candidates():
        add_identity(_health_output_value(outputs, (name,)))
    for selected in generic_selected_values or []:
        if isinstance(selected, dict):
            add_identity(selected.get("value"))
            add_identity(f"{selected.get('name') or ''} {selected.get('value') or ''}")

    pipe_identity = None
    pump_identity = None
    for name in (
        "selected_pipe_option_name",
        "selected_pipe_option_label",
        "selected_pipe_name",
        "selected_pipe_label",
        "recommended_pipe_option_name",
    ):
        identity = _selection_candidate_identity_from_text(_health_output_value(outputs, (name,)))
        if identity and identity.get("pipe"):
            pipe_identity = identity
            break
    for name in (
        "selected_pump_option_name",
        "selected_pump_option_label",
        "selected_pump_name",
        "selected_pump_label",
        "recommended_pump_option_name",
    ):
        identity = _selection_candidate_identity_from_text(_health_output_value(outputs, (name,)))
        if identity and identity.get("pump"):
            pump_identity = identity
            break
    if pipe_identity or pump_identity:
        identities.append(_selection_merge_candidate_identities(pipe_identity, pump_identity))

    full = next((identity for identity in identities if identity.get("full_key")), None)
    if full:
        return full
    return next((identity for identity in identities if identity.get("generic") or identity.get("pipe") or identity.get("pump")), None)


def _selection_merge_candidate_identities(*identities):
    merged = {"pipe": None, "pump": None, "generic": None, "full_key": None}
    for identity in identities:
        if not isinstance(identity, dict):
            continue
        for key in ("pipe", "pump", "generic"):
            if identity.get(key) and not merged.get(key):
                merged[key] = identity.get(key)
    if merged.get("pipe") and merged.get("pump"):
        merged["full_key"] = f"{merged['pipe']}_{merged['pump']}"
    if not merged.get("generic"):
        merged["generic"] = merged.get("pipe")
    return merged


def _selection_candidate_identity_from_text(value):
    if is_missing_value(value):
        return None
    numeric_candidate = _selection_numeric_candidate_id_from_text(value)
    if numeric_candidate:
        return _selection_identity(generic=numeric_candidate)
    return _selection_candidate_identity_from_tokens(_name_tokens(value))


def _selection_candidate_identity_from_tokens(tokens):
    if not tokens:
        return None
    pipe = None
    pump = None
    generic = None

    for index, token in enumerate(tokens):
        first = tokens[index + 1] if index + 1 < len(tokens) else None
        second = tokens[index + 2] if index + 2 < len(tokens) else None
        third = tokens[index + 3] if index + 3 < len(tokens) else None

        if token in {"config", "configuration"}:
            candidate = _selection_candidate_letter(first)
            if candidate:
                pipe = pipe or candidate
                generic = generic or candidate
                pump = pump or _selection_pump_token_from_parts(second, third)
            continue

        if token in {"pipe", "piping"}:
            if first == "option":
                candidate = _selection_candidate_letter(second)
            else:
                candidate = _selection_candidate_letter(first)
            if candidate:
                pipe = pipe or candidate
                generic = generic or candidate
            continue

        if token == "pump":
            candidate = _selection_candidate_letter(first)
            if candidate:
                generic = generic or candidate
            pump = pump or _selection_pump_token_from_parts(first, second)
            continue

        if token in {"option", "candidate", "alternative", "concept"}:
            candidate = _selection_candidate_letter(first)
            if candidate:
                generic = generic or candidate
                if token == "option":
                    pipe = pipe or candidate
                if second == "pump":
                    pump = pump or _selection_pump_token_from_parts(third, None)
                else:
                    pump = pump or _selection_pump_token_from_parts(second, third)

    domain_identity = _selection_domain_option_identity_from_tokens(tokens)
    if domain_identity and not any((pipe, pump, generic)):
        generic = domain_identity.get("generic")

    for index, token in enumerate(tokens):
        first = tokens[index + 1] if index + 1 < len(tokens) else None
        second = tokens[index + 2] if index + 2 < len(tokens) else None
        candidate = _selection_candidate_letter(token)
        pump_token = _selection_pump_token_from_parts(first, second)
        if candidate and pump_token:
            pipe = pipe or candidate
            generic = generic or candidate
            pump = pump or pump_token
            break

    if not any((pipe, pump, generic)):
        return None
    return _selection_identity(pipe=pipe, pump=pump, generic=generic or pipe)


def _selection_identity(pipe=None, pump=None, generic=None):
    pipe = _canonical_candidate_token(pipe)
    pump = _canonical_pump_token(pump)
    generic = _canonical_candidate_token(generic or pipe)
    return {
        "pipe": pipe,
        "pump": pump,
        "generic": generic,
        "full_key": f"{pipe}_{pump}" if pipe and pump else None,
    }


def _selection_numeric_candidate_id_from_text(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return _canonical_numeric_candidate_id(value)
    text = str(value or "").strip()
    if not text:
        return None
    rhs_text = text.split("=", 1)[1].strip() if "=" in text else text
    rhs_text = rhs_text.strip("'\" ")
    numeric_p0 = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)_p0", rhs_text, flags=re.IGNORECASE)
    if numeric_p0:
        return _canonical_numeric_candidate_id(numeric_p0.group(1))
    numeric_unit = re.fullmatch(
        r"([+-]?\d+(?:\.\d+)?)(?:\s*(?:in|inch|inches|ft|mm|cm|m|awg|a|amp|amps|hp|kw|w))?",
        rhs_text,
        flags=re.IGNORECASE,
    )
    if numeric_unit:
        return _canonical_numeric_candidate_id(numeric_unit.group(1))
    embedded_p0 = re.search(r"(?<![a-z0-9])([+-]?\d+(?:\.\d+)?)_p0(?![a-z0-9])", text, flags=re.IGNORECASE)
    if embedded_p0:
        return _canonical_numeric_candidate_id(embedded_p0.group(1))
    if re.search(r"\bp\d+\b|_p\d+\b", text, flags=re.IGNORECASE):
        return None
    embedded_numbers = re.findall(
        r"(?<![a-z0-9])([+-]?\d+(?:\.0+)?)(?:\s*(?:in|inch|inches|ft|mm|cm|m|awg|a|amp|amps|hp|kw|w))?(?![a-z0-9])",
        text,
        flags=re.IGNORECASE,
    )
    if len(embedded_numbers) == 1:
        return _canonical_numeric_candidate_id(embedded_numbers[0])
    return None


def _canonical_candidate_token(token):
    text = str(token or "").strip().lower()
    if not text:
        return None
    unit_match = re.fullmatch(
        r"([+-]?\d+(?:\.\d+)?)(?:in|inch|inches|ft|mm|cm|m|awg|a|amp|amps|hp|kw|w)",
        text,
    )
    if unit_match:
        return _canonical_numeric_candidate_id(unit_match.group(1))
    numeric = _canonical_numeric_candidate_id(text)
    if numeric:
        return numeric
    if re.fullmatch(r"[a-z]", text):
        return text
    return text


def _canonical_numeric_candidate_id(value):
    if isinstance(value, bool) or value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text):
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    if math.isclose(number, round(number), rel_tol=0.0, abs_tol=1e-12):
        return str(int(round(number)))
    rendered = f"{number:.12g}".rstrip("0").rstrip(".")
    return rendered.replace(".", "_").replace("-", "neg_")


def _canonical_pump_token(token):
    text = str(token or "").strip().lower()
    if not text:
        return None
    if re.fullmatch(r"p\d+", text):
        return f"p{int(text[1:])}"
    if re.fullmatch(r"\d+", text):
        return f"p{int(text)}"
    return text


_SELECTION_DOMAIN_OPTION_MARKERS = {
    "awg",
    "conductor",
    "conductors",
    "duct",
    "ducts",
    "diameter",
    "diameters",
    "fuse",
    "fuses",
    "pipe",
    "pipes",
    "size",
    "sizes",
}

_SELECTION_DOMAIN_OPTION_CONTEXT_TOKENS = {
    "best",
    "candidate",
    "check",
    "criterion",
    "criteria",
    "fail",
    "failed",
    "fails",
    "option",
    "pass",
    "passed",
    "passes",
    "recommended",
    "selected",
    "selection",
    "status",
    "valid",
    "viable",
}

_SELECTION_DOMAIN_OPTION_SKIP_TOKENS = {
    "awg",
    "diameter",
    "diameters",
    "in",
    "inch",
    "inches",
    "label",
    "name",
    "nominal",
    "option",
    "selected",
    "size",
    "sizes",
    "str",
    "string",
    "value",
    "values",
}


def _selection_domain_option_identity_from_tokens(tokens):
    token_set = set(tokens)
    has_context = bool(token_set.intersection(_SELECTION_DOMAIN_OPTION_CONTEXT_TOKENS)) or any(
        re.fullmatch(r"c[1-9]\d*", token)
        for token in tokens
    )
    if not has_context:
        return None

    for index, token in enumerate(tokens):
        if token not in _SELECTION_DOMAIN_OPTION_MARKERS:
            continue
        for candidate_token in tokens[index + 1:index + 6]:
            if candidate_token in _SELECTION_DOMAIN_OPTION_SKIP_TOKENS:
                continue
            if re.fullmatch(r"c[1-9]\d*", candidate_token):
                continue
            candidate = _selection_candidate_letter(candidate_token)
            if candidate:
                return {"pipe": None, "pump": None, "generic": candidate, "full_key": None}
    return None


def _selection_candidate_letter(token):
    text = str(token or "").strip().lower()
    if re.fullmatch(r"[a-z]", text):
        return text
    numeric = _canonical_numeric_candidate_id(text)
    if numeric:
        return numeric
    unit_match = re.fullmatch(
        r"([+-]?\d+(?:\.\d+)?)(?:in|inch|inches|ft|mm|cm|m|awg|a|amp|amps|hp|kw|w)",
        text,
    )
    if unit_match:
        return _canonical_numeric_candidate_id(unit_match.group(1))
    return None


def _selection_pump_token_from_parts(first, second=None):
    first_text = str(first or "").strip().lower()
    second_text = str(second or "").strip().lower()
    if re.fullmatch(r"p\d+", first_text):
        return first_text
    if first_text == "p" and re.fullmatch(r"\d+", second_text):
        return f"p{second_text}"
    if re.fullmatch(r"\d+", first_text):
        return f"p{first_text}"
    return None


def _selection_candidate_scope_from_name(name):
    return _selection_candidate_identity_from_tokens(_name_tokens(name))


def _selection_candidate_scope_from_item(item):
    if isinstance(item, dict):
        for key in ("name", "boolean_output", "lhs", "item", "expression", "message", "description"):
            scope = _selection_candidate_scope_from_name(item.get(key))
            if scope:
                return scope
        return None
    return _selection_candidate_scope_from_name(item)


def _selection_candidate_scoped_criteria(outputs):
    scoped = []
    for name, output in outputs.items():
        lowered = str(name or "").strip().lower()
        scope = _selection_candidate_scope_from_name(name)
        if not scope:
            continue
        if not (
            _criterion_output_index(name) is not None
            or "criterion" in lowered
            or "criteria" in lowered
            or "pass" in lowered
            or "viable" in lowered
            or lowered.endswith("_status")
        ):
            continue
        status = _constraint_status_from_output(_output_value(output))
        if status.get("recognized"):
            scoped.append((str(name), output, scope))
    return scoped


def _selection_selected_candidate_criteria_state(scoped_candidate_criteria, selected_identity):
    found = False
    unknown = False
    failures = []
    for name, output, scope in scoped_candidate_criteria:
        if _selection_candidate_scope_matches_selected(scope, selected_identity) is not True:
            continue
        status = _constraint_status_from_output(_output_value(output))
        if not status.get("recognized"):
            continue
        found = True
        if status.get("passes") is False:
            failures.append({"name": name, "message": "Selected candidate criterion evaluated to FAIL."})
        elif status.get("passes") is None:
            unknown = True
    return found, unknown, failures


def _selection_candidate_scope_matches_selected(scope, selected_identity):
    if not scope or not selected_identity:
        return None
    selected_full = _canonical_full_candidate_key(selected_identity.get("full_key"))
    selected_pipe = _canonical_candidate_token(selected_identity.get("pipe"))
    selected_pump = _canonical_pump_token(selected_identity.get("pump"))
    selected_generic = _canonical_candidate_token(selected_identity.get("generic"))
    selected_bases = {
        item
        for item in (
            selected_pipe,
            selected_generic,
            _base_candidate_from_full_key(selected_full),
        )
        if item
    }

    if scope.get("full_key"):
        return bool(selected_full and selected_full == _canonical_full_candidate_key(scope.get("full_key")))
    if scope.get("pipe"):
        return bool(_canonical_candidate_token(scope.get("pipe")) in selected_bases)
    if scope.get("pump"):
        scope_pump = _canonical_pump_token(scope.get("pump"))
        if selected_pump and selected_pump == scope_pump:
            return True
        if not selected_pump and _pump_candidate_base(scope_pump) in selected_bases:
            return True
        return False
    if scope.get("generic"):
        return bool(_canonical_candidate_token(scope.get("generic")) in selected_bases)
    return None


def _selection_identity_display_key(identity):
    if not isinstance(identity, dict):
        return None
    if _is_numeric_p0_full_key(identity.get("full_key")) and identity.get("generic"):
        return str(_canonical_candidate_token(identity.get("generic"))).upper()
    if identity.get("full_key"):
        return str(_canonical_full_candidate_key(identity["full_key"])).upper()
    if identity.get("generic"):
        return str(_canonical_candidate_token(identity["generic"])).upper()
    if identity.get("pipe") and identity.get("pump"):
        return f"{_canonical_candidate_token(identity['pipe'])}_{_canonical_pump_token(identity['pump'])}".upper()
    return None


def _canonical_full_candidate_key(value):
    text = str(value or "").strip().lower()
    if not text:
        return None
    parts = [part for part in re.split(r"[_\W]+", text) if part]
    if len(parts) >= 2:
        base = _canonical_candidate_token(parts[0])
        pump = _canonical_pump_token(parts[1])
        if base and pump:
            return f"{base}_{pump}"
    return text


def _base_candidate_from_full_key(value):
    text = _canonical_full_candidate_key(value)
    if not text:
        return None
    return _canonical_candidate_token(str(text).split("_", 1)[0])


def _pump_candidate_base(value):
    text = _canonical_pump_token(value)
    if not text:
        return None
    if re.fullmatch(r"p\d+", text):
        return _canonical_candidate_token(text[1:])
    return None


def _is_numeric_p0_full_key(value):
    text = _canonical_full_candidate_key(value)
    if not text:
        return False
    return bool(re.fullmatch(r"\d+_p0", text))


def _selection_viable_non_selected_alternatives(scoped_candidate_criteria, selected_identity):
    grouped = {}
    for name, output, scope in scoped_candidate_criteria:
        if _selection_candidate_scope_matches_selected(scope, selected_identity) is True:
            continue
        key = _selection_identity_display_key(scope)
        if not key:
            continue
        status = _constraint_status_from_output(_output_value(output))
        if not status.get("recognized"):
            continue
        item = grouped.setdefault(key, {"candidate_key": key, "criteria": [], "failed": False, "unknown": False})
        item["criteria"].append(str(name))
        if status.get("passes") is False:
            item["failed"] = True
        elif status.get("passes") is None:
            item["unknown"] = True
    alternatives = []
    for key in sorted(grouped, key=_selection_candidate_sort_key):
        item = grouped[key]
        if item.get("criteria") and not item.get("failed") and not item.get("unknown"):
            alternatives.append({
                "candidate_key": key,
                "criteria": item.get("criteria") or [],
            })
    return alternatives


def _selection_candidate_sort_key(value):
    text = str(value or "")
    try:
        return (0, float(text.replace("_", ".")), text)
    except (TypeError, ValueError):
        return (1, text)


def _split_selection_constraint_failures(failures, selected_values, generic_selected_values, selected_solution, selected_identity=None):
    rejected = []
    selected = []
    for item in failures:
        relation = _selection_failure_relation_to_selected(
            item,
            selected_values,
            generic_selected_values,
            selected_solution,
            selected_identity,
        )
        if relation == "rejected":
            rejected.append(item)
        else:
            selected.append(item)
    return rejected, selected


def _selection_failure_relation_to_selected(item, selected_values, generic_selected_values, selected_solution, selected_identity=None):
    scope = _selection_candidate_scope_from_item(item)
    if scope:
        match = _selection_candidate_scope_matches_selected(scope, selected_identity)
        if match is True:
            return "selected"
        if match is False:
            return "rejected"
        if not _selection_has_selected_reference(selected_values, generic_selected_values, selected_solution):
            return "rejected"
    if _selection_failure_targets_selected(
        item,
        selected_values,
        generic_selected_values,
        selected_solution,
        selected_identity,
    ):
        return "selected"
    if _selection_failure_targets_rejected_legacy_component(item, selected_values):
        return "rejected"
    return "selected"


def _selection_has_selected_reference(selected_values, generic_selected_values, selected_solution):
    if not is_missing_value(selected_solution):
        return True
    if any(not is_missing_value(value) for value in (selected_values or {}).values()):
        return True
    return any(
        isinstance(selected, dict) and not is_missing_value(selected.get("value"))
        for selected in generic_selected_values or []
    )


def _selection_failure_targets_selected(item, selected_values, generic_selected_values, selected_solution, selected_identity=None):
    text = _selection_item_text(item)
    if not text:
        return False
    scope = _selection_candidate_scope_from_item(item)
    if scope:
        match = _selection_candidate_scope_matches_selected(scope, selected_identity)
        if match is True:
            return True
        if match is False:
            return False
    if "selected" in text or "selection_pass" in text or "overall_design" in text:
        return True

    conductor = selected_values.get("selected_conductor_AWG")
    if (
        not is_missing_value(conductor)
        and "awg" in text
        and _selection_text_contains_number(text, conductor)
    ):
        return True

    power_supply = selected_values.get("selected_power_supply_A")
    if (
        not is_missing_value(power_supply)
        and _selection_text_mentions_power_supply(text)
        and _selection_text_contains_number(text, power_supply)
    ):
        return True

    fuse = selected_values.get("selected_fuse_A")
    if (
        not is_missing_value(fuse)
        and "fuse" in text
        and _selection_text_contains_number(text, fuse)
    ):
        return True

    solution = str(selected_solution or "").strip().lower()
    if solution and solution in text:
        return True

    for selected in generic_selected_values or []:
        value = selected.get("value") if isinstance(selected, dict) else selected
        if not is_missing_value(value) and _selection_text_contains_value(text, value):
            return True
    return False


def _selection_failure_targets_rejected_legacy_component(item, selected_values):
    text = _selection_item_text(item)
    if not text:
        return False
    conductor = selected_values.get("selected_conductor_AWG")
    if (
        not is_missing_value(conductor)
        and "awg" in text
        and _selection_text_contains_any_number(text)
        and not _selection_text_contains_number(text, conductor)
    ):
        return True
    power_supply = selected_values.get("selected_power_supply_A")
    if (
        not is_missing_value(power_supply)
        and _selection_text_mentions_power_supply(text)
        and _selection_text_contains_any_number(text)
        and not _selection_text_contains_number(text, power_supply)
    ):
        return True
    fuse = selected_values.get("selected_fuse_A")
    if (
        not is_missing_value(fuse)
        and "fuse" in text
        and _selection_text_contains_any_number(text)
        and not _selection_text_contains_number(text, fuse)
    ):
        return True
    return False


def _selection_text_mentions_power_supply(text):
    lowered = str(text or "").strip().lower()
    if "supply" in lowered:
        return True
    tokens = {token for token in re.split(r"[^a-z0-9]+", lowered) if token}
    return bool(tokens.intersection({"ps", "psu"}))


def _selection_item_text(item):
    if isinstance(item, dict):
        text = " ".join(
            str(item.get(key) or "")
            for key in ("name", "boolean_output", "lhs", "item", "expression", "message", "description")
        )
    else:
        text = str(item)
    return text.strip().lower()


def _selection_text_contains_number(text, value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value).strip().lower() in text
    for match in re.finditer(r"(?<![a-z0-9])\d+(?:[._]\d+)?(?![a-z0-9])", str(text or "").lower()):
        try:
            token_value = float(match.group(0).replace("_", "."))
        except ValueError:
            continue
        if math.isclose(token_value, number, rel_tol=1e-12, abs_tol=1e-12):
            return True
    return False


def _selection_text_contains_any_number(text):
    return re.search(r"(?<![a-z0-9])\d+(?:[._]\d+)?(?![a-z0-9])", str(text or "").lower()) is not None


def _selection_text_contains_value(text, value):
    if _selection_text_contains_number(text, value):
        return True
    normalized_value = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    normalized_text = re.sub(r"[^a-z0-9]+", "_", str(text or "").strip().lower()).strip("_")
    return bool(normalized_value and normalized_value in normalized_text)


def _dedupe_health_failures(items):
    deduped = []
    seen = set()
    for item in items:
        if isinstance(item, dict):
            key = tuple(
                str(item.get(field) or "")
                for field in ("name", "item", "expression", "message", "description")
            )
        else:
            key = (str(item),)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _health_diagnostic_summary(result, outputs):
    mode = normalize_eas_mode(result.get("mode") if isinstance(result, dict) else None)
    if mode != "diagnose-root-cause":
        return {}

    supported = []
    eliminated = []
    unresolved = []
    primary_root_cause = None
    root_cause_support = []
    diagnostic_result_status = _health_diagnostic_result_status(outputs)

    for name, output in outputs.items():
        lowered = str(name or "").strip().lower()
        if not _is_diagnostic_boolean_output_name(lowered):
            continue
        value = _output_value(output)
        if not isinstance(value, bool):
            if _is_diagnostic_status_output_name(lowered):
                continue
            unresolved.append({"name": str(name), "value": value})
            continue
        item = {"name": str(name), "value": value}
        if value is True and _is_eliminated_root_cause_flag_name(lowered):
            eliminated.append(item)
        elif value is True:
            supported.append(item)
            if _is_likely_root_cause_flag_name(lowered):
                root_cause_support.append(item)
                if primary_root_cause is None:
                    primary_root_cause = _health_root_cause_label_from_flag_name(name)
        elif value is False and _is_eliminated_root_cause_flag_name(lowered):
            unresolved.append(item)
        elif value is False:
            eliminated.append(item)
        else:
            unresolved.append(item)

    if primary_root_cause is None:
        primary_root_cause = _health_output_value(outputs, _health_diagnostic_conclusion_names())
        if _is_undetermined_diagnostic_value(primary_root_cause):
            primary_root_cause = None

    fallback_status = None
    if primary_root_cause is None and not root_cause_support:
        fallback = _health_diagnostic_fallback_from_criteria(outputs)
        if fallback:
            supported.extend(fallback.get("supported_root_cause_flags") or [])
            eliminated.extend(fallback.get("eliminated_cause_flags") or [])
            unresolved.extend(fallback.get("unresolved_cause_flags") or [])
            primary_root_cause = fallback.get("primary_root_cause")
            fallback_status = fallback.get("diagnostic_status")
            if fallback_status == "diagnostic_result":
                root_cause_support.extend(fallback.get("supported_root_cause_flags") or [])

    evidence_count = len(supported) + len(eliminated) + len(unresolved)
    if len(root_cause_support) > 1:
        diagnostic_status = "diagnostic_conflict"
        primary_root_cause = None
        unresolved.extend(
            {"name": item.get("name"), "value": item.get("value"), "reason": "multiple_root_causes_supported"}
            for item in root_cause_support
        )
    elif diagnostic_result_status == "NEEDS_HUMAN_REVIEW":
        diagnostic_status = "diagnostic_needs_human_review"
    elif fallback_status:
        diagnostic_status = fallback_status
    elif primary_root_cause or root_cause_support:
        diagnostic_status = "diagnostic_result"
    elif evidence_count:
        diagnostic_status = "diagnostic_evidence_only"
    else:
        diagnostic_status = "diagnostic_unknown"

    return {
        "diagnostic_status": diagnostic_status,
        "supported_root_cause_flags": supported,
        "eliminated_cause_flags": eliminated,
        "unresolved_cause_flags": unresolved,
        "primary_root_cause": primary_root_cause,
        "diagnostic_evidence_count": evidence_count,
    }


def _health_diagnostic_result_status(outputs):
    value = _health_output_value(outputs, _health_diagnostic_status_names())
    return _normalize_diagnostic_result_status(value)


def _health_diagnostic_status_names():
    return [
        "overall_diagnostic_result",
        "overall_diagnostic_status",
        "diagnostic_result",
        "diagnostic_status",
        "root_cause_result",
        "root_cause_status",
    ]


def _normalize_diagnostic_result_status(value):
    text = str(value or "").strip()
    if not text:
        return None
    token = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").upper()
    if token in {
        "ROOT_CAUSE_IDENTIFIED",
        "CAUSE_IDENTIFIED",
        "DIAGNOSED",
        "DIAGNOSIS_IDENTIFIED",
        "DIAGNOSTIC_RESULT",
    }:
        return "ROOT_CAUSE_IDENTIFIED"
    if token in {
        "NEEDS_HUMAN_REVIEW",
        "HUMAN_REVIEW_REQUIRED",
        "REVIEW_REQUIRED",
        "UNRESOLVED",
        "NO_ROOT_CAUSE_IDENTIFIED",
    }:
        return "NEEDS_HUMAN_REVIEW"
    if token in {"UNKNOWN", "UNDETERMINED", "INDETERMINATE"}:
        return "UNKNOWN"
    return None


def _is_diagnostic_status_output_name(lowered):
    lowered = str(lowered or "").strip().lower()
    return lowered in {name.lower() for name in _health_diagnostic_status_names()}


def _health_root_cause_label_from_flag_name(name):
    lowered = str(name or "").strip().lower()
    known = {
        "is_root_cause_fouled_strainer": "fouled strainer / excessive strainer pressure drop",
        "likely_cause_fouled_strainer": "fouled strainer / excessive strainer pressure drop",
        "likely_cause_fouled_strainer_filter": "fouled strainer / excessive strainer pressure drop",
        "is_root_cause_restricted_path": "restricted valve or manifold path",
        "is_root_cause_undersized_piping": "undersized or excessively long piping",
        "is_root_cause_tubing_pressure_drop": "excessive tubing pressure drop / undersized actuator tubing",
        "likely_cause_excessive_tubing_pressure_drop": "excessive tubing pressure drop / undersized actuator tubing",
    }
    if lowered in known:
        return known[lowered]
    if lowered.startswith("is_root_cause_"):
        return lowered.removeprefix("is_root_cause_").replace("_", " ")
    return str(name)


def _health_diagnostic_fallback_from_criteria(outputs):
    criteria = _hydraulic_diagnostic_criterion_states(outputs)
    if not criteria:
        return None

    values = {key: item.get("value") for key, item in criteria.items()}
    if not any(value is False for value in values.values()):
        return None

    required_eliminations = (
        "cylinder_leakage",
        "suction_vacuum",
        "relief_pressure",
        "lift_pressure_sufficiency",
    )
    clear_pump_internal_leakage = (
        values.get("speed") is False
        and values.get("case_drain") is False
        and all(values.get(name) is True for name in required_eliminations)
    )

    supported = []
    eliminated = []
    unresolved = []

    if clear_pump_internal_leakage:
        evidence_names = [
            criteria[name]["name"]
            for name in (
                "speed",
                "case_drain",
                "cylinder_leakage",
                "suction_vacuum",
                "relief_pressure",
                "lift_pressure_sufficiency",
            )
            if name in criteria
        ]
        supported.append({
            "name": "inferred_likely_cause_excessive_pump_internal_leakage_or_pump_wear",
            "value": True,
            "source": "diagnostic_fallback",
            "evidence": evidence_names,
        })
        for key, inferred_name in (
            ("cylinder_leakage", "inferred_eliminated_cause_excessive_cylinder_leakage"),
            ("suction_vacuum", "inferred_eliminated_cause_suction_restriction_or_cavitation"),
            ("relief_pressure", "inferred_eliminated_cause_relief_pressure_out_of_range"),
            ("lift_pressure_sufficiency", "inferred_eliminated_cause_insufficient_lift_pressure"),
        ):
            if values.get(key) is True:
                eliminated.append({
                    "name": inferred_name,
                    "value": True,
                    "source": "diagnostic_fallback",
                    "evidence": [criteria[key]["name"]],
                })
        return {
            "diagnostic_status": "diagnostic_result",
            "supported_root_cause_flags": supported,
            "eliminated_cause_flags": eliminated,
            "unresolved_cause_flags": [],
            "primary_root_cause": "excessive_pump_internal_leakage_or_pump_wear",
        }

    for key, item in criteria.items():
        value = item.get("value")
        if value is False:
            unresolved.append({
                "name": item.get("name"),
                "value": value,
                "source": "diagnostic_fallback",
                "evidence_role": "criterion_failed_without_unique_root_cause",
            })
        elif value is True and key != "speed":
            eliminated.append({
                "name": item.get("name"),
                "value": value,
                "source": "diagnostic_fallback",
                "evidence_role": "candidate_cause_not_supported_by_criterion",
            })

    if not supported and not eliminated and not unresolved:
        return None

    return {
        "diagnostic_status": "diagnostic_evidence_only",
        "supported_root_cause_flags": supported,
        "eliminated_cause_flags": eliminated,
        "unresolved_cause_flags": unresolved,
        "primary_root_cause": None,
    }


def _hydraulic_diagnostic_criterion_states(outputs):
    criteria = {}
    for name, output in outputs.items():
        lowered = str(name or "").strip().lower()
        if not _is_diagnostic_criterion_pass_name(lowered):
            continue
        value = _output_value(output)
        if not isinstance(value, bool):
            continue
        key = _hydraulic_diagnostic_criterion_key(lowered)
        if key and key not in criteria:
            criteria[key] = {"name": str(name), "value": value}
    return criteria


def _is_diagnostic_criterion_pass_name(lowered):
    lowered = str(lowered or "").strip().lower()
    return "criterion" in lowered and "pass" in lowered


def _hydraulic_diagnostic_criterion_key(lowered):
    if "speed" in lowered:
        return "speed"
    if "case" in lowered and "drain" in lowered:
        return "case_drain"
    if "cylinder" in lowered and ("leakage" in lowered or "bypass" in lowered):
        return "cylinder_leakage"
    if "suction" in lowered:
        return "suction_vacuum"
    if "relief" in lowered and "pressure" in lowered:
        return "relief_pressure"
    if "lift" in lowered and "pressure" in lowered and (
        "sufficien" in lowered or "load" in lowered
    ):
        return "lift_pressure_sufficiency"
    return None


def _is_likely_root_cause_flag_name(lowered):
    lowered = str(lowered or "").strip().lower()
    if _is_generic_root_cause_rule_flag_name(lowered):
        return False
    return (
        lowered.startswith(("likely_cause_", "probable_cause_", "root_cause_", "is_root_cause_"))
        or "_likely_cause_" in lowered
        or "_probable_cause_" in lowered
        or "_is_root_cause_" in lowered
    )


def _is_generic_root_cause_rule_flag_name(lowered):
    lowered = str(lowered or "").strip().lower()
    return bool(re.fullmatch(r"root_cause_(?:rule|logic|criteria?|condition|check).*", lowered))


def _is_eliminated_root_cause_flag_name(lowered):
    lowered = str(lowered or "").strip().lower()
    return (
        lowered.startswith(("eliminated_cause_", "ruled_out_cause_"))
        or "_eliminated_cause_" in lowered
        or "_ruled_out_cause_" in lowered
    )


def _is_undetermined_diagnostic_value(value):
    text = str(value or "").strip().lower()
    return text in {
        "",
        "undetermined",
        "unknown",
        "none",
        "n/a",
        "na",
        "needs_human_review",
        "human_review_required",
        "review_required",
        "root_cause_identified",
        "no_root_cause_identified",
    }


def _health_diagnostic_conclusion_names():
    return [
        "primary_root_cause",
        "overall_root_cause_diagnosis",
        "root_cause_status_string",
        "root_cause",
        "diagnostic_conclusion",
        "diagnosis",
    ]


def _health_diagnostic_categories(
    result,
    status,
    mcm_required,
    skipped_count,
    missing_variables_count,
    missing_outputs_count,
    invalid_unit_outputs_count,
):
    categories = []
    preflight_unresolved = result.get("preflight_unresolved_variables")
    if preflight_unresolved:
        categories.extend(["schema/Activation 1 mismatch", "unresolved alias"])
    if result.get("selection_aggregation_diagnostics"):
        categories.append("selection aggregation incomplete")
    if missing_variables_count:
        categories.append("missing variable")
    if skipped_count:
        categories.append("skipped equation")
        skipped_text = " ".join(str(item.get("reason") if isinstance(item, dict) else item) for item in result.get("equations_skipped", []))
        if "unsupported" in skipped_text.lower():
            categories.append("unsupported expression")
    if invalid_unit_outputs_count:
        categories.append("invalid unit output")
    if missing_outputs_count:
        categories.append("incomplete requested outputs")
    if status == "unsupported":
        categories.append("unsupported expression")
    if status == "error":
        categories.append("error")
    if mcm_required and status not in {"computed", "not_required"} and not categories:
        categories.append("non-computed status from policy")
    if not mcm_required and status == "not_required":
        categories.append("not_required")
    return sorted(dict.fromkeys(categories))


def _health_blocking_failures(
    result,
    constraint_summary,
    diagnostic_categories,
    screening_summary=None,
    diagnostic_summary=None,
    selection_summary=None,
):
    screening_summary = screening_summary if isinstance(screening_summary, dict) else {}
    diagnostic_summary = diagnostic_summary if isinstance(diagnostic_summary, dict) else {}
    selection_summary = selection_summary if isinstance(selection_summary, dict) else {}
    failures = []
    for name in result.get("missing_variables") or []:
        failures.append({"type": "missing_variable", "item": name, "message": f"Missing variable: {name}."})
    for name in result.get("missing_outputs") or []:
        failures.append({"type": "missing_output", "item": name, "message": f"Missing requested output: {name}."})
    for name in result.get("invalid_unit_outputs") or []:
        failures.append({"type": "invalid_unit_output", "item": name, "message": f"Invalid unit validation for requested output: {name}."})
    for item in result.get("equations_skipped") or []:
        if isinstance(item, dict):
            failures.append({
                "type": "skipped_equation",
                "item": item.get("equation"),
                "message": item.get("reason") or "Equation was skipped.",
            })
        else:
            failures.append({"type": "skipped_equation", "item": str(item), "message": "Equation was skipped."})
    constraint_failures = constraint_summary.get("blocking_failures") or []
    if screening_summary.get("screening_status") == "screening_pass":
        constraint_failures = screening_summary.get("selected_candidate_failures") or []
    if selection_summary.get("selection_status") in {"selection_pass", "selected_option_failed_criteria"}:
        constraint_failures = (
            selection_summary.get("selected_candidate_failures")
            or selection_summary.get("selected_option_failures")
            or []
        )
    elif selection_summary.get("selection_status") == "selection_no_viable_option":
        constraint_failures = (
            selection_summary.get("rejected_option_failures")
            or selection_summary.get("rejected_alternative_failures")
            or constraint_failures
        )
    elif selection_summary.get("selection_status") == "selection_unknown":
        constraint_failures = []
    if diagnostic_summary.get("diagnostic_status") in {"diagnostic_result", "diagnostic_evidence_only"}:
        constraint_failures = [
            item for item in constraint_failures
            if not _health_failure_is_diagnostic_evidence(item)
        ]

    for item in constraint_failures:
        if isinstance(item, dict):
            failures.append({
                "type": "constraint_failure",
                "item": item.get("name"),
                "message": item.get("message") or "Constraint failed.",
            })
    if selection_summary.get("selection_status") == "selection_unknown":
        failures.append({
            "type": "selection_unknown",
            "item": selection_summary.get("selected_solution"),
            "message": "Selected solution could not be mapped to candidate-scoped criteria.",
        })
    if selection_summary.get("selection_status") == "selection_no_viable_option":
        failures.append({
            "type": "no_viable_candidate",
            "item": None,
            "message": "No viable selected solution was identified.",
        })
    if not failures and diagnostic_categories:
        message = result.get("message") or "MCM did not return a clean computed result."
        failures.append({"type": diagnostic_categories[0], "item": None, "message": message})
    return failures


def _health_failure_is_diagnostic_evidence(item):
    if isinstance(item, dict):
        text = " ".join(
            str(item.get(key) or "")
            for key in ("name", "item", "expression", "message", "description")
        )
    else:
        text = str(item)
    lowered = text.strip().lower()
    if not lowered:
        return False
    return (
        "diagnostic" in lowered
        or "root_cause" in lowered
        or "likely_cause" in lowered
        or "probable_cause" in lowered
        or "eliminated_cause" in lowered
        or _is_diagnostic_criterion_pass_name(lowered)
        or _is_hydraulic_diagnostic_check_name(lowered)
        or re.search(r"(?<![a-z0-9])is_[a-z0-9_]+", lowered) is not None
    )


def _is_hydraulic_diagnostic_check_name(lowered):
    lowered = str(lowered or "").strip().lower()
    if "_check" not in lowered:
        return False
    return _hydraulic_diagnostic_criterion_key(lowered) is not None


def _health_readiness_label(
    status,
    mcm_required,
    skipped_count,
    missing_variables_count,
    missing_outputs_count,
    invalid_unit_outputs_count,
    unit_warnings_count,
    constraint_failed_count,
    constraint_unknown_count,
):
    if not mcm_required and status == "not_required":
        return "not_required"
    if status == "computed":
        if any((skipped_count, missing_variables_count, missing_outputs_count, invalid_unit_outputs_count)):
            return "partial"
        if constraint_failed_count or constraint_unknown_count:
            return "needs_human_review"
        return "computed_with_warnings" if unit_warnings_count else "computed_clean"
    if status in {"partial", "needs_human_review", "unsupported", "error"}:
        return status
    return "error" if mcm_required else "unsupported"


def _health_recommendation_status(outputs, recommended_name=None):
    status = _health_output_value(outputs, _health_recommendation_status_names())
    normalized = _normalize_status_value(status)
    if normalized:
        return normalized
    if not is_missing_value(recommended_name):
        return "PASS"
    return status


def _health_output_value(outputs, candidates):
    for name in candidates:
        output = outputs.get(name)
        if isinstance(output, dict):
            return output.get("value")
    lowered = {str(name).lower(): name for name in outputs}
    for candidate in candidates:
        original = lowered.get(str(candidate).lower())
        output = outputs.get(original) if original else None
        if isinstance(output, dict):
            return output.get("value")
    return None


def _health_release_status_names():
    return list(_overall_status_alias_names())


def _health_recommendation_status_names():
    return [
        "overall_recommendation_status",
        "recommendation_status",
        "overall_recommendation_status_string",
    ]


def _health_recommended_name_candidates():
    return [
        "recommended_option_name",
        "recommended_concept_name",
        "recommended_candidate_name",
        "recommended_option",
        "recommended_concept",
        "best_viable_concept_name",
        "best_concept_name",
    ]


def _health_recommended_concept_name_candidates():
    return [
        "recommended_concept_name",
        "recommended_concept",
        "best_viable_concept_name",
        "best_concept_name",
    ]


def _health_selected_solution_candidates():
    return [
        "selected_solution",
        "selected_solution_name",
        "selected_config_name",
        "selected_configuration_name",
        "selected_configuration_label",
        "selected_config_label",
        "recommended_config_name",
        "recommended_configuration_name",
        "recommended_configuration_label",
        "recommended_config_label",
        "selected_candidate_name",
        "recommended_candidate_name",
        "best_config_label",
        "best_configuration_label",
        "selected_duct_diameter_str",
        "selected_option_name",
        "recommended_option_name",
        "selected_concept_name",
        "recommended_concept_name",
        "best_config_name",
        "best_candidate_name",
        "best_option_name",
        "best_concept_name",
        "best_viable_concept_name",
    ]


def _percent_delta(delta, baseline):
    if delta is None or not _is_number(baseline) or baseline == 0:
        return None
    return (delta / baseline) * 100


def _is_number(value):
    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


def _base_result(mcm_request, status, message, outputs, diagnostics, inputs_used=None):
    if status == "computed":
        try:
            _validate_evaluated_value(outputs)
        except ValueError as error:
            status = "unsupported"
            message = f"MCM rejected an unbounded or non-finite result: {error}"
            outputs = {}
            diagnostics = list(diagnostics) + [
                "Computed output failed the public evaluator bounds."
            ]
    return {
        "module": "Synthetic_OS_MCM",
        "computation_id": mcm_request.get("computation_id") if isinstance(mcm_request, dict) else None,
        "status": status,
        "message": message,
        "mode": mcm_request.get("mode") if isinstance(mcm_request, dict) else None,
        "objective": mcm_request.get("objective") if isinstance(mcm_request, dict) else None,
        "task_type": mcm_request.get("task_type") if isinstance(mcm_request, dict) else None,
        "operation": mcm_request.get("operation") if isinstance(mcm_request, dict) else None,
        "outputs": outputs,
        "inputs_used": inputs_used or {},
        "constraints": mcm_request.get("constraints", []) if isinstance(mcm_request, dict) else [],
        "requested_output": mcm_request.get("requested_output") if isinstance(mcm_request, dict) else None,
        "diagnostics": diagnostics,
    }
