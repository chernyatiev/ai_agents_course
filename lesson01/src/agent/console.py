"""Чтение сообщения пользователя в консоли, в том числе многострочного.

Встроенный input() читает ровно одну строку. Если вставить в терминал условие
задачи из нескольких строк, без этого модуля агент получит только первую строку,
а остальные уйдут следующими сообщениями.

Два способа ввести несколько строк:
1. Просто вставить текст. Строки, которые пришли в терминал вместе с первой
   (так бывает при вставке из буфера обмена), склеиваются в одно сообщение.
   Работает в macOS и Linux.
2. Явный блок: строка с тремя кавычками, текст, снова строка с тремя кавычками.
   Работает везде, в том числе в Windows.
"""
import select
import sys

BLOCK_MARK = '"""'
PASTE_WAIT_SEC = 0.05  # строки вставки приходят почти мгновенно, человек так быстро не печатает


def more_input_ready(timeout: float = PASTE_WAIT_SEC) -> bool:
    """Есть ли в терминале ещё непрочитанные строки (признак вставки)."""
    try:
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
    except (OSError, ValueError):  # Windows: select не работает с консолью
        return False
    return bool(ready)


def read_message(prompt: str = "\nты> ", ready=more_input_ready) -> str:
    """Читает одно сообщение пользователя. EOFError пробрасывается наружу (выход)."""
    first = input(prompt)

    if first.strip() == BLOCK_MARK:
        lines = []
        while (line := input("... ")).strip() != BLOCK_MARK:
            lines.append(line)
        return "\n".join(lines).strip()

    lines = [first]
    while ready():
        try:
            lines.append(input())
        except EOFError:
            break
    return "\n".join(lines).strip()
