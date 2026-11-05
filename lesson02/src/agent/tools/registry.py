"""Реестр инструментов: имя -> (JSON-схема для модели, функция Python).

Главная идея занятия 2: цикл агента не меняется, когда появляется новый
инструмент. Новая возможность = новая запись в этой таблице.
"""
import json

# Таблица диспетчеризации. Ключ — имя инструмента, значение — словарь
# {"schema": <описание для модели>, "func": <функция Python>}.
_REGISTRY: dict[str, dict] = {}


def register(name: str, description: str, parameters: dict, func) -> None:
    """Регистрирует инструмент. Вызывается один раз при импорте модуля инструмента."""
    if name in _REGISTRY:
        raise ValueError(f"Инструмент {name} уже зарегистрирован")
    _REGISTRY[name] = {
        "schema": {
            "type": "function",
            "function": {"name": name, "description": description, "parameters": parameters},
        },
        "func": func,
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
        result = _REGISTRY[name]["func"](**args)
    except Exception as e:  # noqa: BLE001 — ошибку отдаём модели, а не пользователю
        return f"Ошибка {type(e).__name__}: {e}"
    return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
