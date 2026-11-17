"""Инструменты банка задач: save_problem, list_problems, get_problem.

Обратите внимание, чего здесь НЕТ:
- аргумента «путь к файлу» — только id, путь строит bank.py;
- аргумента status — verified ставит harness после проверки, approved и
  rejected ставит только преподаватель командой в REPL;
- инструмента удаления.
Самое надёжное разрешение — инструмент, которым нельзя сделать опасное.
"""
from agent import bank, verify
from agent.tools.registry import register


def save_problem(
    title: str,
    grade: int,
    topic: str,
    statement: str,
    answer: dict,
    solution: str,
    verification: dict,
    id: str | None = None,  # noqa: A002 — так поле называется в схеме для модели
) -> dict:
    if not isinstance(grade, int) or not 5 <= grade <= 9:
        raise ValueError("grade — номер класса от 5 до 9")
    if not statement.strip():
        raise ValueError("Условие задачи пустое")
    if not isinstance(verification, dict) or "tool" not in verification:
        raise ValueError("verification должен быть {'tool': ..., 'arguments': {...}}")

    if id is None:
        record = {"id": bank.next_id(), "created_at": bank.now()}
    else:
        record = bank.get(id)  # KeyError, если такой задачи нет

    check = verify.run(verification["tool"], verification.get("arguments") or {}, answer)
    record.update({
        "title": title,
        "grade": grade,
        "topic": topic,
        "statement": statement,
        "answer": answer,
        "solution": solution,
        "verification": {
            "tool": verification["tool"],
            "arguments": verification.get("arguments") or {},
            "result": check["result"],
            "ok": check["ok"],
            "reason": check["reason"],
            "checked_at": bank.now(),
        },
        # Любое изменение сбрасывает решение преподавателя: утверждали другую задачу.
        "status": "verified" if check["ok"] else "draft",
        "review": None,
        "updated_at": bank.now(),
    })
    bank.save(record)
    return {
        "id": record["id"],
        "status": record["status"],
        "verification": {"ok": check["ok"], "reason": check["reason"]},
    }


def list_problems(grade: int | None = None, topic: str | None = None,
                  status: str | None = None) -> dict:
    records, broken = bank.list_all(grade=grade, topic=topic, status=status)
    result = {
        "count": len(records),
        "problems": [
            {k: r.get(k) for k in ("id", "title", "grade", "topic", "status")} for r in records
        ],
    }
    if broken:
        result["broken_files"] = broken
    return result


def get_problem(id: str) -> dict:  # noqa: A002
    return bank.get(id)


register(
    name="save_problem",
    description=(
        "Сохраняет задачу в банк. Перед сохранением реши задачу инструментом и передай "
        "этот вызов в verification — harness сам повторит его и сравнит с answer. "
        "Если совпало (а для z3 — ещё и решение единственно), статус станет verified, "
        "иначе draft. Статус approved ставит только преподаватель. "
        "answer: для z3_check и sympy_solve — словарь {переменная: значение}, "
        "для python_eval — {'value': 'результат'}. "
        "Чтобы изменить существующую задачу, передай её id (потребуется подтверждение). "
        "Пример verification: {'tool': 'z3_check', 'arguments': {'variables': {'n': 'Int'}, "
        "'constraints': ['n > 1', 'n % 3 == 1'], 'minimize': 'n'}}."
    ),
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Короткое название"},
            "grade": {"type": "integer", "description": "Класс: от 5 до 9"},
            "topic": {"type": "string", "description": "Тема: делимость, логика, уравнения, ..."},
            "statement": {"type": "string", "description": "Условие задачи для ученика"},
            "answer": {"type": "object", "description": "Ответ, см. описание инструмента"},
            "solution": {"type": "string", "description": "Решение для преподавателя"},
            "verification": {
                "type": "object",
                "description": "Проверочный вызов: {'tool': 'z3_check' | 'sympy_solve' | 'python_eval', "
                               "'arguments': {...}}",
                "properties": {
                    "tool": {"type": "string", "enum": list(verify.VERIFY_TOOLS)},
                    "arguments": {"type": "object"},
                },
                "required": ["tool", "arguments"],
            },
            "id": {"type": "string", "description": "id существующей задачи (P-0001), только для изменения"},
        },
        "required": ["title", "grade", "topic", "statement", "answer", "solution", "verification"],
    },
    func=save_problem,
)

register(
    name="list_problems",
    description=(
        "Список задач из банка (id, название, класс, тема, статус) с необязательными "
        "фильтрами. Используй, чтобы не придумывать задачу, которая уже есть."
    ),
    parameters={
        "type": "object",
        "properties": {
            "grade": {"type": "integer", "description": "Класс, 5–9"},
            "topic": {"type": "string", "description": "Часть названия темы"},
            "status": {"type": "string", "enum": list(bank.STATUSES)},
        },
    },
    func=list_problems,
)

register(
    name="get_problem",
    description=(
        "Полная запись задачи по id: условие, ответ, решение, проверка и отзыв "
        "преподавателя (review), если задачу отклонили."
    ),
    parameters={
        "type": "object",
        "properties": {"id": {"type": "string", "description": "id задачи, например P-0001"}},
        "required": ["id"],
    },
    func=get_problem,
)
