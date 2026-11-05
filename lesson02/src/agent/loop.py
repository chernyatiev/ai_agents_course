"""Цикл агента. По сравнению с занятием 1 изменилось только одно:
вместо `if name == "python_eval"` — вызов через реестр инструментов.

    while True:
        ответ = модель(история, tools.schemas())
        если в ответе нет вызовов инструментов: выход
        для каждого вызова: результат = tools.call(имя, аргументы)
"""
import json

from agent import llm, tools

SYSTEM_PROMPT = """Ты — помощник преподавателя математики (олимпиадные задачи, 5–9 класс).

Правила:
- Не считай и не решай в уме. Каждый ответ получай инструментом.
- Выбор инструмента:
  * python_eval — арифметика и перебор по небольшому диапазону;
  * sympy_solve — уравнения, системы уравнений, неравенства;
  * sympy_simplify — упрощение выражений;
  * z3_check — логические задачи (рыцари и лжецы), целочисленные условия,
    «найдите наименьшее/наибольшее», а также когда важно доказать единственность ответа.
- Если инструмент вернул ошибку, исправь вызов и попробуй снова.
- Если z3_check вернул unique=false, обязательно скажи, что у задачи несколько ответов,
  и приведи второй ответ.
Отвечай по-русски: ответ, каким инструментом он получен, короткое пояснение."""


def run_turn(messages: list[dict], chat=llm.chat, verbose: bool = False) -> str:
    """Один ход пользователя: крутит цикл, пока модель вызывает инструменты.

    `chat` передаётся параметром, чтобы в тестах подменить модель.
    """
    while True:
        reply = chat(messages, tools.schemas())
        tool_calls = reply.get("tool_calls") or []

        assistant_msg = {"role": "assistant", "content": reply.get("content") or ""}
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)
        _trace(verbose, assistant_msg)

        if not tool_calls:  # модель ответила текстом — ход закончен
            return assistant_msg["content"]

        for call in tool_calls:
            result = tools.call(call["function"]["name"], call["function"]["arguments"])
            tool_msg = {"role": "tool", "tool_call_id": call["id"], "content": result}
            messages.append(tool_msg)
            _trace(verbose, tool_msg)


def _trace(verbose: bool, message: dict) -> None:
    if verbose:
        print("  " + json.dumps(message, ensure_ascii=False))
