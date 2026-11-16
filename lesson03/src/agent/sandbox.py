"""Песочница: выполнение кода модели в отдельном процессе с ограничениями.

Разрешения (permissions.py) решают, МОЖНО ЛИ выполнять вызов.
Песочница ограничивает, ЧТО МОЖЕТ НАТВОРИТЬ уже разрешённый вызов:

- отдельный процесс — зависание или падение не роняет REPL;
- таймаут по реальному времени — процесс убивается;
- лимиты ОС (только POSIX): процессорное время, память, размер файлов.

Две функции:
- run_python(code)          — скрипт целиком в `python -I` (инструмент python_run);
- run_isolated(func, kwargs) — функция Python в дочернем процессе
                               (python_eval, SymPy, z3).

ВАЖНО: это учебная песочница, а не граница безопасности. Дочерний процесс
работает с правами пользователя и видит файловую систему. Настоящая изоляция —
контейнер, nsjail/gVisor, отдельная виртуальная машина.
"""
import builtins
import multiprocessing
import signal
import subprocess
import sys
import tempfile

MAX_OUTPUT = 4000      # символов stdout/stderr, которые уходят модели
MEMORY_MB = 1024       # лимит адресного пространства (работает в Linux, в macOS игнорируется)
FILE_SIZE_MB = 1       # процесс не сможет записать файл больше этого размера


def limit_resources(cpu_seconds: int) -> None:
    """Ставит лимиты ОС на текущий процесс. Вызывается уже в дочернем процессе."""
    try:
        import resource  # нет в Windows
    except ImportError:
        return

    def _set(limit, value):
        try:
            resource.setrlimit(limit, (value, value))
        except (ValueError, OSError):
            pass  # например, macOS не даёт ограничить RLIMIT_AS — честно пропускаем

    _set(resource.RLIMIT_CPU, cpu_seconds)
    _set(resource.RLIMIT_AS, MEMORY_MB * 2**20)
    _set(resource.RLIMIT_FSIZE, FILE_SIZE_MB * 2**20)


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT:
        return text
    return text[:MAX_OUTPUT] + f"\n... [обрезано, всего {len(text)} символов]"


# ---------- скрипт целиком: python_run ----------

def run_python(code: str, timeout: float = 5) -> dict:
    """Запускает скрипт в новом интерпретаторе и возвращает его вывод.

    -I  — изолированный режим: не читаются PYTHON* переменные окружения,
          текущая папка не попадает в sys.path, нет user site-packages;
    cwd — пустая временная папка, которая удаляется после запуска;
    env — пустое окружение: скрипт не увидит API-ключи из .env.
    """
    preexec = None
    if sys.platform != "win32":
        def preexec():
            limit_resources(int(timeout) + 1)

    with tempfile.TemporaryDirectory(prefix="agent_sandbox_") as workdir:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", code],
                cwd=workdir,
                env={},
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=preexec,
            )
        except subprocess.TimeoutExpired as e:
            return {
                "timed_out": True,
                "returncode": None,
                "stdout": _truncate(_as_text(e.stdout)),
                "stderr": f"Превышен лимит времени {timeout} с, процесс остановлен",
            }
    return {
        "timed_out": False,
        "returncode": proc.returncode,
        "stdout": _truncate(proc.stdout),
        "stderr": _truncate(proc.stderr),
    }


def _as_text(data) -> str:
    if data is None:
        return ""
    return data.decode(errors="replace") if isinstance(data, bytes) else data


# ---------- функция в дочернем процессе: python_eval, SymPy, z3 ----------

def _worker(func, kwargs, cpu_seconds, queue):
    """Выполняется в дочернем процессе: лимиты -> вызов -> результат в очередь."""
    limit_resources(cpu_seconds)
    try:
        queue.put(("ok", func(**kwargs)))
    except Exception as e:  # noqa: BLE001 — передаём ошибку родителю как данные
        queue.put(("error", type(e).__name__, str(e)))


def run_isolated(func, kwargs: dict, timeout: float = 10):
    """Вызывает func(**kwargs) в отдельном процессе с таймаутом.

    Метод запуска "spawn" одинаков в Windows, macOS и Linux: дочерний процесс —
    чистый интерпретатор, который заново импортирует модуль с func.
    Ошибка внутри func пробрасывается в родителе с тем же именем типа
    (ZeroDivisionError, ValueError, ...), чтобы реестр показал её модели.
    """
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    # Лимит процессорного времени — страховка на случай, если таймаут по часам не сработал.
    cpu_limit = 2 * int(timeout) + 1
    proc = ctx.Process(target=_worker, args=(func, kwargs, cpu_limit, queue), daemon=True)
    proc.start()
    try:
        outcome = queue.get(timeout=timeout)
    except Exception:  # queue.Empty: результата нет — процесс завис или упал
        outcome = None
    hung = outcome is None and proc.is_alive()
    proc.join(1)
    if proc.is_alive():
        proc.kill()
        proc.join()

    # SIGXCPU — ОС остановила процесс за превышение лимита процессорного времени.
    killed_by_cpu_limit = proc.exitcode == -getattr(signal, "SIGXCPU", 0)
    if hung or (outcome is None and killed_by_cpu_limit):
        raise TimeoutError(f"превышен лимит времени {timeout} с, вычисление остановлено")
    if outcome is None:  # процесс умер сам: например, его убила ОС за превышение лимита
        raise RuntimeError(f"процесс инструмента аварийно завершился (код {proc.exitcode})")
    if outcome[0] == "ok":
        return outcome[1]
    _, type_name, message = outcome
    error_type = getattr(builtins, type_name, None)
    if isinstance(error_type, type) and issubclass(error_type, Exception):
        raise error_type(message)
    raise RuntimeError(f"{type_name}: {message}")
