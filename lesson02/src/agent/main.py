"""Консольный REPL помощника преподавателя."""
import argparse
import json

from agent import llm, tools
from agent.console import read_message
from agent.loop import SYSTEM_PROMPT, run_turn

HELP = (
    "Команды:\n"
    "  /tools     список инструментов\n"
    "  /messages  показать историю сообщений (массив messages)\n"
    "  /reset     очистить историю\n"
    "  /exit      выход\n"
    'Многострочный текст: просто вставьте его или заключите между строками """'
)


def new_history() -> list[dict]:
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def main() -> None:
    parser = argparse.ArgumentParser(description="Помощник преподавателя — занятие 2")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="печатать каждое сообщение, добавленное в messages")
    args = parser.parse_args()

    print(f"Модель: {llm.MODEL} @ {llm.BASE_URL}")
    print(f"Инструменты: {', '.join(tools.names())}")
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
            print("История очищена.")
            continue
        if user_input == "/tools":
            for schema in tools.schemas():
                fn = schema["function"]
                print(f"- {fn['name']}: {fn['description']}")
            continue
        if user_input == "/messages":
            print(json.dumps(messages, ensure_ascii=False, indent=2))
            continue

        messages.append({"role": "user", "content": user_input})
        try:
            answer = run_turn(messages, verbose=args.verbose)
        except Exception as e:  # noqa: BLE001 — ошибки сети/API; ошибки инструментов сюда не доходят
            print(f"[ошибка harness] {type(e).__name__}: {e}")
            continue
        print(f"\nагент> {answer}  [len(messages)={len(messages)}]")


if __name__ == "__main__":
    main()
