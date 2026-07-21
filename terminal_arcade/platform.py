"""Shared platform paths and durable local persistence helpers."""

from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, TypeVar


_T = TypeVar("_T")
_THREAD_LOCKS: dict[str, threading.Lock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()


def app_data_dir(app_dir_name: str, base_dir: Path | None = None) -> Path:
    """Return an application data directory while preserving test overrides."""
    if base_dir is not None:
        return Path(base_dir)

    home = Path.home()
    if sys.platform == "darwin":
        root = home / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    return root / app_dir_name


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Atomically replace *path* with *text* in the same filesystem."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding=encoding) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def atomic_write_json(
    path: Path,
    payload: Any,
    *,
    indent: int | None = 2,
    ensure_ascii: bool = False,
) -> None:
    """Serialize JSON and atomically replace the target file."""
    atomic_write_text(
        path,
        json.dumps(payload, indent=indent, ensure_ascii=ensure_ascii),
    )


@contextmanager
def _exclusive_file_lock(path: Path):
    """Serialize threads and processes that update the same local state file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_key = str(path.resolve())
    with _THREAD_LOCKS_GUARD:
        thread_lock = _THREAD_LOCKS.setdefault(lock_key, threading.Lock())

    with thread_lock:
        with path.open("a+b") as handle:
            if os.name == "nt":
                import msvcrt

                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def locked_json_update(
    path: Path,
    defaults: dict,
    update: Callable[[dict], _T],
    *,
    indent: int | None = None,
) -> _T:
    """Atomically read, mutate, and persist a JSON object under an exclusive lock."""
    path = Path(path)
    lock_path = path.with_name(f".{path.name}.lock")
    with _exclusive_file_lock(lock_path):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                payload = copy.deepcopy(defaults)
        except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
            payload = copy.deepcopy(defaults)
        result = update(payload)
        atomic_write_json(path, payload, indent=indent)
        return result
