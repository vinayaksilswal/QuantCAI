#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python setup_prisma.py
prisma generate --schema=schema_py.prisma
prisma db push --schema=schema_py.prisma
