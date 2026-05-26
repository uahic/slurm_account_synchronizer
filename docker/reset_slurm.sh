#!/bin/bash
# Run inside the slurm container to wipe all accounts, users, and associations.
# Leaves only the built-in 'root' account intact.
set -e

echo "[reset] Removing all users..."
users=$(sacctmgr -nrP show users format=user | grep -v '^root$' | tr '\n' ',' | sed 's/,$//')
if [ -n "$users" ]; then
    sacctmgr -i delete user name="$users"
else
    echo "[reset] No users to remove."
fi

echo "[reset] Removing all accounts..."
accounts=$(sacctmgr -nrP show accounts format=account | grep -v '^root$' | tr '\n' ',' | sed 's/,$//')
if [ -n "$accounts" ]; then
    sacctmgr -i delete account name="$accounts"
else
    echo "[reset] No accounts to remove."
fi

echo "[reset] Done. Current state:"
sacctmgr show accounts
