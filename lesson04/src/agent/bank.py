"""Банк задач: одна задача = один JSON-файл в папке bank/.

Главная идея занятия 4: у агента появляется состояние ВНЕ контекста модели.
История `messages` исчезает после /reset или выхода, банк остаётся на диске.

Почему один файл на задачу (как .tasks/ в референсе s12):
- файл можно открыть и прочитать глазами;
- `git diff` показывает, что именно поменялось в задаче;
- испорченный файл ломает одну задачу, а не весь банк.

Модель никогда не передаёт путь к файлу — только id вида P-0007.
Путь строит этот модуль, поэтому записать что-то вне bank/ невозможно.
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

ID_RE = re.compile(r"^P-\d{4}$")
STATUSES = ("draft", "verified", "approved", "rejected")


def bank_dir() -> Path:
    """Папка банка. BANK_DIR читается при каждом вызове — так тесты подменяют её."""
    path = Path(os.getenv("BANK_DIR", "bank"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _path(problem_id: str) -> Path:
    if not isinstance(problem_id, str) or not ID_RE.match(problem_id):
        raise ValueError(f"Некорректный id {problem_id!r}: ожидается вид P-0001")
    return bank_dir() / f"{problem_id}.json"


def next_id() -> str:
    numbers = [int(p.stem[2:]) for p in bank_dir().glob("P-*.json") if ID_RE.match(p.stem)]
    return f"P-{max(numbers, default=0) + 1:04d}"


def exists(problem_id: str) -> bool:
    return _path(problem_id).exists()


def save(record: dict) -> None:
    """Атомарная запись: сначала во временный файл, потом мгновенная подмена.

    Если процесс упадёт посреди записи, старый файл останется целым —
    вместо него не окажется обрезанный JSON.
    """
    path = _path(record["id"])
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def get(problem_id: str) -> dict:
    path = _path(problem_id)
    if not path.exists():
        raise KeyError(f"Задача {problem_id} не найдена")
    return json.loads(path.read_text(encoding="utf-8"))


def list_all(grade: int | None = None, topic: str | None = None,
             status: str | None = None) -> tuple[list[dict], list[str]]:
    """Все задачи с фильтрами. Возвращает (задачи, имена испорченных файлов)."""
    records, broken = [], []
    for path in sorted(bank_dir().glob("P-*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            broken.append(path.name)  # один плохой файл не ломает весь банк
            continue
        if grade is not None and record.get("grade") != grade:
            continue
        if topic and topic.lower() not in (record.get("topic") or "").lower():
            continue
        if status and record.get("status") != status:
            continue
        records.append(record)
    return records, broken


def set_status(problem_id: str, status: str, comment: str | None = None) -> dict:
    """Смена статуса преподавателем (команды /approve и /reject в REPL)."""
    if status not in STATUSES:
        raise ValueError(f"Статус должен быть одним из {STATUSES}")
    record = get(problem_id)
    record["status"] = status
    record["review"] = {"status": status, "comment": comment, "at": now()}
    record["updated_at"] = now()
    save(record)
    return record


def summary() -> str:
    """Короткое оглавление банка для системного промпта (идея из s09 Memory).

    В промпт кладём не задачи целиком, а сводку: сколько, каких классов, какие темы.
    Полный текст модель получит по запросу через get_problem.
    """
    records, _ = list_all()
    if not records:
        return "Банк задач пуст."
    by_status = {s: sum(r.get("status") == s for r in records) for s in STATUSES}
    by_grade = {}
    for r in records:
        by_grade[r.get("grade")] = by_grade.get(r.get("grade"), 0) + 1
    topics = sorted({r.get("topic") for r in records if r.get("topic")})
    return (
        f"Задач в банке: {len(records)} ("
        + ", ".join(f"{s}: {n}" for s, n in by_status.items() if n)
        + "). По классам: "
        + ", ".join(f"{g} кл — {n}" for g, n in sorted(by_grade.items(), key=lambda kv: str(kv[0])))
        + ". Темы: " + ", ".join(topics[:20]) + "."
    )
