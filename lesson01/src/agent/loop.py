"""Цикл агента: модель -> инструмент -> результат обратно в messages.

    while True:
        ответ = модель(история, инструменты)
        если в ответе нет вызовов инструментов: выход
        выполнить инструменты, добавить результаты в историю
"""
import builtins
import json
import math

from agent import llm

SYSTEM_PROMPT = """Ты — помощник преподавателя математики (олимпиадные задачи, 5–9 класс).
Не считай в уме. Любое вычисление выполняй инструментом python_eval:
запиши его одним выражением Python и используй полученный результат.
Отвечай по-русски, кратко: ответ и короткое пояснение."""

# Описание инструмента для модели (JSON Schema в формате OpenAI tools).
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "python_eval",
            "description": (
                "Вычисляет одно выражение Python и возвращает результат. "
                "Доступны: range, sum, len, min, max, abs, all, any, "
                "list, set, sorted, divmod, pow, round и модуль math. "
                "Пример: sum(1 for n in range(100, 1000) if n % 7 == 0)"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Выражение Python (не инструкция)",
                    }
                },
                "required": ["expression"],
            },
        },
    }
]

# Пространство имён для eval. ВНИМАНИЕ: это не песочница —
# изоляцию сделаем на занятии 3. Пока ограничиваем только видимые имена.
_SAFE_NAMES = {
    name: getattr(builtins, name)
    for name in (
        "range", "sum", "len", "min", "max", "abs", "all", "any",
        "list", "set", "sorted", "divmod", "pow", "round", "int", "str",
    )
}
_SAFE_NAMES["math"] = math


def python_eval(expression: str) -> str:
    """Единственный инструмент занятия 1."""
    # Имена кладём в globals: из locals их не увидят генераторные выражения.
    result = eval(expression, {"__builtins__": {}, **_SAFE_NAMES})
    return str(result)


def run_turn(messages: list[dict], chat=llm.chat, verbose: bool = False) -> str:
    """Один ход пользователя: крутит цикл, пока модель вызывает инструменты.

    `chat` передаётся параметром, чтобы в тестах подменить модель.
    """
    while True:
        reply = chat(messages, TOOLS)
        tool_calls = reply.get("tool_calls") or []

        assistant_msg = {"role": "assistant", "content": reply.get("content") or ""}
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)
        _trace(verbose, assistant_msg)

        if not tool_calls:  # модель ответила текстом — ход закончен
            return assistant_msg["content"]

        for call in tool_calls:
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"] or "{}")
            if name == "python_eval":
                result = python_eval(**args)
            else:
                result = f"Неизвестный инструмент: {name}"
            tool_msg = {"role": "tool", "tool_call_id": call["id"], "content": result}
            messages.append(tool_msg)
            _trace(verbose, tool_msg)


def _trace(verbose: bool, message: dict) -> None:
    if verbose:
        print("  " + json.dumps(message, ensure_ascii=False))
