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


def local_engine_path() -> Path | None:
    """Return the engine binary already installed next to the app, if any."""
    matches = sorted(APP_DIR.glob(f"{ENGINE_PREFIX}*"))
    for match in matches:
        if match.is_file():
            return match
    return None


def configure_engine_env() -> Path | None:
    """
    Point prisma-client-py at the binary engine before it is imported.

    Returns the engine path if one is already installed locally.
    """
    # Force the binary (Rust process) engine rather than the Node-based one.
    os.environ.setdefault("PRISMA_CLIENT_ENGINE_TYPE", "binary")
    os.environ.setdefault("PRISMA_CLI_QUERY_ENGINE_TYPE", "binary")

    engine = local_engine_path()
    if engine is not None:
        # Explicit override — bypasses prisma's platform-name guessing entirely.
        os.environ["PRISMA_QUERY_ENGINE_BINARY"] = str(engine)
    return engine


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
    # Do this first: _download() may import prisma.binaries, which reads the
    # engine-type env vars at import time. Setting them afterwards would be too
    # late and could fetch the library engine instead of the binary one.
    existing = configure_engine_env()

    if existing is not None and not force:
        _log(f"Engine already present: {existing.name}")
        return existing

    # 1. The authoritative prisma-python cache may already be warm from an
    #    earlier build — reuse it rather than hitting the network again.
    cached = _iter_cached_engines(_PYTHON_CACHE_ROOTS)

    # 2. Otherwise download the revision prisma-client-py was built against.
    if not cached:
        try:
            _download()
        except Exception as exc:  # noqa: BLE001
            _log(f"Engine download failed: {exc}")
        cached = _iter_cached_engines(_PYTHON_CACHE_ROOTS)

    # 3. Only if that failed entirely, borrow the Node CLI's engine. A possible
    #    revision mismatch beats a guaranteed BinaryNotFoundError at boot.
    if not cached:
        _log("Authoritative cache empty — falling back to the Node CLI engines")
        cached = _iter_cached_engines(_FALLBACK_ROOTS)

    if not cached:
        _log(
            "No query engine found in any cache root. Searched: "
            + ", ".join(_PYTHON_CACHE_ROOTS + _FALLBACK_ROOTS)
        )
        return None

    try:
        installed = _install(cached[0])
    except Exception as exc:  # noqa: BLE001
        _log(f"Failed to install engine from {cached[0]}: {exc}")
        return None

    # When this runs as a runtime fallback, prisma has already been imported and
    # has baked in a CWD-relative candidate path. Gunicorn starts in APP_DIR so
    # the two normally coincide, but mirror the binary if they don't.
    cwd = Path.cwd().resolve()
    if cwd != APP_DIR:
        try:
            mirrored = cwd / installed.name
            shutil.copy(installed, mirrored)
            os.chmod(mirrored, 0o755)
            _log(f"Mirrored engine to working directory: {mirrored}")
        except Exception as exc:  # noqa: BLE001
            _log(f"Could not mirror engine into {cwd}: {exc}")

    configure_engine_env()
    return installed


if __name__ == "__main__":
    result = ensure_engine(force="--force" in sys.argv)
    if result is None:
        _log("FATAL: could not provision the Prisma query engine")
        sys.exit(1)
    _log(f"Ready: {result}")
