import logging
from . import accounts as _accounts
from . import associations as _associations
from . import unix_groups as _unix_groups
from . import users as _users

from .checks import (
    check_default_accounts,
    check_association_entries,
    check_default_accounts_are_defined,
)

logger = logging.getLogger(__name__)


class SLURMAccountSynchronizer:

    def __init__(
        self, config: dict, associations: dict, users, groups, accounts
    ) -> None:
        self.config = config
        self.associations = associations
        self.association_map = _associations.create_association_map(associations)
        self.users = users
        self.groups = groups
        self.accounts = accounts
        self.sanity_checks()

    def sanity_checks(self) -> None:
        logger.info("[Running sanity checks]")
        check_association_entries(self.config)
        check_default_accounts(self.config, self.users, self.association_map)
        check_default_accounts_are_defined(self.config)

    def synchronize(self, dry_run=False) -> None:
        # 1. Accounts
        logger.info("[Create missing accounts]")
        _accounts.api.create_accounts(self.accounts, dry_run=dry_run)

    # logger.info("[Create and modify users]")
    # create_users(users, dry_run=dry_run)

        # 2. Create Associations
        logger.info("[Create associations]")
        existing_assocs = _associations.api.get_existing_associations()
        _associations.api.create_associations(
            self.associations, existing_assocs, dry_run=dry_run
        )

        # 3. Update/Remove Users
        logger.info("[Remove users]")
        _users.api.delete_unused_users(self.users, dry_run=dry_run)
        logger.info("[Modify users]")
        _users.api.modify_users(self.users, dry_run=dry_run)

        # 4. Update/Remove Associations
        logger.info("[Update or delete associations]")
        _associations.api.update_and_delete_associations(
            self.associations, existing_assocs, dry_run=dry_run
        )

        # 5. Remove unused Accounts
        logger.info("[Delete unused accounts]")
        _accounts.api.delete_unused_accounts(self.accounts, dry_run=dry_run)

        # 6. Update existing Accounts
        logger.info("[modify existing accounts]")
        _accounts.api.modify_accounts(self.accounts, dry_run=dry_run)


def from_config(config: dict) -> SLURMAccountSynchronizer:
    unix_groups = _unix_groups.get_unix_groups_from_config(config)
    associations = _associations.get_user_associations_from_config(config, unix_groups)
    users = _users.get_users_from_associations(associations, unix_groups, config)
    accounts = _accounts.accounts_from_config(config)
    accounts.extend(_accounts.accounts_from_user_list(users, config))

    return SLURMAccountSynchronizer(config, associations, users, unix_groups, accounts)
