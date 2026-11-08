"""Parolni taxmin qilishdan himoya: ketma-ket 5 xato urinishdan keyin 10 daqiqa bloklanadi."""
import threading
import time

MAX_FAILS = 5
LOCK_SECONDS = 600

_lock = threading.Lock()
_fails: dict[str, tuple[int, float]] = {}


def is_locked(key: str) -> bool:
    now = time.monotonic()
    with _lock:
        for k in [k for k, (_, until) in _fails.items() if until <= now]:
            del _fails[k]
        entry = _fails.get(key)
        return entry is not None and entry[0] >= MAX_FAILS


def record_failure(key: str) -> None:
    with _lock:
        count = _fails.get(key, (0, 0.0))[0] + 1
        _fails[key] = (count, time.monotonic() + LOCK_SECONDS)


def reset(key: str) -> None:
    with _lock:
        _fails.pop(key, None)
