"""Тесты конвейера разрешений — без LLM, без сети и без клавиатуры."""
import json

import pytest

from agent import permissions
from agent.permissions import evaluate, find_violation

# Обход «пустых builtins», который работал в занятии 2: из кортежа добираемся
# до всех классов интерпретатора, среди них subprocess.Popen.
ESCAPE = "[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'Popen']"


def args(**kw):
    return json.dumps(kw, ensure_ascii=False)


# ---------- ворота 1: AST-валидатор ----------

@pytest.mark.parametrize("code", [
    ESCAPE,
    "__import__('os').system('ls')",
    "getattr((), 'x')",
    "'{0.__class__}'.format(())",
    "open('/etc/passwd').read()",
    "(lambda: exec('1'))()",
    "f'{().__class__}'",
])
def test_dangerous_expressions_are_denied(code):
    assert find_violation(code) is not None


@pytest.mark.parametrize("code", [
    "sum(1 for n in range(100, 1000) if n % 7 == 0)",
    "math.gcd(12, 18)",
    "sorted(set(x * x % 10 for x in range(10)))",
])
def test_normal_expressions_pass(code):
    assert find_violation(code) is None


def test_import_forbidden_in_expression_mode():
    # Инструкцию import в выражение не вписать, остаётся __import__ — и он запрещён.
    assert find_violation("__import__('math')") is not None


def test_script_may_import_math_modules():
    assert find_violation("import math\nfrom itertools import permutations\nprint(1)", mode="exec") is None


@pytest.mark.parametrize("code", ["import os", "from subprocess import run", "import socket", "import sys"])
def test_script_cannot_import_system_modules(code):
    assert "запрещён" in find_violation(code, mode="exec")


def test_syntax_error_is_left_for_the_tool():
    assert find_violation("sum(range(1, 101)") is None
    assert find_violation("x.__class__ (") is not None  # но __ не пропускаем даже так


def test_deny_checks_z3_constraints():
    d = evaluate("z3_check", {"variables": {"x": "Int"}, "constraints": ["x > 0", ESCAPE]})
    assert d.behavior == "deny"


def test_deny_checks_both_sides_of_sympy_equation():
    d = evaluate("sympy_solve", {"equations": ["x = ().__class__"], "variables": ["x"]})
    assert d.behavior == "deny"
    ok = evaluate("sympy_solve", {"equations": ["x^2 - 5*x + 6 = 0"], "variables": ["x"]})
    assert ok.behavior == "allow"


# ---------- ворота 2: правила ----------

def test_python_run_always_needs_approval():
    d = evaluate("python_run", {"code": "print(1)"})
    assert d.behavior == "ask" and "скрипта" in d.reason


def test_big_range_needs_approval():
    assert evaluate("python_eval", {"expression": "sum(range(10**8))"}).behavior == "ask"
    assert evaluate("python_eval", {"expression": "9**9**9"}).behavior == "ask"
    assert evaluate("python_eval", {"expression": "sum(range(1000))"}).behavior == "allow"


def test_all_matching_rules_are_reported():
    d = evaluate("python_run", {"code": "print(sum(range(10**9)))", "timeout": 20})
    assert "скрипта" in d.reason and "Долгий" in d.reason and "перебор" in d.reason


def test_deny_wins_over_ask():
    assert evaluate("python_run", {"code": "import os"}).behavior == "deny"


# ---------- ворота 3 и режимы ----------

def test_user_says_yes():
    d = permissions.check("python_run", args(code="print(1)"), ask=lambda *a: "y")
    assert d.allowed


def test_user_says_no():
    d = permissions.check("python_run", args(code="print(1)"), ask=lambda *a: "n")
    assert not d.allowed and "отклонил" in d.reason


def test_always_allow_remembers_tool_for_session():
    asked = []

    def ask(*a):
        asked.append(a)
        return "a"

    for _ in range(3):
        assert permissions.check("python_run", args(code="print(1)"), ask=ask).allowed
    assert len(asked) == 1
    assert permissions.always_allowed() == ["python_run"]


def test_always_allow_does_not_bypass_deny():
    permissions.check("python_run", args(code="print(1)"), ask=lambda *a: "a")
    assert not permissions.check("python_run", args(code="import os"), ask=lambda *a: "a").allowed


def test_auto_mode_does_not_ask():
    permissions.set_mode("auto")
    assert permissions.check("python_run", args(code="print(1)"), ask=None).allowed
    assert not permissions.check("python_eval", args(expression=ESCAPE)).allowed  # ворота 1 работают


def test_strict_mode_denies_without_asking():
    permissions.set_mode("strict")

    def ask(*a):
        raise AssertionError("в strict спрашивать нельзя")

    assert not permissions.check("python_run", args(code="print(1)"), ask=ask).allowed


def test_no_ask_function_means_deny():
    assert not permissions.check("python_run", args(code="print(1)"), ask=None).allowed


def test_safe_calls_pass_without_asking():
    def ask(*a):
        raise AssertionError("не должны спрашивать")

    assert permissions.check("sympy_simplify", args(expression="(a^2-b^2)/(a-b)"), ask=ask).allowed


def test_bad_json_is_left_for_registry():
    assert permissions.check("python_eval", "{expression:").allowed


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        permissions.set_mode("yolo")
