"""
=============================================================================
QuantCAI — Prisma Query Engine Bootstrap
=============================================================================
prisma-client-py ships the Rust query engine as a separate binary that is
downloaded on demand into a cache directory. On Render that cache lives at
/opt/render/.cache/... which is available during BUILD but NOT at RUNTIME,
so the app crashed on boot with:

    prisma.engine.errors.BinaryNotFoundError:
      Expected /opt/render/project/src/python_admin/prisma-query-engine-debian-openssl-3.0.x,
      ... to exist but none were found

The only location that survives into the runtime container is the project
source tree itself, so this module downloads the engine (at build time) and
copies it next to the application code as:

    python_admin/prisma-query-engine-<platform>

which is the first path prisma-client-py probes.

Two entry points:
  configure_engine_env()  — cheap, no I/O beyond a glob. MUST be called
                            BEFORE `import prisma` anywhere in the process,
                            because prisma resolves its binary paths at
                            import time.
  ensure_engine()         — downloads + installs the engine if missing.
                            Called from build.sh (build time) and as a
                            last-resort fallback from main.py's lifespan.
=============================================================================
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# The application directory — this is what ends up in the runtime container.
APP_DIR = Path(__file__).resolve().parent

# Filename prefix prisma-client-py expects when the engine sits next to the app.
ENGINE_PREFIX = "prisma-query-engine-"

# Where prisma-client-py caches the engine revision it was built against.
# This is the authoritative source.
_PYTHON_CACHE_ROOTS = (
    "/opt/render/.cache/prisma-python/binaries",
    os.path.join(os.path.expanduser("~"), ".cache", "prisma-python", "binaries"),
)

# Last resort only. `prisma generate` / `prisma db push` in build.sh make the
# Node CLI download its own engines here, but package.json pins prisma@^5.0.0,
# which may resolve to a different 5.x than prisma-client-py expects — so this
# is used only when the authoritative download has failed outright.
_FALLBACK_ROOTS = (str(APP_DIR / "node_modules"),)


def _log(message: str) -> None:
    """Print instead of loguru — this runs before logging is configured."""
    print(f"[prisma-engine] {message}", flush=True)


def expected_platform() -> str | None:
    """
    Ask prisma which engine build this machine needs, e.g. 'debian-openssl-3.0.x'.

    Only call this once the engine-type env vars are set, since it imports
    prisma. Returns None if prisma cannot be interrogated.
    """
    try:
        from prisma.binaries import platform as prisma_platform

        fn = getattr(prisma_platform, "binary_platform", None)
        if callable(fn):
            return str(fn())
    except Exception:  # noqa: BLE001
        pass

    try:
        from prisma.engine.utils import BINARY_PATHS

        names = list(BINARY_PATHS.query_engine.keys())
        if len(names) == 1:
            return str(names[0])
    except Exception:  # noqa: BLE001
        pass

    return None


def local_engine_path() -> Path | None:
    """
    Return the engine binary installed next to the app, preferring the one that
    matches this machine's platform.

    Selecting alphabetically here is a trap: 'debian-openssl-1.1.x' sorts before
    'debian-openssl-3.0.x', so a blind sorted()[0] can hand back a binary that
    exists but cannot execute on this host.
    """
    matches = [p for p in sorted(APP_DIR.glob(f"{ENGINE_PREFIX}*")) if p.is_file()]
    if not matches:
        return None

    platform_name = expected_platform()
    if platform_name:
        for match in matches:
            if match.name == f"{ENGINE_PREFIX}{platform_name}":
                return match
        _log(
            f"WARNING: no engine matching platform '{platform_name}'; "
            f"have {[m.name for m in matches]}"
        )

    return matches[0]


def configure_engine_env() -> None:
    """
    Select the binary (Rust process) engine rather than the Node-based one.

    Must run before `import prisma`, which reads these at import time.

    Deliberately does NOT set PRISMA_QUERY_ENGINE_BINARY: that override bypasses
    prisma's platform detection, so pointing it at the wrong OpenSSL variant
    turns a clear BinaryNotFoundError into an opaque EngineConnectionError.
    Prisma's own resolution already probes <cwd>/prisma-query-engine-<platform>
    with the correct platform name — our job is just to put the right file there.
    """
    os.environ.setdefault("PRISMA_CLIENT_ENGINE_TYPE", "binary")
    os.environ.setdefault("PRISMA_CLI_QUERY_ENGINE_TYPE", "binary")
    return None


def _expected_engine_version() -> str | None:
    """The engine revision hash prisma-client-py was generated against."""
    for module_name, attr in (
        ("prisma.binaries", "ENGINE_VERSION"),
        ("prisma", "ENGINE_VERSION"),
    ):
        try:
            module = __import__(module_name, fromlist=[attr])
            value = getattr(module, attr, None)
            if value:
                return str(value)
        except Exception:  # noqa: BLE001
            continue
    return None


def verify_engine(engine: Path) -> bool:
    """
    Run the engine with --version to surface why it will not start.

    prisma reports every spawn failure as the same opaque
    EngineConnectionError, so probe the binary directly and log the real
    reason: a wrong-architecture binary fails to exec, a missing shared library
    names itself, and a healthy engine prints its revision hash.
    """
    try:
        result = subprocess.run(
            [str(engine), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception as exc:  # noqa: BLE001
        _log(f"Engine self-check FAILED to execute {engine.name}: {exc}")
        return False

    output = (result.stdout or result.stderr or "").strip()
    if result.returncode == 0:
        # The engine prints its own revision hash. Log what prisma expects
        # alongside it so a mismatch is obvious rather than inferred.
        _log(f"Engine self-check OK: {engine.name} -> {output}")
        _log(f"Client expects engine revision: {_expected_engine_version() or 'unknown'}")
        return True

    _log(
        f"Engine self-check FAILED: {engine.name} exited {result.returncode} -> {output}"
    )
    return False


def _iter_cached_engines(roots: tuple[str, ...]) -> list[Path]:
    """
    Walk the given roots looking for a downloaded query engine.

    prisma-client-py has moved this file around between releases
    (node_modules/prisma/, node_modules/@prisma/engines/, and the version
    directory itself), so we search recursively rather than hardcoding a
    layout — that assumption is exactly what broke the deploy.
    """
    found: list[Path] = []
    search_roots = [Path(root) for root in roots]

    override = os.environ.get("PRISMA_BINARY_CACHE_DIR")
    if override:
        search_roots.insert(0, Path(override))

    # Partial downloads, archives, and the JS/TS files that sit alongside the
    # engines in node_modules — none of these are executable engines.
    skip_suffixes = (".tmp", ".gz", ".sha256", ".js", ".ts", ".json", ".map", ".md")

    for root in search_roots:
        if not root.is_dir():
            continue
        matches: list[Path] = []
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                if "query-engine-" not in name or name.endswith(skip_suffixes):
                    continue
                matches.append(Path(dirpath) / name)
        # Sort within each root for deterministic selection, but keep the roots
        # themselves in priority order.
        found.extend(sorted(matches))

    return found


def _install(source: Path) -> Path:
    """Copy a cached engine next to the app under the name prisma expects."""
    basename = source.name
    if basename.startswith(ENGINE_PREFIX):
        target_name = basename
    else:
        # e.g. query-engine-debian-openssl-3.0.x -> prisma-query-engine-debian-openssl-3.0.x
        target_name = f"prisma-{basename}"

    target = APP_DIR / target_name
    shutil.copy(source, target)
    os.chmod(target, 0o755)
    _log(f"Installed engine: {source} -> {target}")

    if "node_modules" in source.parts:
        # package.json pins the Node CLI as prisma@^5.0.0, which may resolve to a
        # different 5.x than the engine revision prisma-client-py expects. This
        # source is a last resort, so say so loudly if we had to use it.
        _log(
            "WARNING: engine taken from node_modules (Node CLI), not the "
            "prisma-python cache. Verify the engine revision matches the "
            "generated client if you see version-mismatch errors."
        )
    return target


def _download() -> None:
    """
    Fetch the engine binaries into the local cache.

    Preferred path is prisma's own Python download API, which pulls straight
    from the Prisma CDN. The `prisma py fetch` subprocess is kept as a
    fallback, but it first installs the Node CLI (slow — it is what was
    timing out the Gunicorn worker boot), so it is only used if the direct
    API is unavailable.
    """
    try:
        import prisma.binaries as prisma_binaries

        # The attribute has been named both ENGINES and BINARIES across
        # prisma-client-py releases.
        engines = getattr(prisma_binaries, "ENGINES", None) or getattr(
            prisma_binaries, "BINARIES", None
        )
        if not engines:
            raise AttributeError("no ENGINES/BINARIES list in prisma.binaries")

        for engine in engines:
            engine.download()
        _log("Engines downloaded via prisma.binaries")
        return
    except Exception as exc:  # noqa: BLE001 - any failure falls through to the CLI
        _log(f"Direct engine download unavailable ({exc}); falling back to 'prisma py fetch'")

    subprocess.run([sys.executable, "-m", "prisma", "py", "fetch"], check=True)
    _log("Engines downloaded via 'prisma py fetch'")


def ensure_engine(force: bool = False) -> Path | None:
    """
    Guarantee that a usable query engine sits next to the application code.

    Args:
        force: re-install even if an engine is already present.

    Returns:
        Path to the installed engine, or None if it could not be obtained.
    """
    # Do this first: everything below imports prisma, which reads the
    # engine-type env vars at import time. Setting them afterwards would be too
    # late and could fetch the library engine instead of the binary one.
    configure_engine_env()

    existing = local_engine_path()
    if existing is not None and not force:
        _log(f"Engine already present: {existing.name}")
        return existing

    platform_name = expected_platform()
    engine_version = _expected_engine_version()
    _log(f"Detected engine platform: {platform_name or 'unknown'}")
    _log(f"Client expects engine revision: {engine_version or 'unknown'}")

    def _right_revision(paths: list[Path]) -> list[Path]:
        """
        Keep only engines from the revision this client was generated against.

        The cache is keyed by <prisma-version>/<engine-revision>/ and Render
        persists it across builds, so several revisions accumulate — all with
        the same filename. An engine from the wrong revision starts up but
        fails the handshake, surfacing as EngineConnectionError rather than
        anything that names the real problem.
        """
        if not engine_version:
            return paths
        return [p for p in paths if engine_version in str(p)]

    # 1. The authoritative prisma-python cache may already hold the right
    #    revision from an earlier build — reuse it rather than re-downloading.
    cached = _right_revision(_iter_cached_engines(_PYTHON_CACHE_ROOTS))

    # 2. Otherwise fetch the revision prisma-client-py was built against. Note
    #    this also runs when the cache is warm but holds only stale revisions.
    if not cached:
        try:
            _download()
        except Exception as exc:  # noqa: BLE001
            _log(f"Engine download failed: {exc}")
        cached = _right_revision(_iter_cached_engines(_PYTHON_CACHE_ROOTS))

    # 3. Accept a revision mismatch from the python cache before giving up.
    if not cached:
        cached = _iter_cached_engines(_PYTHON_CACHE_ROOTS)
        if cached:
            _log(
                f"WARNING: no engine matching revision {engine_version}; "
                "using another revision from the python cache"
            )

    # 4. Last resort: borrow the Node CLI's engine.
    if not cached:
        _log("Authoritative cache empty — falling back to the Node CLI engines")
        cached = _iter_cached_engines(_FALLBACK_ROOTS)

    if not cached:
        _log(
            "No query engine found in any cache root. Searched: "
            + ", ".join(_PYTHON_CACHE_ROOTS + _FALLBACK_ROOTS)
        )
        return None

    _log(f"Candidate engines: {[str(c) for c in cached]}")

    # Install the platform match if we can identify one. Otherwise install every
    # distinct variant — a few extra MB is cheap next to another failed boot,
    # and it lets prisma pick the one it actually wants by name.
    to_install: list[Path] = []
    if platform_name:
        to_install = [c for c in cached if c.name.endswith(platform_name)]
        if not to_install:
            _log(
                f"WARNING: no candidate matches platform '{platform_name}' — "
                "installing all variants instead"
            )
    if not to_install:
        seen: set[str] = set()
        for candidate in cached:
            if candidate.name not in seen:
                seen.add(candidate.name)
                to_install.append(candidate)

    installed: Path | None = None
    for candidate in to_install:
        try:
            result = _install(candidate)
        except Exception as exc:  # noqa: BLE001
            _log(f"Failed to install engine from {candidate}: {exc}")
            continue
        if installed is None:
            installed = result

    if installed is None:
        _log("Every candidate engine failed to install")
        return None

    # Re-resolve so we hand back the platform match rather than whichever
    # variant happened to be installed first.
    installed = local_engine_path() or installed

    # When this runs as a runtime fallback, prisma has already been imported and
    # has baked in a CWD-relative candidate path. Gunicorn starts in APP_DIR so
    # the two normally coincide, but mirror the binaries if they don't.
    cwd = Path.cwd().resolve()
    if cwd != APP_DIR:
        for engine_file in APP_DIR.glob(f"{ENGINE_PREFIX}*"):
            try:
                mirrored = cwd / engine_file.name
                shutil.copy(engine_file, mirrored)
                os.chmod(mirrored, 0o755)
                _log(f"Mirrored engine to working directory: {mirrored}")
            except Exception as exc:  # noqa: BLE001
                _log(f"Could not mirror {engine_file.name} into {cwd}: {exc}")

    return installed


if __name__ == "__main__":
    result = ensure_engine(force="--force" in sys.argv)
    if result is None:
        _log("FATAL: could not provision the Prisma query engine")
        sys.exit(1)

    # Diagnostic only — a failing self-check still deploys, because the log line
    # it produces is far more actionable than another opaque boot failure.
    verify_engine(result)
    _log(f"Ready: {result}")
