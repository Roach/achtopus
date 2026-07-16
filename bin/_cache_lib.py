"""
Achtopus — local cache clerk. The "librarian/archivist" for canonical fetches: one place
to get-or-fetch content addressed by a stable key, so repeated identical work (a `git diff`,
a `gh pr view`, a repro command run by two different verify passes) is paid for once — in
tokens, latency, and (for network fetches) egress — and every reader after the first gets a
disk read instead of re-doing the fetch.

Storage: flat files under wire/cache/<sanitized-key>. Deliberately flat and greppable, same
philosophy as the wire itself (docs/protocol.md) — no index, no database, `ls`/`cat` always
work. `bin/wire clear` archives/purges the whole `cache/` dir alongside the .md artifacts (see
bin/wire) — same per-run lifecycle, so a stale cache from an unrelated prior run never survives
a fresh run.

Shared by:
- bin/run: the driver's own preflight precompute step (deterministic, zero LLM cost — see
  precompute_context_cache in bin/run) writes here directly via set_bytes()/set_text().
- bin/cache: the CLI wrapper any persona (or a human) invokes as a subprocess — get/has/set/
  fetch/list/rm — for the (common) case where bin/ is reachable from the agent's cwd (i.e. an
  isolated worktree task normally can't reach bin/, since only wire/ and its own cwd are
  --add-dir'd; non-isolated tasks at REPO_ROOT can).
"""
import os
import re
import subprocess
import time

WIRE_DIRNAME = "wire"
CACHE_DIRNAME = "cache"

_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_key(key):
    """Collapse a cache key to a single path-safe filename segment. Deliberately permissive
    (dots allowed) so a natural key like `diff.patch` or `pr.json` round-trips unchanged;
    anything else (spaces, slashes, shell metacharacters) collapses to underscores rather
    than erroring — a caller passing a weird key gets a working, if ugly, cache entry instead
    of a crash."""
    key = str(key).strip()
    if not key:
        raise ValueError("cache key must be non-empty")
    return _SAFE_RE.sub("_", key)[:200]


def cache_dir(wire_dir):
    d = os.path.join(wire_dir, CACHE_DIRNAME)
    os.makedirs(d, exist_ok=True)
    return d


def path_for(wire_dir, key):
    return os.path.join(cache_dir(wire_dir), sanitize_key(key))


def has(wire_dir, key):
    return os.path.isfile(path_for(wire_dir, key))


def get_bytes(wire_dir, key):
    """Returns the cached bytes, or None on a miss (never raises for a plain miss)."""
    p = path_for(wire_dir, key)
    if not os.path.isfile(p):
        return None
    with open(p, "rb") as f:
        return f.read()


def get_text(wire_dir, key, encoding="utf-8"):
    b = get_bytes(wire_dir, key)
    return None if b is None else b.decode(encoding, errors="replace")


def set_bytes(wire_dir, key, data):
    """Atomic write (tmp file + rename) so a reader never sees a partial cache entry —
    relevant because fetch() below may be racing a concurrent task's own fetch() of the
    same key."""
    p = path_for(wire_dir, key)
    tmp = p + f".tmp.{os.getpid()}.{int(time.time() * 1000)}"
    with open(tmp, "wb") as f:
        f.write(data if isinstance(data, bytes) else str(data).encode("utf-8"))
    os.replace(tmp, p)
    return p


def set_text(wire_dir, key, text):
    return set_bytes(wire_dir, key, text.encode("utf-8"))


def remove(wire_dir, key):
    p = path_for(wire_dir, key)
    try:
        os.remove(p)
        return True
    except FileNotFoundError:
        return False


def list_entries(wire_dir):
    """Returns [(key, size_bytes, mtime), ...] sorted by key. Reads the actual filenames on
    disk (not a separate index) — the directory listing IS the source of truth."""
    d = cache_dir(wire_dir)
    out = []
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if os.path.isfile(p) and not name.endswith(".tmp"):
            st = os.stat(p)
            out.append((name, st.st_size, st.st_mtime))
    return out


def fetch(wire_dir, key, argv, cwd=None):
    """Get-or-compute: return (data_bytes, hit_bool). On a cache hit, `argv` never runs — this
    is the single primitive that turns "check if it's cached, else run the command and cache
    it" from a convention every caller has to remember into one call that can't be gotten
    wrong. Raises subprocess.CalledProcessError if argv fails (a failed fetch is never cached,
    so the next caller retries it rather than caching a failure as if it were content)."""
    cached = get_bytes(wire_dir, key)
    if cached is not None:
        return cached, True
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, check=True)
    set_bytes(wire_dir, key, proc.stdout)
    return proc.stdout, False
