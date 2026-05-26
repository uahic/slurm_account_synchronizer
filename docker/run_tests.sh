#!/bin/bash
# Run inside the slurm container:
#   docker compose exec slurm /opt/slurm_account_sync/docker/run_tests.sh

set -e
cd /opt/slurm_account_sync
CONFIG=docker/test_accounts.yml
PASS=0
FAIL=0

ok()   { echo "  PASS: $1"; ((PASS++)); }
fail() { echo "  FAIL: $1"; ((FAIL++)); }

section() { echo; echo "=== $1 ==="; }

# ── 1. Dry run ────────────────────────────────────────────────────────────────
section "Dry run (no changes to SLURM)"
output=$(python3 main.py --file "$CONFIG" 2>&1)
echo "$output"
echo "$output" | grep -q "sacctmgr" \
    && ok "dry run printed sacctmgr commands" \
    || fail "dry run produced no sacctmgr commands"

# Verify sacctmgr was NOT actually called (accounts still empty)
accounts_before=$(sacctmgr -nrP show accounts 2>/dev/null | grep -v root || true)
[ -z "$accounts_before" ] \
    && ok "no accounts created during dry run" \
    || fail "accounts appeared after dry run — something was executed"

# ── 2. Apply ──────────────────────────────────────────────────────────────────
section "Apply (--execute)"
python3 main.py --file "$CONFIG" --execute 2>&1

# Accounts
section "Verify accounts"
for acc in research ml_group bio_group; do
    sacctmgr -nrP show account "$acc" | grep -q "$acc" \
        && ok "account '$acc' exists" \
        || fail "account '$acc' missing"
done

# Hierarchy: ml_group.parent == research
parent=$(sacctmgr -nrP show account ml_group format=ParentName | tail -1)
[ "$parent" = "research" ] \
    && ok "ml_group parent is research" \
    || fail "ml_group parent is '$parent', expected research"

# Users
section "Verify users"
for usr in alice bob carol dave; do
    sacctmgr -nrP show user "$usr" | grep -q "$usr" \
        && ok "user '$usr' exists" \
        || fail "user '$usr' missing"
done

# Associations — alice and bob should be in ml_group (via ml_approved)
section "Verify associations"
for usr in alice bob; do
    sacctmgr -nrP show assoc user="$usr" account=ml_group | grep -q "$usr" \
        && ok "$usr has ml_group association" \
        || fail "$usr missing ml_group association"
done

# carol and dave should be in bio_group
for usr in carol dave; do
    sacctmgr -nrP show assoc user="$usr" account=bio_group | grep -q "$usr" \
        && ok "$usr has bio_group association" \
        || fail "$usr missing bio_group association"
done

# alice and bob should NOT be in bio_group
for usr in alice bob; do
    sacctmgr -nrP show assoc user="$usr" account=bio_group | grep -q "$usr" \
        && fail "$usr unexpectedly has bio_group association" \
        || ok "$usr correctly absent from bio_group"
done

# Default accounts — ml_approved maps to ml_group
section "Verify default accounts"
for usr in alice bob; do
    default=$(sacctmgr -nrP show user "$usr" format=DefaultAccount | tail -1)
    [ "$default" = "ml_group" ] \
        && ok "$usr defaultaccount is ml_group" \
        || fail "$usr defaultaccount is '$default', expected ml_group"
done

# ── 3. Idempotency ────────────────────────────────────────────────────────────
section "Idempotency (second --execute should change nothing)"
output=$(python3 main.py --file "$CONFIG" --execute 2>&1)
echo "$output"
echo "$output" | grep -qiE "create|delete|modify" \
    && fail "second run issued modification commands" \
    || ok "second run was a no-op"

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
