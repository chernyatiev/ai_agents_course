"""Реестр инструментов: имя -> (JSON-схема для модели, функция Python).

Главная идея занятия 2: цикл агента не меняется, когда появляется новый
инструмент. Новая возможность = новая запись в этой таблице.

Занятие 3: при регистрации можно указать timeout — тогда функция инструмента
выполняется в отдельном процессе (sandbox.run_isolated) и не может повесить REPL.
"""
import json

from agent import sandbox

# Таблица диспетчеризации. Ключ — имя инструмента, значение — словарь
# {"schema": <описание для модели>, "func": <функция Python>}.
_REGISTRY: dict[str, dict] = {}


def register(name: str, description: str, parameters: dict, func, timeout: float | None = None) -> None:
    """Регистрирует инструмент. Вызывается один раз при импорте модуля инструмента.

    timeout — лимит времени в секундах. Если задан, func выполняется в песочнице
    (отдельный процесс). None — func вызывается напрямую, как на занятии 2.
    """
    if name in _REGISTRY:
        raise ValueError(f"Инструмент {name} уже зарегистрирован")
    _REGISTRY[name] = {
        "schema": {
            "type": "function",
            "function": {"name": name, "description": description, "parameters": parameters},
        },
        "func": func,
        "timeout": timeout,
    }


def schemas() -> list[dict]:
    """Описания всех инструментов — то, что уходит модели в поле `tools`."""
    return [entry["schema"] for entry in _REGISTRY.values()]


def names() -> list[str]:
    return list(_REGISTRY)


def call(name: str, arguments: str) -> str:
    """Выполняет вызов инструмента и ВСЕГДА возвращает строку.

    Любая ошибка (неизвестное имя, кривой JSON, исключение внутри
    инструмента) превращается в текст для модели — цикл не падает,
    а модель получает шанс исправиться.
    """
    if name not in _REGISTRY:
        return f"Ошибка: неизвестный инструмент {name}. Доступны: {', '.join(names())}"
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError as e:
        return f"Ошибка: аргументы не являются корректным JSON ({e})"
    try:
        entry = _REGISTRY[name]
        if entry["timeout"] is None:
            result = entry["func"](**args)
        else:
            result = sandbox.run_isolated(entry["func"], args, timeout=entry["timeout"])
    except Exception as e:  # noqa: BLE001 — ошибку отдаём модели, а не пользователю
        return f"Ошибка {type(e).__name__}: {e}"
    return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
