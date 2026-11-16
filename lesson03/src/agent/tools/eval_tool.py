"""python_eval — вычисление одного выражения Python (перенесён из занятия 1)."""
import builtins
import math

from agent.tools.registry import register

# Список имён — только первая линия обороны. Обход через ().__class__... ловят
# разрешения (ворота 1, AST), зависание — песочница (timeout при регистрации).
_SAFE_NAMES = {
    name: getattr(builtins, name)
    for name in (
        "range", "sum", "len", "min", "max", "abs", "all", "any",
        "list", "set", "sorted", "divmod", "pow", "round", "int", "str",
    )
}
_SAFE_NAMES["math"] = math


def python_eval(expression: str) -> str:
    # Имена кладём в globals: из locals их не увидят генераторные выражения.
    return str(eval(expression, {"__builtins__": {}, **_SAFE_NAMES}))


register(
    name="python_eval",
    description=(
        "Вычисляет одно выражение Python и возвращает результат. "
        "Подходит для арифметики и перебора по небольшому диапазону (одно выражение). "
        "Доступны: range, sum, len, min, max, abs, all, any, list, set, sorted, "
        "divmod, pow, round, int, str и модуль math. "
        "Пример: sum(1 for n in range(100, 1000) if n % 7 == 0)"
    ),
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Выражение Python (не инструкция)"},
        },
        "required": ["expression"],
    },
    func=python_eval,
    timeout=5,
)
