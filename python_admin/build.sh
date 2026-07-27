#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Generate the Python client and sync the schema first. Besides producing the
# client, these populate node_modules/ with the Node CLI's own engine binaries,
# which setup_prisma.py can fall back to if the direct download fails.
prisma generate --schema=schema_py.prisma
prisma db push --schema=schema_py.prisma

# Install the query engine next to the app. /opt/render/.cache does not exist at
# runtime, so this copy into the source tree is the only thing that survives
# into the running container. Exits non-zero on failure — do not deploy an app
# that cannot reach the database.
python setup_prisma.py

echo "--- Prisma engine provisioned ---"
ls -lh prisma-query-engine-*
