#!/usr/bin/env python3

import sys
import yaml
import logging
import argparse

from slurm_account_sync import from_config

logger = logging.getLogger(__name__)


def setup_logger() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return


if __name__ == "__main__":
    setup_logger()
    parser = argparse.ArgumentParser(prog="Slurm Account Sync Tool")
    parser.add_argument(
        "-e",
        "--execute",
        action="store_true",
        help="Execute sacctmgr commands instead of printing them",
        default=False,
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Location of the configuration file (yaml)",
        default="accounts.yml",
    )
    args = parser.parse_args()

    with open(args.file, "r") as f:
        config = yaml.safe_load(f)

    slurm_synchronizer = from_config(config)
    slurm_synchronizer.synchronize(not args.execute)
