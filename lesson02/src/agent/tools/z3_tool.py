"""z3_check — поиск решения в SMT-солвере z3 с проверкой единственности.

Для олимпиадных задач важно не только найти ответ, но и доказать, что он
единственный. Приём: найдя решение m, добавляем ограничение «решение не равно m»
и запускаем солвер ещё раз. Ответ unsat означает, что других решений нет.
"""
import z3

from agent.tools.registry import register

TIMEOUT_MS = 10_000

_TYPES = {"Int": z3.Int, "Bool": z3.Bool, "Real": z3.Real}

# Имена, доступные внутри строк-ограничений (кроме самих переменных).
_HELPERS = {
    "And": z3.And, "Or": z3.Or, "Not": z3.Not, "Implies": z3.Implies,
    "If": z3.If, "Distinct": z3.Distinct, "Sum": z3.Sum, "Xor": z3.Xor,
}


def _value(model: z3.ModelRef, var):
    """Значение переменной из модели в виде обычного числа/булева."""
    v = model.eval(var, model_completion=True)
    if z3.is_int_value(v):
        return v.as_long()
    if z3.is_true(v) or z3.is_false(v):
        return z3.is_true(v)
    return str(v)  # Real: дробь вида 7/2


def z3_check(
    variables: dict,
    constraints: list[str],
    minimize: str | None = None,
    maximize: str | None = None,
    check_unique: bool = True,
) -> dict:
    # 1. Переменные: {"x": "Int", "A": "Bool"} -> объекты z3.
    z3_vars = {}
    for name, type_name in variables.items():
        if type_name not in _TYPES:
            raise ValueError(f"Тип {type_name} не поддерживается, используйте {list(_TYPES)}")
        z3_vars[name] = _TYPES[type_name](name)

    # 2. Ограничения: строки Python -> выражения z3.
    #    ВНИМАНИЕ: eval без изоляции — песочница на занятии 3.
    namespace = {"__builtins__": {}, **_HELPERS, **z3_vars}
    exprs = [eval(c, namespace) for c in constraints]
    objective_text = minimize or maximize
    objective = eval(objective_text, namespace) if objective_text else None

    # 3. Первое решение (с оптимизацией, если она нужна).
    solver = z3.Optimize() if objective is not None else z3.Solver()
    solver.set("timeout", TIMEOUT_MS)
    solver.add(*exprs)
    if minimize:
        solver.minimize(objective)
    elif maximize:
        solver.maximize(objective)

    status = solver.check()
    if status != z3.sat:
        return {"status": str(status)}  # "unsat" — решений нет, "unknown" — солвер не справился

    model = solver.model()
    solution = {name: _value(model, var) for name, var in z3_vars.items()}
    result = {"status": "sat", "solution": solution}
    if objective is not None:
        result["objective_value"] = _value(model, objective)

    if not check_unique:
        return result

    # 4. Проверка единственности: ищем другое решение с тем же значением цели.
    second = z3.Solver()
    second.set("timeout", TIMEOUT_MS)
    second.add(*exprs)
    if objective is not None:
        second.add(objective == model.eval(objective, model_completion=True))
    second.add(z3.Not(z3.And([var == model.eval(var, model_completion=True) for var in z3_vars.values()])))

    second_status = second.check()
    if second_status == z3.unsat:
        result["unique"] = True
    elif second_status == z3.sat:
        result["unique"] = False
        other = second.model()
        result["another_solution"] = {name: _value(other, var) for name, var in z3_vars.items()}
    else:
        result["unique"] = None  # солвер не успел доказать
    return result


register(
    name="z3_check",
    description=(
        "Ищет решение задачи с ограничениями в SMT-солвере z3 и проверяет, единственно ли оно. "
        "Подходит для логических задач (рыцари и лжецы: Bool, True = рыцарь), целочисленных "
        "условий, задач «найдите наименьшее/наибольшее». Ограничения — выражения Python над "
        "переменными; доступны And, Or, Not, Implies, If, Distinct, Sum, Xor, операторы "
        "==, !=, <, %, +, *. Пример: variables={'n': 'Int'}, constraints=['n > 1', 'n % 3 == 1'], "
        "minimize='n'. Ответ: status (sat/unsat/unknown), solution, unique, another_solution."
    ),
    parameters={
        "type": "object",
        "properties": {
            "variables": {
                "type": "object",
                "additionalProperties": {"type": "string", "enum": list(_TYPES)},
                "description": "Имя переменной -> тип: Int, Bool или Real",
            },
            "constraints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ограничения, например ['A == Not(B)', 'x + y == 10']",
            },
            "minimize": {"type": "string", "description": "Выражение, которое нужно минимизировать"},
            "maximize": {"type": "string", "description": "Выражение, которое нужно максимизировать"},
            "check_unique": {
                "type": "boolean",
                "description": "Проверять ли единственность решения (по умолчанию true)",
            },
        },
        "required": ["variables", "constraints"],
    },
    func=z3_check,
)
