"""Проверка, которую можно воспроизвести.

Модель УТВЕРЖДАЕТ, что проверила ответ. Harness не верит на слово: при сохранении
задачи он сам заново запускает проверочный вызов и сравнивает результат с ответом.
Статус verified ставит только этот модуль, а не модель.

Повторный запуск идёт тем же путём, что и обычный вызов модели:
разрешения (permissions.check) -> реестр -> песочница.
"""
import json

from agent import permissions, tools

# Чем можно подтвердить ответ. python_run не входит: каждый запуск скрипта требует
# подтверждения пользователя, а проверка при сохранении должна идти без вопросов.
VERIFY_TOOLS = ("python_eval", "sympy_solve", "z3_check")


def run(tool: str, arguments: dict, answer: dict) -> dict:
    """Перезапускает проверку и сравнивает с ответом.

    Возвращает {"ok": bool, "reason": str, "result": <что вернул инструмент>}.
    """
    if tool not in VERIFY_TOOLS:
        return {"ok": False, "reason": f"проверять можно только через {', '.join(VERIFY_TOOLS)}",
                "result": None}

    arguments_json = json.dumps(arguments, ensure_ascii=False)
    # ask=None: при сохранении спросить некого — вызов, которому нужно
    # подтверждение, будет отклонён, и задача останется черновиком.
    decision = permissions.check(tool, arguments_json, ask=None)
    if not decision.allowed:
        return {"ok": False, "reason": f"проверка отклонена: {decision.reason}", "result": None}

    raw = tools.call(tool, arguments_json)
    if raw.startswith("Ошибка"):
        return {"ok": False, "reason": raw, "result": None}
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = raw  # python_eval возвращает просто строку

    ok, reason = matches(tool, result, answer)
    return {"ok": ok, "reason": reason, "result": result}


def matches(tool: str, result, answer: dict) -> tuple[bool, str]:
    """Совпадает ли результат инструмента с ответом задачи. Своё правило для каждого."""
    if not isinstance(answer, dict) or not answer:
        return False, "ответ должен быть непустым словарём"

    if tool == "python_eval":
        expected = str(answer.get("value", "")).strip()
        if str(result).strip() == expected:
            return True, "значение выражения совпадает с ответом"
        return False, f"python_eval вернул {result}, а в ответе {expected}"

    if tool == "z3_check":
        if result.get("status") != "sat":
            return False, f"z3 не нашёл решения (status={result.get('status')})"
        if result.get("unique") is not True:
            return False, ("решение не единственно, второе: "
                           f"{result.get('another_solution')}" if result.get("unique") is False
                           else "z3 не успел доказать единственность")
        return _compare(result["solution"], answer, "z3")

    if tool == "sympy_solve":
        if result.get("kind") != "equations":
            return False, "неравенства пока не проверяются, используйте z3_check"
        if result.get("count") != 1:
            return False, f"у системы {result.get('count')} решений, а нужно ровно одно"
        return _compare(result["solutions"][0], answer, "SymPy")

    return False, f"нет правила сравнения для {tool}"


def _compare(solution: dict, answer: dict, who: str) -> tuple[bool, str]:
    """Сравнивает только переменные, указанные в ответе: вспомогательные можно не писать."""
    for name, value in answer.items():
        if name not in solution:
            return False, f"в решении {who} нет переменной {name}"
        if str(solution[name]) != str(value):
            return False, f"{who}: {name} = {solution[name]}, а в ответе {value}"
    return True, f"ответ совпадает с решением {who}, решение единственно"
