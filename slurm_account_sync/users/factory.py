import logging
from typing import List
from associations import Association
from user import User

logger = logging.getLogger(__name__)


def get_users_from_associations(
    associations: List[Association],
    unix_groups: dict,
    config: dict,
) -> List[User]:
    users = []

    user_names = list(set(map(lambda x: x.user, associations)))
    for usr_name in user_names:
        default_account = get_default_account(usr_name, config, unix_groups)
        users.append(User(usr_name, default_account))
    return users


def get_default_account(user_name: str, config: dict, unix_grp_map: dict) -> str:
    # 1. Priority: User specific defaults
    user_defaults = config["defaults"].get("users")
    if user_defaults and user_name in user_defaults:
        return user_defaults.get(user_name)

    # 2. Priority: Group-specific defaults
    # groups = user_grp_map.get(user_name) or []
    default_groups = config["defaults"].get("groups")
    if default_groups:
        for grp_name, grp_entry in default_groups.items():
            if grp_name in unix_grp_map and user_name in unix_grp_map[grp_name].users:
                if not grp_entry["account"]:
                    raise Exception(
                        f"Key 'account' is missing in defaults/groups/{grp_name}"
                    )
                return grp_entry["account"]

    # 3. User Account
    # Fallback defaultaccount=<username>
    return user_name
