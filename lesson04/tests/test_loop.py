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
    assert names == {"python_eval", "python_run", "sympy_solve", "sympy_simplify", "z3_check",
                                  "save_problem", "list_problems", "get_problem"}


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


# ---------- занятие 3: разрешения в цикле ----------

ESCAPE = "[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'Popen']"


def test_denied_call_is_not_executed_and_model_sees_reason():
    chat = make_fake_chat([
        tool_call("python_eval", {"expression": ESCAPE}),
        {"role": "assistant", "content": "Не могу выполнить такой вызов."},
    ])
    messages = history("Покажи классы интерпретатора")
    run_turn(messages, chat=chat)
    assert messages[3]["content"].startswith("Отказано: запрещено политикой")
    assert "Popen" not in messages[3]["content"]


def test_ask_yes_runs_script():
    asked = []

    def ask(name, args, reason):
        asked.append((name, reason))
        return "y"

    chat = make_fake_chat([
        tool_call("python_run", {"code": "print(sum(range(101)))"}),
        {"role": "assistant", "content": "5050"},
    ])
    messages = history("Сумма от 0 до 100 скриптом")
    run_turn(messages, chat=chat, ask=ask)
    assert asked == [("python_run", "Запуск скрипта Python")]
    assert json.loads(messages[3]["content"])["stdout"] == "5050\n"


def test_ask_no_model_switches_tool():
    chat = make_fake_chat([
        tool_call("python_run", {"code": "print(sum(range(101)))"}, call_id="c1"),
        tool_call("python_eval", {"expression": "sum(range(101))"}, call_id="c2"),
        {"role": "assistant", "content": "5050"},
    ])
    messages = history("Сумма от 0 до 100")
    assert run_turn(messages, chat=chat, ask=lambda *a: "n") == "5050"
    assert messages[3]["content"].startswith("Отказано: пользователь отклонил")
    assert messages[5]["content"] == "5050"


def test_safe_call_never_asks():
    def ask(*a):
        raise AssertionError("безопасный вызов не должен спрашивать")

    chat = make_fake_chat([
        tool_call("sympy_solve", {"equations": ["x + 1 = 3"], "variables": ["x"]}),
        {"role": "assistant", "content": "x = 2"},
    ])
    run_turn(history("x + 1 = 3"), chat=chat, ask=ask)
