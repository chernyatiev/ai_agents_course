"""SymPy-инструменты: решение уравнений/неравенств и упрощение выражений."""
import re

import sympy
from sympy.parsing.sympy_parser import (
    convert_xor,
    parse_expr,
    standard_transformations,
)

from agent.tools.registry import register

# convert_xor позволяет модели писать x^2 вместо x**2.
_TRANSFORMS = standard_transformations + (convert_xor,)

# Предположения о переменных для разных областей.
_DOMAINS = {
    "real": {"real": True},
    "integer": {"integer": True},
    "natural": {"integer": True, "positive": True},
    "complex": {},
}

# Одиночный "=" — разделитель уравнения; "==", "<=", ">=", "!=" не трогаем.
_EQUALS = re.compile(r"(?<![<>=!])=(?!=)")


def _parse(text: str, symbols: dict):
    """Строку 'x^2 - 5x = -6' превращает в объект SymPy.

    ВНИМАНИЕ: parse_expr внутри использует eval — изоляция на занятии 3.
    """
    parts = _EQUALS.split(text)
    if len(parts) == 2:
        left, right = (parse_expr(p, local_dict=symbols, transformations=_TRANSFORMS) for p in parts)
        return sympy.Eq(left, right)
    if len(parts) > 2:
        raise ValueError(f"В строке больше одного '=': {text}")
    return parse_expr(text, local_dict=symbols, transformations=_TRANSFORMS)


def sympy_solve(equations: list[str], variables: list[str], domain: str = "real") -> dict:
    if domain not in _DOMAINS:
        raise ValueError(f"domain должен быть одним из {list(_DOMAINS)}")
    symbols = {name: sympy.Symbol(name, **_DOMAINS[domain]) for name in variables}
    exprs = [_parse(e, symbols) for e in equations]
    unknowns = [symbols[name] for name in variables]

    is_inequality = any(
        isinstance(e, sympy.core.relational.Relational) and not isinstance(e, sympy.Eq)
        for e in exprs
    )
    if is_inequality:
        if len(unknowns) != 1:
            raise ValueError("Неравенства поддерживаются только для одной переменной")
        result = sympy.reduce_inequalities(exprs, unknowns[0])
        return {"kind": "inequality", "solution": str(result)}

    solutions = sympy.solve(exprs, unknowns, dict=True)
    return {
        "kind": "equations",
        "count": len(solutions),
        "solutions": [{str(k): str(v) for k, v in sol.items()} for sol in solutions],
    }


def sympy_simplify(expression: str) -> str:
    expr = _parse(expression, {})
    return str(sympy.simplify(expr))


register(
    name="sympy_solve",
    description=(
        "Точно решает уравнение, систему уравнений или неравенство с одной переменной "
        "средствами SymPy. Уравнения записываются через '=' (например 'x^2 - 5*x + 6 = 0'), "
        "неравенства через <, >, <=, >=. Возвращает JSON со всеми решениями и их количеством."
    ),
    parameters={
        "type": "object",
        "properties": {
            "equations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Уравнения или неравенства, например ['x + y = 10', 'x - y = 2']",
            },
            "variables": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Имена неизвестных, например ['x', 'y']",
            },
            "domain": {
                "type": "string",
                "enum": list(_DOMAINS),
                "description": "Где ищем решения: real (по умолчанию), integer, natural, complex",
            },
        },
        "required": ["equations", "variables"],
    },
    func=sympy_solve,
)

register(
    name="sympy_simplify",
    description="Упрощает выражение средствами SymPy, например '(a^2 - b^2)/(a - b)' -> 'a + b'.",
    parameters={
        "type": "object",
        "properties": {"expression": {"type": "string", "description": "Выражение"}},
        "required": ["expression"],
    },
    func=sympy_simplify,
)
