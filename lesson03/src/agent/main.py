"""Консольный REPL помощника преподавателя."""
import argparse
import json

from agent import llm, permissions, tools
from agent.console import ask_permission, read_message
from agent.loop import SYSTEM_PROMPT, run_turn

HELP = (
    "Команды:\n"
    "  /tools         список инструментов\n"
    "  /permissions   режим, правила и что разрешено «всегда» в этой сессии\n"
    "  /mode <режим>  default (спрашивать) | auto (не спрашивать) | strict (отказывать)\n"
    "  /messages      показать историю сообщений (массив messages)\n"
    "  /reset         очистить историю (разрешения сессии тоже сбрасываются)\n"
    "  /exit          выход\n"
    'Многострочный текст: просто вставьте его или заключите между строками """'
)


def new_history() -> list[dict]:
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def show_permissions() -> None:
    print(f"Режим: {permissions.get_mode()}")
    print("Ворота 1 (запрет): __dunder__, import в выражениях, имена "
          f"{', '.join(sorted(n for n in permissions.BANNED_NAMES if not n.startswith('_')))}")
    print(f"  python_run может импортировать: {', '.join(sorted(permissions.ALLOWED_MODULES))}")
    print("Ворота 2 (спросить):")
    for rule in permissions.RULES:
        print(f"  - {rule['message']}: {', '.join(rule['tools'])}")
    allowed = permissions.always_allowed()
    print(f"Разрешено всегда в этой сессии: {', '.join(allowed) if allowed else 'ничего'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Помощник преподавателя — занятие 3")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="печатать каждое сообщение, добавленное в messages")
    parser.add_argument("--mode", choices=permissions.MODES, default="default",
                        help="режим разрешений: default — спрашивать, auto — не спрашивать, "
                             "strict — отказывать без вопроса")
    args = parser.parse_args()
    permissions.reset(args.mode)

    print(f"Модель: {llm.MODEL} @ {llm.BASE_URL}")
    print(f"Инструменты: {', '.join(tools.names())}")
    print(f"Режим разрешений: {permissions.get_mode()}")
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
            permissions.reset(permissions.get_mode())
            print("История и разрешения сессии очищены.")
            continue
        if user_input == "/tools":
            for schema in tools.schemas():
                fn = schema["function"]
                print(f"- {fn['name']}: {fn['description']}")
            continue
        if user_input == "/permissions":
            show_permissions()
            continue
        if user_input.startswith("/mode"):
            parts = user_input.split()
            if len(parts) == 2 and parts[1] in permissions.MODES:
                permissions.set_mode(parts[1])
                print(f"Режим разрешений: {parts[1]}")
            else:
                print(f"Использование: /mode {'|'.join(permissions.MODES)}  (сейчас {permissions.get_mode()})")
            continue
        if user_input == "/messages":
            print(json.dumps(messages, ensure_ascii=False, indent=2))
            continue

        messages.append({"role": "user", "content": user_input})
        try:
            answer = run_turn(messages, verbose=args.verbose, ask=ask_permission)
        except Exception as e:  # noqa: BLE001 — ошибки сети/API; ошибки инструментов сюда не доходят
            print(f"[ошибка harness] {type(e).__name__}: {e}")
            continue
        print(f"\nагент> {answer}  [len(messages)={len(messages)}]")


if __name__ == "__main__":
    main()
