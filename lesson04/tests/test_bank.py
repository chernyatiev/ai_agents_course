"""Тесты банка задач, проверки и сохранённых разрешений — без LLM и без сети."""
import json

import pytest

from agent import bank, main, permissions, tools, verify
from agent.loop import SYSTEM_PROMPT, run_turn
from agent.tools.bank_tools import save_problem

CRT = {  # наименьшее n > 1 с остатком 1 при делении на 3, 4, 5 — это 61
    "tool": "z3_check",
    "arguments": {"variables": {"n": "Int"},
                  "constraints": ["n > 1", "n % 3 == 1", "n % 4 == 1", "n % 5 == 1"],
                  "minimize": "n"},
}


def problem(**overrides):
    data = {
        "title": "Остатки 3, 4, 5",
        "grade": 6,
        "topic": "делимость",
        "statement": "Найдите наименьшее натуральное n > 1, которое при делении на 3, 4 и 5 даёт остаток 1.",
        "answer": {"n": 61},
        "solution": "n − 1 делится на НОК(3, 4, 5) = 60, значит n = 61.",
        "verification": CRT,
    }
    data.update(overrides)
    return data


# ---------- хранилище ----------

def test_save_and_get_roundtrip():
    out = save_problem(**problem())
    assert out == {"id": "P-0001", "status": "verified",
                   "verification": {"ok": True, "reason": "ответ совпадает с решением z3, решение единственно"}}
    record = bank.get("P-0001")
    assert record["answer"] == {"n": 61}
    assert record["verification"]["result"]["solution"] == {"n": 61}
    assert (bank.bank_dir() / "P-0001.json").exists()


def test_ids_grow():
    save_problem(**problem())
    save_problem(**problem(title="Вторая"))
    assert [r["id"] for r in bank.list_all()[0]] == ["P-0001", "P-0002"]


def test_bank_survives_restart():
    """«Перезапуск» = новый вызов функций модуля: всё читается с диска."""
    save_problem(**problem())
    records, _ = bank.list_all()
    assert records[0]["title"] == "Остатки 3, 4, 5"


@pytest.mark.parametrize("bad_id", ["../.env", "P-0001/../../x", "p-1", "P-00001", "", None])
def test_bad_ids_rejected(bad_id):
    with pytest.raises(ValueError):
        bank.get(bad_id)


def test_missing_problem():
    with pytest.raises(KeyError):
        bank.get("P-0042")


def test_broken_file_does_not_break_bank():
    save_problem(**problem())
    (bank.bank_dir() / "P-0002.json").write_text("{не json", encoding="utf-8")
    records, broken = bank.list_all()
    assert [r["id"] for r in records] == ["P-0001"]
    assert broken == ["P-0002.json"]


def test_atomic_write_leaves_no_temp_files():
    save_problem(**problem())
    assert [p.name for p in bank.bank_dir().iterdir()] == ["P-0001.json"]


def test_filters():
    save_problem(**problem())
    save_problem(**problem(grade=8, topic="логика"))
    assert len(bank.list_all(grade=8)[0]) == 1
    assert len(bank.list_all(topic="делим")[0]) == 1
    assert len(bank.list_all(status="approved")[0]) == 0


def test_summary_for_system_prompt():
    assert bank.summary() == "Банк задач пуст."
    save_problem(**problem())
    assert "Задач в банке: 1" in bank.summary() and "делимость" in bank.summary()
    assert "Состояние банка" in main.system_prompt()


# ---------- воспроизводимая проверка ----------

def test_wrong_answer_stays_draft():
    out = save_problem(**problem(answer={"n": 60}))
    assert out["status"] == "draft"
    assert "n = 61, а в ответе 60" in out["verification"]["reason"]


def test_not_unique_stays_draft():
    two = {"tool": "z3_check",
           "arguments": {"variables": {"x": "Int", "y": "Int"}, "constraints": ["x > 0", "y > 0", "x + y == 10"]}}
    out = save_problem(**problem(answer={"x": 1, "y": 9}, verification=two))
    assert out["status"] == "draft" and "не единственно" in out["verification"]["reason"]


def test_sympy_verification():
    v = {"tool": "sympy_solve", "arguments": {"equations": ["x + y = 10", "x - y = 2"], "variables": ["x", "y"]}}
    assert save_problem(**problem(answer={"x": 6, "y": 4}, verification=v))["status"] == "verified"


def test_python_eval_verification():
    v = {"tool": "python_eval", "arguments": {"expression": "sum(1 for n in range(100, 1000) if n % 7 == 0)"}}
    assert save_problem(**problem(answer={"value": 128}, verification=v))["status"] == "verified"


def test_python_run_is_not_a_verification_tool():
    v = {"tool": "python_run", "arguments": {"code": "print(61)"}}
    out = save_problem(**problem(verification=v))
    assert out["status"] == "draft"


