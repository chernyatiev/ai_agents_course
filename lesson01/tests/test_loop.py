"""Тесты без сети: модель подменяется заранее записанными ответами."""
import json

import pytest

from agent.loop import SYSTEM_PROMPT, python_eval, run_turn


def make_fake_chat(replies):
    """Возвращает функцию chat(), которая по очереди отдаёт заготовленные ответы."""
    replies = list(replies)
    seen = []

    def fake_chat(messages, tools):
        seen.append([dict(m) for m in messages])
        return replies.pop(0)

    fake_chat.seen = seen
    return fake_chat


def tool_call(expression, call_id="call_1"):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": call_id,
            "type": "function",
            "function": {"name": "python_eval",
                         "arguments": json.dumps({"expression": expression})},
        }],
    }


def test_python_eval_counts_three_digit_multiples_of_7():
    assert python_eval("sum(1 for n in range(100, 1000) if n % 7 == 0)") == "128"


def test_python_eval_names_visible_inside_generator():
    assert python_eval("sum(1 for n in range(-5, 6) if abs(n) > 3)") == "4"


def test_python_eval_has_math():
    assert python_eval("math.gcd(84, 36)") == "12"


def test_python_eval_has_no_import():
    with pytest.raises(NameError):
        python_eval("__import__('os')")


def test_two_iterations_of_the_loop():
    chat = make_fake_chat([
        tool_call("sum(1 for n in range(100, 1000) if n % 7 == 0)"),
        {"role": "assistant", "content": "128 трёхзначных чисел делятся на 7."},
    ])
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Сколько трёхзначных чисел делятся на 7?"},
    ]

    answer = run_turn(messages, chat=chat)

    assert answer == "128 трёхзначных чисел делятся на 7."
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool", "assistant"]
    assert messages[3] == {"role": "tool", "tool_call_id": "call_1", "content": "128"}
    # Во второй вызов модель уже видит результат инструмента.
    assert chat.seen[1][-1]["content"] == "128"


def test_text_answer_without_tools_ends_turn_immediately():
    chat = make_fake_chat([{"role": "assistant", "content": "Привет!"}])
    messages = [{"role": "user", "content": "Привет"}]
    assert run_turn(messages, chat=chat) == "Привет!"
    assert len(chat.seen) == 1
