"""Консольный REPL помощника преподавателя."""
import argparse
import json

from agent import bank, llm, permissions, tools
from agent.console import ask_permission, read_message
from agent.loop import SYSTEM_PROMPT, run_turn

HELP = (
    "Команды:\n"
    "  /bank [статус]          задачи в банке (draft, verified, approved, rejected)\n"
    "  /show <id>              полная запись задачи\n"
    "  /approve <id>           утвердить проверенную задачу\n"
    "  /reject <id> <причина>  отклонить задачу с комментарием для модели\n"
    "  /tools                  список инструментов\n"
    "  /permissions            режим, правила и сохранённые разрешения «всегда»\n"
    "  /forget                 забыть все разрешения «всегда» (и на диске)\n"
    "  /mode <режим>           default | auto | strict\n"
    "  /messages               показать историю сообщений (массив messages)\n"
    "  /reset                  очистить историю (банк и разрешения остаются)\n"
    "  /exit                   выход\n"
    'Многострочный текст: просто вставьте его или заключите между строками """'
)


def new_history() -> list[dict]:
    return [{"role": "system", "content": system_prompt()}]


def system_prompt() -> str:
    """Системный промпт + свежее оглавление банка (идея из s09 Memory)."""
    return f"{SYSTEM_PROMPT}\n\nСостояние банка: {bank.summary()}"


def show_bank(status: str | None) -> None:
    records, broken = bank.list_all(status=status)
    if not records:
        print("Задач нет." if status is None else f"Задач со статусом {status} нет.")
    for r in records:
        print(f"  {r['id']}  [{r.get('status'):8}]  {r.get('grade')} кл  "
              f"{r.get('topic')}: {r.get('title')}")
    if broken:
        print(f"  Испорченные файлы (пропущены): {', '.join(broken)}")


def show_problem(problem_id: str) -> None:
    r = bank.get(problem_id)
    v = r.get("verification") or {}
    print(f"{r['id']} [{r['status']}] {r['grade']} кл, {r['topic']}: {r['title']}")
    print(f"\nУсловие:\n{r['statement']}")
    print(f"\nОтвет: {json.dumps(r['answer'], ensure_ascii=False)}")
    print(f"\nРешение:\n{r['solution']}")
    print(f"\nПроверка: {v.get('tool')} — {'OK' if v.get('ok') else 'НЕ ПРОЙДЕНА'}: {v.get('reason')}")
    if r.get("review"):
        print(f"Отзыв: {r['review']['status']} — {r['review'].get('comment') or ''}")


def approve(problem_id: str) -> None:
    r = bank.get(problem_id)
    if r["status"] != "verified":
        print(f"{problem_id} в статусе {r['status']}: утвердить можно только verified-задачу.")
        return
    bank.set_status(problem_id, "approved")
    print(f"{problem_id} утверждена.")


def show_permissions() -> None:
    print(f"Режим: {permissions.get_mode()}")
    print("Ворота 1 (запрет): __dunder__, import в выражениях, имена "
          f"{', '.join(sorted(n for n in permissions.BANNED_NAMES if not n.startswith('_')))}")
    print(f"  python_run может импортировать: {', '.join(sorted(permissions.ALLOWED_MODULES))}")
    print("Ворота 2 (спросить):")
    for rule in permissions.RULES:
        print(f"  - {rule['message']}: {', '.join(rule['tools'])}")
    allowed = permissions.always_allowed()
    print(f"Разрешено всегда ({permissions.settings_path()}): {', '.join(allowed) if allowed else 'ничего'}")


def handle_command(user_input: str) -> bool:
    """Команды банка и разрешений. True — команда обработана."""
    parts = user_input.split(maxsplit=2)
    cmd = parts[0]
    try:
        if cmd == "/bank":
            show_bank(parts[1] if len(parts) > 1 else None)
        elif cmd == "/show" and len(parts) == 2:
            show_problem(parts[1])
        elif cmd == "/approve" and len(parts) == 2:
            approve(parts[1])
        elif cmd == "/reject" and len(parts) == 3:
            bank.set_status(parts[1], "rejected", comment=parts[2])
            print(f"{parts[1]} отклонена. Комментарий модель увидит через get_problem.")
        elif cmd == "/tools":
            for schema in tools.schemas():
                fn = schema["function"]
                print(f"- {fn['name']}: {fn['description']}")
        elif cmd == "/permissions":
            show_permissions()
        elif cmd == "/forget":
            permissions.forget_settings()
            print("Разрешения «всегда» забыты.")
        elif cmd == "/mode":
            if len(parts) == 2 and parts[1] in permissions.MODES:
                permissions.set_mode(parts[1])
                print(f"Режим разрешений: {parts[1]}")
            else:
                print(f"Использование: /mode {'|'.join(permissions.MODES)}  (сейчас {permissions.get_mode()})")
        elif cmd in ("/show", "/approve", "/reject"):
            print("Использование: /show <id>, /approve <id>, /reject <id> <причина>")
        else:
            return False
    except (KeyError, ValueError) as e:
        print(f"Ошибка: {e.args[0] if e.args else e}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Помощник преподавателя — занятие 4")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="печатать каждое сообщение, добавленное в messages")
    parser.add_argument("--mode", choices=permissions.MODES, default="default",
                        help="режим разрешений: default — спрашивать, auto — не спрашивать, "
                             "strict — отказывать без вопроса")
    args = parser.parse_args()
    permissions.reset(args.mode)
    permissions.load_settings()

    print(f"Модель: {llm.MODEL} @ {llm.BASE_URL}")
    print(f"Инструменты: {', '.join(tools.names())}")
    print(f"Режим разрешений: {permissions.get_mode()}")
    print(f"Банк: {bank.bank_dir().resolve()} — {bank.summary()}")
    print(HELP)
    messages = new_history()

    while True:
        try:
            user_input = read_message()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input == "/exit":
            break
        if user_input == "/reset":
            messages = new_history()
            print("История очищена. Банк и сохранённые разрешения остались.")
            continue
        if user_input == "/messages":
            print(json.dumps(messages, ensure_ascii=False, indent=2))
            continue
        if user_input.startswith("/") and handle_command(user_input):
            continue

        messages[0]["content"] = system_prompt()  # банк мог измениться с прошлого хода
        messages.append({"role": "user", "content": user_input})
        try:
            answer = run_turn(messages, verbose=args.verbose, ask=ask_permission)
        except Exception as e:  # noqa: BLE001 — ошибки сети/API; ошибки инструментов сюда не доходят
            print(f"[ошибка harness] {type(e).__name__}: {e}")
            continue
        print(f"\nагент> {answer}  [len(messages)={len(messages)}]")


if __name__ == "__main__":
    main()
