FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    munge \
    slurmdbd \
    slurm-client \
    python3 \
    python3-yaml \
    wait-for-it \
    && rm -rf /var/lib/apt/lists/*

# Munge key — fixed so the container is reproducible across rebuilds
RUN dd if=/dev/urandom bs=1 count=1024 > /etc/munge/munge.key \
    && chown munge:munge /etc/munge/munge.key \
    && chmod 400 /etc/munge/munge.key

# SLURM config
COPY docker/slurmdbd.conf /etc/slurm/slurmdbd.conf
RUN chown slurm:slurm /etc/slurm/slurmdbd.conf && chmod 600 /etc/slurm/slurmdbd.conf

# Runtime dirs
RUN mkdir -p /var/log/slurm /run/slurm \
    && chown slurm:slurm /var/log/slurm /run/slurm

# Test UNIX users and groups (appended to the base /etc/passwd and /etc/group)
COPY docker/test_passwd /tmp/test_passwd
COPY docker/test_group  /tmp/test_group
RUN cat /tmp/test_passwd >> /etc/passwd \
    && cat /tmp/test_group  >> /etc/group

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /opt/slurm_account_sync
