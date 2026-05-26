#!/bin/bash
set -e

echo "[entrypoint] Starting munge..."
service munge start

echo "[entrypoint] Waiting for database..."
wait-for-it db:3306 --timeout=60 --strict -- echo "[entrypoint] Database is up"

echo "[entrypoint] Starting slurmdbd..."
slurmdbd
# Give slurmdbd a moment to initialize the schema
sleep 3

echo "[entrypoint] Registering cluster..."
sacctmgr -i add cluster test-cluster

echo "[entrypoint] Ready. SLURM accounting is available via sacctmgr."
