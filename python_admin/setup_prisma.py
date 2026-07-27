"""
Build-time provisioning of the Prisma query engine.

Run by build.sh before `prisma generate`. All of the real work lives in
prisma_engine.py so that the build path and the runtime fallback in main.py
cannot drift apart — they previously did, and both looked for the engine in a
directory prisma-client-py no longer uses, which shipped an app that 502'd on
every boot.

By default this does NOT fail the build when the engine cannot be provisioned.
Render keeps the previous deploy running when a build fails, so failing here
would pin the service to the last (broken) release and suppress the runtime
diagnostics in main.py. Instead it warns loudly and lets main.py retry at boot.

Set PRISMA_ENGINE_STRICT=1 to fail the build instead — worth turning on once
the service is healthy, so a silently engine-less release can never ship again.
"""

import os
import sys

from prisma_engine import ensure_engine, verify_engine

if __name__ == "__main__":
    engine = ensure_engine()
    strict = os.environ.get("PRISMA_ENGINE_STRICT") == "1"

    if engine is None:
        print(
            "WARNING: could not provision the Prisma query engine at build time. "
            "main.py will retry at startup.",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1 if strict else 0)

    ok = verify_engine(engine)
    print(f"Prisma query engine ready: {engine} (self-check {'ok' if ok else 'FAILED'})", flush=True)
    if not ok and strict:
        sys.exit(1)
