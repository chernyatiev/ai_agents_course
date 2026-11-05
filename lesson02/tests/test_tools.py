"""Юнит-тесты инструментов — без LLM и без сети."""
import json

from agent import tools
from agent.tools.eval_tool import python_eval
from agent.tools.sympy_tool import sympy_simplify, sympy_solve
from agent.tools.z3_tool import z3_check


# ---------- реестр ----------

def test_registry_has_all_tools():
    assert set(tools.names()) == {"python_eval", "sympy_solve", "sympy_simplify", "z3_check"}


def test_schemas_are_openai_format():
    for schema in tools.schemas():
        assert schema["type"] == "function"
        assert {"name", "description", "parameters"} <= set(schema["function"])


def test_call_unknown_tool_returns_error_text():
    assert tools.call("nope", "{}").startswith("Ошибка: неизвестный инструмент nope")


def test_call_bad_json_returns_error_text():
    assert "корректным JSON" in tools.call("python_eval", "{expression:")


def test_call_exception_inside_tool_returns_error_text():
    assert tools.call("python_eval", json.dumps({"expression": "1/0"})) == (
        "Ошибка ZeroDivisionError: division by zero"
    )


def test_call_serializes_dict_result_to_json():
    out = tools.call("sympy_solve", json.dumps({"equations": ["x + 1 = 3"], "variables": ["x"]}))
    assert json.loads(out)["solutions"] == [{"x": "2"}]


# ---------- python_eval ----------

def test_eval_counts_multiples_of_7():
    assert python_eval("sum(1 for n in range(100, 1000) if n % 7 == 0)") == "128"


# ---------- SymPy ----------

def test_sympy_quadratic():
    r = sympy_solve(["x^2 - 5*x + 6 = 0"], ["x"])
    assert r["count"] == 2
    assert sorted(s["x"] for s in r["solutions"]) == ["2", "3"]


def test_sympy_system():
    r = sympy_solve(["x + y = 10", "x - y = 2"], ["x", "y"])
    assert r["solutions"] == [{"x": "6", "y": "4"}]


def test_sympy_domain_filters_roots():
    real = sympy_solve(["x^2 = 2"], ["x"], domain="real")
    integer = sympy_solve(["x^2 = 2"], ["x"], domain="integer")
    assert real["count"] == 2
    assert integer["count"] == 0


def test_sympy_natural_domain():
    r = sympy_solve(["x^2 = 9"], ["x"], domain="natural")
    assert r["solutions"] == [{"x": "3"}]


def test_sympy_inequality():
    r = sympy_solve(["2*x - 3 > 5"], ["x"])
    assert r["kind"] == "inequality"
    assert "4 < x" in r["solution"]


def test_sympy_simplify():
    assert sympy_simplify("(a^2 - b^2)/(a - b)") == "a + b"


# ---------- z3 ----------

def test_z3_knights_and_knaves_unique():
    # A: «B — лжец». B: «Мы с A одного типа». True = рыцарь.
    r = z3_check({"A": "Bool", "B": "Bool"}, ["A == Not(B)", "B == (A == B)"])
    assert r == {"status": "sat", "solution": {"A": True, "B": False}, "unique": True}


def test_z3_detects_several_solutions():
    r = z3_check({"x": "Int", "y": "Int"}, ["x > 0", "y > 0", "x + y == 10"])
    assert r["unique"] is False
    assert r["another_solution"] != r["solution"]
    assert sum(r["another_solution"].values()) == 10


def test_z3_minimize_crt():
    r = z3_check({"n": "Int"}, ["n > 1", "n % 3 == 1", "n % 4 == 1", "n % 5 == 1"], minimize="n")
    assert r["solution"] == {"n": 61}
    assert r["objective_value"] == 61
    assert r["unique"] is True  # наименьшее единственно


def test_z3_maximize_with_tie_is_not_unique():
    # Максимум x + y = 4 достигается в нескольких точках.
    r = z3_check({"x": "Int", "y": "Int"}, ["x >= 0", "y >= 0", "x <= 3", "y <= 3", "x + y <= 4"],
                 maximize="x + y")
    assert r["objective_value"] == 4
    assert r["unique"] is False


def test_z3_unsat():
    assert z3_check({"x": "Int"}, ["x > 5", "x < 3"]) == {"status": "unsat"}


def test_z3_distinct_digits():
    # Двузначное число, цифры различны, сумма цифр 9, число делится на 7.
    r = z3_check(
        {"a": "Int", "b": "Int"},
        ["a >= 1", "a <= 9", "b >= 0", "b <= 9", "Distinct(a, b)", "a + b == 9", "(10*a + b) % 7 == 0"],
    )
    assert r["solution"] == {"a": 6, "b": 3} and r["unique"] is True
