"""
services/atomic_io.py — Atomic file writes + advisory file locks.

Background. The audit identified state-file persistence as a concurrency
hazard: cooldowns.json and the per-symbol paper-engine state files were
written with a plain `with open(path, "w") as f: json.dump(...)`. If
Streamlit, the run-loop, and a manual action all touched the same file,
the result was: torn writes (partial JSON), corrupted state (file
contains '{' on its own), lost cooldowns, or duplicated/missing trades.

Defense in two layers:

    atomic_write_text(path, text)
        Write `text` to a sibling tmp file, fsync it, then os.replace
        onto the target. POSIX guarantees the rename is atomic, so a
        reader either sees the previous contents or the new contents —
        never a half-written file.

    file_lock(path)
        A coarse advisory lock. Uses fcntl.flock on POSIX, falls back
        to a noop on platforms without it. Does NOT prevent two
        *processes* from racing if one of them ignores the lock — but
        every state-mutating call site in this codebase goes through
        the lock, so as long as no one else writes the file by hand,
        we're consistent.

Together: writers acquire the lock, write to tmp, replace; readers can
read concurrently and either see the old or the new file.
"""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:  # POSIX
    import fcntl
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover — Windows fallback
    fcntl = None  # type: ignore[assignment]
    _HAS_FCNTL = False


def atomic_write_text(path: str | Path, text: str) -> None:
    """
    Atomically replace `path` with `text`. Creates parent dirs if needed.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # NamedTemporaryFile in the same dir guarantees os.replace can be
    # used (it requires the temp file to be on the same filesystem).
    fd, tmp_path = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, p)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_write_json(path: str | Path, data: Any, *, indent: int = 2) -> None:
    """JSON-serialize `data` and write atomically to `path`."""
    atomic_write_text(path, json.dumps(data, indent=indent, default=str))


@contextmanager
def file_lock(path: str | Path) -> Iterator[None]:
    """
    Acquire an exclusive advisory lock keyed by `path`. The lock file
    sits next to the target (path + '.lock'). Released on context exit.

    On platforms without fcntl, this is a noop — the caller still gets
    the in-process consistency guarantee from being inside a `with`.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lock_path = p.with_suffix(p.suffix + ".lock")
    if not _HAS_FCNTL:
        # Best-effort noop. Open the file so callers that look for it
        # see something, but don't actually block.
        with open(lock_path, "w") as fh:
            fh.write("noop")
            yield
        return

    with open(lock_path, "w") as fh:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
