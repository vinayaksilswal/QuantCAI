"""
Build-time provisioning of the Prisma query engine.

Run by build.sh before `prisma generate`. All of the real work lives in
prisma_engine.py so that the build path and the runtime fallback in main.py
cannot drift apart — they previously did, and both looked for the engine in a
directory prisma-client-py no longer uses, which shipped an app that 502'd on
every boot.

Exits non-zero when the engine cannot be provisioned so that build.sh's
`set -o errexit` fails the deploy instead of publishing a broken release.
"""

import sys

from prisma_engine import ensure_engine

if __name__ == "__main__":
    engine = ensure_engine()
    if engine is None:
        print(
            "FATAL: could not provision the Prisma query engine. "
            "The app cannot connect to the database without it.",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)
    print(f"Prisma query engine ready: {engine}", flush=True)
