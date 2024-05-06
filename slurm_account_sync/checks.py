import logging
from typing import List
from users.user import User

logger = logging.getLogger(__name__)


def check_association_entries(config: dict) -> None:
    assoc_section = config["associations"]

    if assoc_section is None:
        return

    for assoc_name, assoc_entry in assoc_section.items():
        if not "account" in assoc_entry:
            raise Exception(f"Association '{assoc_name}' is missing the key 'account'")
        if not "groups" in assoc_entry and not "extra_users" in assoc_entry:
            raise Exception(
                f"Association '{assoc_name}' lacks at least one of the following keys: 'groups' or 'extra_users'"
            )


def check_default_accounts(
    config: dict, users: List[User], association_map: dict
) -> None:
    def get_error_message(acc_name: str, usr_name: str, section_name: str) -> str:
        return f"The default account '{acc_name}' specified for user '{usr_name}' is not specified in the {section_name} section."

    for u in users:
        # Check if account is defined
        if (
            not u.defaultaccount in config["accounts"]
            and not u.defaultaccount == u.user
        ):
            raise Exception(get_error_message(u.defaultaccount, u.user, "accounts"))

        # Check if at least one association for that user/account is defined
        if (
            len(association_map[u.defaultaccount][u.user]) < 1
            and not u.defaultaccount == u.user
        ):
            raise Exception(get_error_message(u.defaultaccount, u.user, "associations"))


def check_default_accounts_are_defined(config: dict) -> None:
    groups = config["defaults"].get("groups")
    if groups:
        for grp_name, grp_entry in groups.items():
            if not grp_entry["account"] in config["accounts"]:
                raise Exception(
                    f"The default account '{grp_entry['account']}' of group '{grp_name}' as specified in the defaults/groups section is not specified in the accounts section."
                )

    users = config["defaults"].get("users")
    if users:
        for usr_name, usr_entry in users.items():
            if not usr_entry["account"] in config["accounts"]:
                raise Exception(
                    f"The default account '{usr_entry['account']}' of user '{usr_name}' as specified in the defaults/groups section is not specified in the accounts section."
                )
