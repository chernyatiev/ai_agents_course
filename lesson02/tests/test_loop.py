"""Тесты цикла без сети: модель подменяется заранее записанными ответами."""
import json

from agent.loop import SYSTEM_PROMPT, run_turn


def make_fake_chat(replies):
    """Возвращает функцию chat(), которая по очереди отдаёт заготовленные ответы."""
    replies = list(replies)
    seen = []

    def fake_chat(messages, tools):
        seen.append({"messages": [dict(m) for m in messages], "tools": tools})
        return replies.pop(0)

    fake_chat.seen = seen
    return fake_chat


def tool_call(name, args, call_id="call_1"):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": call_id,
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)},
        }],
    }


def history(question):
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]


def test_model_receives_all_tool_schemas():
    chat = make_fake_chat([{"role": "assistant", "content": "ok"}])
    run_turn(history("привет"), chat=chat)
    names = {t["function"]["name"] for t in chat.seen[0]["tools"]}
    assert names == {"python_eval", "sympy_solve", "sympy_simplify", "z3_check"}


def test_dispatch_to_z3():
    chat = make_fake_chat([
        tool_call("z3_check", {"variables": {"A": "Bool", "B": "Bool"},
                               "constraints": ["A == Not(B)", "B == (A == B)"]}),
        {"role": "assistant", "content": "A — рыцарь, B — лжец; решение единственно."},
    ])
    messages = history("Рыцари и лжецы ...")
    run_turn(messages, chat=chat)
    result = json.loads(messages[3]["content"])
    assert result["solution"] == {"A": True, "B": False}
    assert result["unique"] is True


def test_tool_error_goes_back_to_model_and_it_retries():
    chat = make_fake_chat([
        tool_call("python_eval", {"expression": "sum(range(1, 101)"}, call_id="c1"),   # скобка
        tool_call("python_eval", {"expression": "sum(range(1, 101))"}, call_id="c2"),
        {"role": "assistant", "content": "5050"},
    ])
    messages = history("Сумма чисел от 1 до 100?")
    assert run_turn(messages, chat=chat) == "5050"
    assert messages[3]["content"].startswith("Ошибка SyntaxError")
    assert messages[5]["content"] == "5050"
    # Модель увидела текст ошибки перед второй попыткой.
    assert chat.seen[1]["messages"][-1]["content"].startswith("Ошибка SyntaxError")


def test_two_tool_calls_in_one_reply():
    reply = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": "a", "type": "function",
             "function": {"name": "python_eval", "arguments": json.dumps({"expression": "2**10"})}},
            {"id": "b", "type": "function",
             "function": {"name": "sympy_simplify", "arguments": json.dumps({"expression": "(x^2-1)/(x-1)"})}},
        ],
    }
    chat = make_fake_chat([reply, {"role": "assistant", "content": "готово"}])
    messages = history("два вычисления")
    run_turn(messages, chat=chat)
    assert [m["content"] for m in messages if m["role"] == "tool"] == ["1024", "x + 1"]
