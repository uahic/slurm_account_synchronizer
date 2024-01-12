import logging
from dataclasses import dataclass
from typing import List
from utils import execute_command
from associations import Association

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class User:
    user: str  # Unix name
    defaultaccount: str


def create_new_user(user: User, dry_run=False) -> None:
    cmd = f"$(which sacctmgr) -i create user name={user.user} DefaultAccount={user.defaultaccount}"
    result = execute_command(cmd, dry_run=dry_run)


def delete_user(user_name: str, dry_run=False) -> None:
    cmd = f"$(which sacctmgr) -i delete user name={user_name}"
    result = execute_command(cmd, dry_run=dry_run)


def get_existing_users() -> dict:
    user_format = ",".join(User.__dataclass_fields__.keys())
    cmd = f'$(which sacctmgr) -nrP show user WithAssoc format="{user_format}"'
    user_list = execute_command(cmd, hide_log=True)
    user_dict = {}
    for user_record in user_list:
        values = user_record.split("|")
        user_dict[values[0]] = User(*values)
    return user_dict


def get_default_account(
    user_name: str, config: dict, unix_grp_map: dict, association_map: dict
) -> str:
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

    # # 3. Priority: use the account specified in the first declared association that contains this user
    # for account in association_map.keys():
    #     if user_name in association_map[account]:
    #         return account

    # Fallback defaultaccount=<username>
    return user_name


def modify_user_account(prev_user: User, user: User, dry_run=False) -> None:
    if prev_user.defaultaccount != user.defaultaccount:
        cmd = f"$(which sacctmgr) -i modify user where user={user.user} set defaultaccount={user.defaultaccount}"
        result = execute_command(cmd, dry_run=dry_run)


def create_users(users: List[User], dry_run=False) -> None:
    existing_users = get_existing_users()
    for user in users:
        if not user.user in existing_users:
            create_new_user(user, dry_run=dry_run)


def modify_users(users: List[User], dry_run=False) -> None:
    existing_users = get_existing_users()
    for user in users:
        if user.user in existing_users:
            modify_user_account(existing_users[user.user], user, dry_run=dry_run)


def get_removable_users(users: List[User]) -> List[str]:
    existing_user_map = get_existing_users()
    existing_usr_set = set(existing_user_map.keys())
    removable_user_names = existing_usr_set.difference(map(lambda x: x.user, users))
    removable_user_names.remove("root")
    return removable_user_names


def delete_unused_users(users: List[User], dry_run=False) -> None:
    removable_users = get_removable_users(users)
    for name in removable_users:
        delete_user(name, dry_run=dry_run)


def get_users_from_associations(
    associations: List[Association],
    unix_grp_map: dict,
    association_map: dict,
    config: dict,
) -> List[User]:
    users = []

    user_names = list(set(map(lambda x: x.user, associations)))
    for usr_name in user_names:
        default_account = get_default_account(
            usr_name, config, unix_grp_map, association_map
        )
        users.append(User(usr_name, default_account))
    return users
