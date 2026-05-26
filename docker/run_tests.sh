#!/bin/bash
# Run inside the slurm container:
#   docker compose exec slurm /opt/slurm_account_sync/docker/run_tests.sh

set -e
cd /opt/slurm_account_sync
CONFIG=docker/test_accounts.yml
PASS=0
FAIL=0

ok()   { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

section() { echo; echo "=== $1 ==="; }

# ── 1. Dry run ────────────────────────────────────────────────────────────────
section "Dry run (no changes to SLURM)"
output=$(python3 main.py --file "$CONFIG" 2>&1)
echo "$output"

if echo "$output" | grep -q "sacctmgr"; then
    ok "dry run printed sacctmgr commands"
else
    fail "dry run produced no sacctmgr commands"
fi

accounts_before=$(sacctmgr -nrP show accounts 2>/dev/null | grep -v root || true)
if [ -z "$accounts_before" ]; then
    ok "no accounts created during dry run"
else
    fail "accounts appeared after dry run — something was executed"
fi

# ── 2. Apply ──────────────────────────────────────────────────────────────────
section "Apply (--execute)"
python3 main.py --file "$CONFIG" --execute 2>&1

# Accounts
section "Verify accounts"
for acc in research ml_group bio_group; do
    if sacctmgr -nrP show account "$acc" | grep -q "$acc"; then
        ok "account '$acc' exists"
    else
        fail "account '$acc' missing"
    fi
done

if sacctmgr -nrP show assoc account=ml_group format=account,parentname | grep -qF "ml_group|research"; then
    ok "ml_group parent is research"
else
    fail "ml_group parent is not research"
fi

# Users
section "Verify users"
for usr in alice bob carol dave; do
    if sacctmgr -nrP show user "$usr" | grep -q "$usr"; then
        ok "user '$usr' exists"
    else
        fail "user '$usr' missing"
    fi
done

# Associations
section "Verify associations"
for usr in alice bob; do
    if sacctmgr -nrP show assoc user="$usr" account=ml_group | grep -q "$usr"; then
        ok "$usr has ml_group association"
    else
        fail "$usr missing ml_group association"
    fi
done

for usr in carol dave; do
    if sacctmgr -nrP show assoc user="$usr" account=bio_group | grep -q "$usr"; then
        ok "$usr has bio_group association"
    else
        fail "$usr missing bio_group association"
    fi
done

for usr in alice bob; do
    if sacctmgr -nrP show assoc user="$usr" account=bio_group | grep -q "$usr"; then
        fail "$usr unexpectedly has bio_group association"
    else
        ok "$usr correctly absent from bio_group"
    fi
done

# Default accounts
section "Verify default accounts"
for usr in alice bob; do
    default=$(sacctmgr -nrP show user "$usr" format=DefaultAccount | tail -1)
    if [ "$default" = "ml_group" ]; then
        ok "$usr defaultaccount is ml_group"
    else
        fail "$usr defaultaccount is '$default', expected ml_group"
    fi
done

# ── 3. Idempotency ────────────────────────────────────────────────────────────
section "Idempotency (second --execute should change nothing)"
output=$(python3 main.py --file "$CONFIG" --execute 2>&1)
echo "$output"
if echo "$output" | grep -qiE "^\s*/usr/bin/sacctmgr -i (create|delete|modify)"; then
    fail "second run issued modification commands"
else
    ok "second run was a no-op"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
