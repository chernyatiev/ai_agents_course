"""python_run — многострочный скрипт Python для перебора (новый на занятии 3).

python_eval считает одно выражение. Олимпиадные задачи часто удобнее проверить
перебором с циклами и функциями — для этого нужен целый скрипт. Такой инструмент
по-настоящему опасен, поэтому:
- перед запуском harness спрашивает пользователя (правило в permissions.py);
- код выполняется в отдельном процессе с таймаутом и лимитами (sandbox.py).
"""
from agent import sandbox
from agent.tools.registry import register

DEFAULT_TIMEOUT = 5
MAX_TIMEOUT = 30


def python_run(code: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    if not 1 <= timeout <= MAX_TIMEOUT:
        raise ValueError(f"timeout должен быть от 1 до {MAX_TIMEOUT} секунд")
    return sandbox.run_python(code, timeout=timeout)


register(
    name="python_run",
    description=(
        "Выполняет скрипт Python в песочнице и возвращает то, что он напечатал. "
        "Используй для перебора, который не помещается в одно выражение python_eval "
        "(циклы, функции, несколько шагов). Результат обязательно выводи через print(). "
        "Можно импортировать: math, itertools, functools, collections, fractions, sympy, z3 и др. "
        "Нельзя: файлы, сеть, os, sys, subprocess. Запуск требует подтверждения пользователя. "
        "Ответ: stdout, stderr, returncode, timed_out."
    ),
    parameters={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Текст скрипта Python"},
            "timeout": {
                "type": "integer",
                "description": f"Лимит времени в секундах (по умолчанию {DEFAULT_TIMEOUT}, максимум {MAX_TIMEOUT})",
            },
        },
        "required": ["code"],
    },
    func=python_run,
)
