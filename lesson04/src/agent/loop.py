"""Цикл агента. Занятие 4 его НЕ меняет: банк задач — это новые инструменты
и файлы на диске, а цикл остаётся тем же, что в занятии 3.

    while True:
        ответ = модель(история, tools.schemas())
        если в ответе нет вызовов инструментов: выход
        для каждого вызова:
            решение = permissions.check(имя, аргументы, ask)   # ← новое
            результат = tools.call(...) если разрешено, иначе «Отказано: причина»
"""
import json

from agent import llm, permissions, tools

SYSTEM_PROMPT = """Ты — помощник преподавателя математики (олимпиадные задачи, 5–9 класс).

Правила:
- Не считай и не решай в уме. Каждый ответ получай инструментом.
- Выбор инструмента:
  * python_eval — арифметика и перебор по небольшому диапазону (одно выражение);
  * python_run — перебор, которому нужен скрипт (циклы, функции); результат печатай
    через print(). Запуск подтверждает пользователь, поэтому сначала подумай,
    нельзя ли обойтись python_eval, sympy_solve или z3_check;
  * sympy_solve — уравнения, системы уравнений, неравенства;
  * sympy_simplify — упрощение выражений;
  * z3_check — логические задачи (рыцари и лжецы), целочисленные условия,
    «найдите наименьшее/наибольшее», а также когда важно доказать единственность ответа.
- Если инструмент вернул ошибку, исправь вызов и попробуй снова.
- Если вызов «Отказано», не повторяй его в том же виде: реши задачу другим
  инструментом или объясни пользователю, что без этого вызова ответ не проверить.
- Если z3_check вернул unique=false, обязательно скажи, что у задачи несколько ответов,
  и приведи второй ответ.

Банк задач:
- Перед тем как придумать задачу, посмотри list_problems: не повторяйся.
- Сохраняй задачу через save_problem только после проверки инструментом и передай
  этот же вызов в verification. Harness повторит его сам.
- Не называй задачу проверенной, пока save_problem не вернул status=verified.
  Если вернул draft — сообщи причину и исправь формализацию или ответ.
- Утвердить задачу (approved) может только преподаватель командой /approve.
- Если у задачи есть review с комментарием преподавателя, учти его при исправлении.
Отвечай по-русски: ответ, каким инструментом он получен, короткое пояснение."""


def run_turn(messages: list[dict], chat=llm.chat, verbose: bool = False, ask=None) -> str:
    """Один ход пользователя: крутит цикл, пока модель вызывает инструменты.

    `chat` передаётся параметром, чтобы в тестах подменить модель.
    `ask(name, args, reason) -> "y"/"n"/"a"` — как спросить пользователя
    о подозрительном вызове. None — спросить некого, такие вызовы отклоняются.
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
            name, arguments = call["function"]["name"], call["function"]["arguments"]
            decision = permissions.check(name, arguments, ask=ask)  # ← занятие 3
            if decision.allowed:
                result = tools.call(name, arguments)
            else:
                result = f"Отказано: {decision.reason}"
                print(f"  ⛔ {name}: {decision.reason}")
            tool_msg = {"role": "tool", "tool_call_id": call["id"], "content": result}
            messages.append(tool_msg)
            _trace(verbose, tool_msg)


def _trace(verbose: bool, message: dict) -> None:
    if verbose:
        print("  " + json.dumps(message, ensure_ascii=False))
