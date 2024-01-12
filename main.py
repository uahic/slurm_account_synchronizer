#!/usr/bin/env python3

import sys
from typing import List
import yaml
import logging
import argparse

logger = logging.getLogger(__name__)

from accounts import (
    accounts_from_config,
    add_user_accounts,
    delete_unused_accounts,
    create_or_modify_accounts,
)

from associations import (
    user_associations_from_config,
    create_association_map,
    Association,
    update_and_delete_associations,
    check_illegal_association_overlaps,
    get_existing_associations,
    create_associations,
)

from groups import get_unix_group_map, add_declared_groups_from_config
from checks import check_default_accounts, check_association_entries, check_default_accounts_are_defined
from user import (
    get_users_from_associations,
    create_users,
    modify_users,
    delete_unused_users,
    User,
)


def sanity_checks(
    config: dict,
    associations: List[Association],
    association_map: dict,
    users: List[User],
) -> None:
    check_association_entries(config)
    check_default_accounts(config, users, association_map)
    check_default_accounts_are_defined(config)
    check_illegal_association_overlaps(associations, association_map)


def synchronize(config: dict, dry_run=True):
    unix_grp_map = get_unix_group_map()
    add_declared_groups_from_config(unix_grp_map, config)
    assocs = user_associations_from_config(config, unix_grp_map)
    prev_assocs = get_existing_associations()
    association_map = create_association_map(assocs)
    users = get_users_from_associations(assocs, unix_grp_map, association_map, config)

    logger.info("[Running sanity checks]")
    sanity_checks(config, assocs, association_map, users)

    logger.info("[Create and modify accounts]")
    cfg_accounts = accounts_from_config(config)
    add_user_accounts(users, cfg_accounts, config)
    create_or_modify_accounts(cfg_accounts, dry_run=dry_run)

    logger.info("[Create and modify users]")
    create_users(users, dry_run=dry_run)

    logger.info("[Create Associations]")
    create_associations(assocs, prev_assocs, dry_run=dry_run)

    logger.info("[Remove users]")
    delete_unused_users(users, dry_run=dry_run)

    logger.info("[Modify users]")
    modify_users(users, dry_run=dry_run)

    logger.info("[Update or delete associations]")
    update_and_delete_associations(assocs, prev_assocs, dry_run=dry_run)

    logger.info("[Delete unused accounts]")
    delete_unused_accounts(cfg_accounts, dry_run=dry_run)


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

    synchronize(config, dry_run=not args.execute)
