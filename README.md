# slurm-account-sync

Keeps SLURM user associations in sync with UNIX group membership.

```
  UNIX groups (/etc/group)        YAML config (accounts.yml)
  ┌─────────────────────┐         ┌──────────────────────────┐
  │ ml_team:  alice,bob │         │ declared_groups          │
  │ bio_team: carol     │─────┐   │   ml_approved:           │
  │ hpc_users: alice,   │     │   │     groups: [ml_team]    │
  │           carol,dave│     │   │     whitelist: [hpc_users]│
  └─────────────────────┘     │   │ accounts:                │
           │ getent group      │   │   research > ml_group    │
           │                  └──▶│ associations:            │
           ▼                      │   ml_gpu_assoc:          │
  ┌─────────────────────┐         │     account: ml_group    │
  │  Group expansion    │◀────────│     groups: [ml_approved]│
  │  + set operations   │         └──────────────────────────┘
  │  (union/intersect/  │
  │   add/exclude)      │
  └────────┬────────────┘
           │ resolved (user, account) pairs
           ▼
  ┌─────────────────────┐         ┌──────────────────────────┐
  │   Diff engine       │         │  SLURM accounting DB     │
  │                     │◀────────│  sacctmgr list assoc     │
  │  desired vs current │         └──────────────────────────┘
  └────────┬────────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
  create       delete
  assoc        assoc
     │            │
     └─────┬──────┘
           ▼
  ┌─────────────────────┐
  │     sacctmgr        │   dry-run: only print commands
  │  (--dry-run / live) │   --execute: apply to SLURM
  └─────────────────────┘
```

SLURM requires explicit (user, account, partition, cluster) association tuples for every user and has no native mechanism to derive these from UNIX groups. This tool reads a YAML config, expands group memberships via `getent group`, and drives `sacctmgr` to create, update, and delete associations accordingly.

The core of this repository was not generated via AI models, only the docker testing environment.

## Requirements

- Python 3.x
- `sacctmgr` in `$PATH`
- Read access to `/etc/group` (via `getent`)

## Usage

```sh
# Dry run (default) — prints sacctmgr commands, executes nothing
python main.py

# Apply changes
python main.py --execute

# Use a different config file
python main.py --file /etc/slurm/accounts.yml
```

| Flag | Short | Description |
|------|-------|-------------|
| `--execute` | `-e` | Execute `sacctmgr` commands. Without this flag the tool only logs what it would do. |
| `--file PATH` | `-f` | Path to the YAML config file. Defaults to `accounts.yml` in the current directory. |

## Configuration

The config file is `accounts.yml` by default.

### Top-level structure

```yaml
declared_groups:   # optional — define virtual groups from real UNIX groups
defaults:          # required — cluster, org, and default account mappings
accounts:          # required — SLURM account hierarchy
associations:      # required — maps groups to accounts
```

### `declared_groups`

Virtual groups built from real UNIX groups using set operations, applied in this order:

1. Union of all listed `groups`
2. Add individual users via `add_users`
3. Remove individual users via `exclude_users`
4. Intersect with `whitelist` groups

```yaml
declared_groups:
  ml_approved:
    groups:
      - ml_team
    whitelist:
      - cluster_users
    add_users:
      - serviceaccount
    exclude_users:
      - intern01
```

Virtual groups can be used anywhere a real UNIX group can.

### `defaults`

```yaml
defaults:
  cluster: my-cluster    # must match ClusterName in slurm.conf
  organization: myorg
  groups:                # optional: default account per group
    ml_approved:
      account: ml_group
  users:                 # optional: default account per user (highest priority)
    jdoe:
      account: research
```

Default account resolution order per user:
1. `defaults/users/<username>` if defined
2. First matching entry in `defaults/groups` where the user is a member
3. Falls back to a personal account named after the user

### `accounts`

Defines the SLURM account hierarchy. Accounts without a `parent` are placed under `root`.

```yaml
accounts:
  research:
    description: Top-level research account
    fairshare: 10
  ml_group:
    description: Machine learning research
    parent: research
    fairshare: 5
  bio_group:
    description: Bioinformatics
    parent: research
    fairshare: 3
```

Supports all `sacctmgr` limit fields: `fairshare`, `qos`, `defaultqos`, `grptres`, `maxtres`, `maxwall`, etc.

### `associations`

Maps groups (real or virtual) to accounts with optional per-association limits.

```yaml
associations:
  ml_gpu_assoc:
    account: ml_group
    groups:
      - ml_approved
    extra_users:
      - serviceaccount
    fairshare: 55
```

### Full example

See [`example_accounts.yml`](example_accounts.yml).

## Testing

A self-contained test environment is in [`docker/`](docker/). It runs MariaDB and a SLURM accounting daemon (`slurmdbd`) with four test users (`alice`, `bob`, `carol`, `dave`) pre-populated in `/etc/group`.

### Docker

```sh
# Build and start
docker compose -f docker/docker-compose.yml up --build -d

# Run the test suite
docker compose -f docker/docker-compose.yml exec slurm docker/run_tests.sh

# Poke around manually
docker compose -f docker/docker-compose.yml exec slurm bash

# Tear down
docker compose -f docker/docker-compose.yml down -v
```

### Podman

`podman-compose` is a separate package — install it first if needed (`pip install podman-compose` or via your distro).

```sh
# Build and start
podman-compose -f docker/docker-compose.yml up --build -d

# Run the test suite
podman-compose -f docker/docker-compose.yml exec slurm docker/run_tests.sh

# Poke around manually
podman-compose -f docker/docker-compose.yml exec slurm bash

# Tear down
podman-compose -f docker/docker-compose.yml down -v
```

Alternatively, if you have Podman 4.4+ with the Docker-compatible CLI alias:

```sh
podman compose -f docker/docker-compose.yml up --build -d
```

The test suite covers dry-run safety, account creation, association correctness, and idempotency.
