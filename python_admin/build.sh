#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Install the query engine next to the app. /opt/render/.cache does not exist at
# runtime, so this copy into the source tree is the only thing that survives
# into the running container.
#
# Kept in its original position (before generate/push) because that ordering is
# known to build successfully. It is non-fatal by design: Render keeps the
# previous deploy alive when a build fails, so aborting here would strand the
# service on the old release. Set PRISMA_ENGINE_STRICT=1 to make it fatal once
# the service is healthy.
python setup_prisma.py

prisma generate --schema=schema_py.prisma
prisma db push --schema=schema_py.prisma

# Diagnostics only — must not trip errexit if the glob matches nothing.
echo "--- Prisma engine provisioned ---"
ls -lh prisma-query-engine-* || echo "(no engine binary present; main.py will fetch at startup)"