def test_verification_goes_through_permissions():
    """Эксплойт, спрятанный в проверке, останавливают ворота 1."""
    v = {"tool": "z3_check", "arguments": {"variables": {"n": "Int"},
                                           "constraints": ["n == ().__class__.__base__.__subclasses__().__len__()"]}}
    out = save_problem(**problem(verification=v))
    assert out["status"] == "draft" and "запрещено политикой" in out["verification"]["reason"]


def test_formalization_error_is_not_caught():
    """Задел на занятие 5: условие про остаток 2, а формализация — про остаток 1.

    Проверка воспроизводится, поэтому задача получает verified, хотя ответ к
    такому условию неверный. verified ≠ «задача правильная».
    """
    out = save_problem(**problem(statement="Найдите наименьшее n > 2, дающее остаток 2 при делении на 3, 4 и 5."))
    assert out["status"] == "verified"


# ---------- права: модель, harness, преподаватель ----------

def test_model_cannot_set_status():
    out = tools.call("save_problem", json.dumps({**problem(), "status": "approved"}, ensure_ascii=False))
    assert out.startswith("Ошибка TypeError")
    assert bank.list_all()[0] == []


def test_no_tool_can_approve_or_delete():
    for schema in tools.schemas():
        props = schema["function"]["parameters"].get("properties", {})
        assert "status" not in props or schema["function"]["name"] == "list_problems"
        assert "path" not in props
    assert not any("delete" in n or "approve" in n for n in tools.names())


def test_teacher_approves_and_change_resets_approval():
    save_problem(**problem())
    main.approve("P-0001")
    assert bank.get("P-0001")["status"] == "approved"
    save_problem(**problem(title="Новое название"), id="P-0001")
    record = bank.get("P-0001")
    assert record["status"] == "verified" and record["review"] is None


def test_approve_requires_verified(capsys):
    save_problem(**problem(answer={"n": 60}))
    main.approve("P-0001")
    assert bank.get("P-0001")["status"] == "draft"
    assert "только verified" in capsys.readouterr().out


def test_reject_comment_visible_to_model():
    save_problem(**problem())
    main.handle_command("/reject P-0001 слишком просто для 6 класса")
    out = json.loads(tools.call("get_problem", json.dumps({"id": "P-0001"})))
    assert out["status"] == "rejected"
    assert out["review"]["comment"] == "слишком просто для 6 класса"


def test_update_unknown_id_is_error():
    out = tools.call("save_problem", json.dumps({**problem(), "id": "P-0099"}, ensure_ascii=False))
    assert out.startswith("Ошибка KeyError")


def test_bad_grade_is_error():
    out = tools.call("save_problem", json.dumps(problem(grade=11), ensure_ascii=False))
    assert out.startswith("Ошибка ValueError")


# ---------- разрешения ----------

def test_new_problem_saved_without_asking():
    assert permissions.evaluate("save_problem", problem()).behavior == "allow"


def test_overwrite_needs_approval():
    d = permissions.evaluate("save_problem", {**problem(), "id": "P-0001"})
    assert d.behavior == "ask" and "Перезапись" in d.reason


def test_always_allow_persists_across_restart():
    permissions.check("python_run", json.dumps({"code": "print(1)"}), ask=lambda *a: "a")
    assert json.loads(permissions.settings_path().read_text())["always_allow"] == ["python_run"]
    permissions.reset()                       # «перезапуск»: память пуста
    assert permissions.always_allowed() == []
    permissions.load_settings()               # main() делает это при старте
    assert permissions.check("python_run", json.dumps({"code": "print(1)"}), ask=None).allowed


def test_forget_removes_settings_file():
    permissions.check("python_run", json.dumps({"code": "print(1)"}), ask=lambda *a: "a")
    permissions.forget_settings()
    assert not permissions.settings_path().exists()
    assert permissions.always_allowed() == []


def test_broken_settings_file_is_ignored():
    permissions.settings_path().write_text("{oops")
    permissions.load_settings()
    assert permissions.always_allowed() == []


# ---------- полный ход с подменённой моделью ----------

def _call(name, args, call_id):
    return {"role": "assistant", "content": None, "tool_calls": [{
        "id": call_id, "type": "function",
        "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}}]}


def test_full_turn_formulate_check_save():
    replies = [
        _call("list_problems", {"grade": 6}, "c1"),
        _call("z3_check", CRT["arguments"], "c2"),
        _call("save_problem", problem(), "c3"),
        {"role": "assistant", "content": "Сохранил P-0001, статус verified."},
    ]

    def chat(messages, schemas):
        return replies.pop(0)

    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Придумай задачу на остатки для 6 класса и сохрани"}]
    run_turn(messages, chat=chat)
    tool_results = [m["content"] for m in messages if m["role"] == "tool"]
    assert json.loads(tool_results[0]) == {"count": 0, "problems": []}
    assert json.loads(tool_results[2])["status"] == "verified"
    assert bank.get("P-0001")["status"] == "verified"


def test_verify_module_rejects_empty_answer():
    assert verify.run("z3_check", CRT["arguments"], {})["ok"] is False
