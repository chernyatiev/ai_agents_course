"""Тесты песочницы: отдельный процесс, таймаут, пустое окружение."""
import json
import os

import pytest

from agent import sandbox, tools


def slow_function(seconds):
    import time
    time.sleep(seconds)
    return "done"


def failing_function():
    raise ValueError("плохие аргументы")


def unusual_error():
    class MyError(Exception):
        pass
    raise MyError("своя ошибка")


# ---------- run_python (python_run) ----------

def test_run_python_returns_stdout():
    r = sandbox.run_python("print(sum(range(101)))")
    assert r == {"timed_out": False, "returncode": 0, "stdout": "5050\n", "stderr": ""}


def test_run_python_reports_exception_in_stderr():
    r = sandbox.run_python("1/0")
    assert r["returncode"] != 0 and "ZeroDivisionError" in r["stderr"]


def test_run_python_infinite_loop_is_killed():
    r = sandbox.run_python("while True: pass", timeout=1)
    assert r["timed_out"] is True


def test_run_python_does_not_see_api_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "secret-key")
    r = sandbox.run_python("import os; print(os.environ.get('LLM_API_KEY'))")
    assert r["stdout"].strip() == "None"


def test_run_python_works_in_temp_dir():
    r = sandbox.run_python("import os; print(os.getcwd())")
    assert r["stdout"].strip() != os.getcwd()
    assert "agent_sandbox_" in r["stdout"]


def test_run_python_output_is_truncated():
    r = sandbox.run_python("print('x' * 100_000)")
    assert len(r["stdout"]) < 5000 and "обрезано" in r["stdout"]


# ---------- run_isolated (python_eval, SymPy, z3) ----------

def test_run_isolated_returns_result():
    assert sandbox.run_isolated(slow_function, {"seconds": 0}) == "done"


def test_run_isolated_timeout():
    with pytest.raises(TimeoutError):
        sandbox.run_isolated(slow_function, {"seconds": 5}, timeout=1)


def test_run_isolated_keeps_builtin_error_type():
    with pytest.raises(ValueError, match="плохие аргументы"):
        sandbox.run_isolated(failing_function, {})


def test_run_isolated_unknown_error_type():
    with pytest.raises(RuntimeError, match="MyError: своя ошибка"):
        sandbox.run_isolated(unusual_error, {})


# ---------- через реестр ----------

def test_hanging_eval_does_not_hang_agent():
    out = tools.call("python_eval", json.dumps({"expression": "sum(range(10**12))"}))
    assert out.startswith("Ошибка TimeoutError")


def test_python_run_through_registry():
    out = json.loads(tools.call("python_run", json.dumps({"code": "print(2**10)"})))
    assert out["stdout"] == "1024\n"


def test_python_run_rejects_huge_timeout():
    out = tools.call("python_run", json.dumps({"code": "print(1)", "timeout": 999}))
    assert out.startswith("Ошибка ValueError")
