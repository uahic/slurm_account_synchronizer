import logging
from dataclasses import dataclass, field
from typing import List, Set
from utils import execute_command

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UnixGroup:
    name: str
    gid: int  # -1 means 'virtual group'
    users: List[str] = field(default_factory=list)

    def has_user(self, name: str) -> bool:
        return name in self.users


def get_unix_group_map() -> dict:
    group_accounts = {}
    cmd = f"getent group"
    group_lines = execute_command(cmd)
    for g in group_lines:
        g_entry = g.split(":")
        if g_entry[0] == "root":
            continue
        usr_list = g_entry[3].split(",")
        if len(usr_list)>0 and usr_list[-1]=="":
            del usr_list[-1]
        unix_grp = UnixGroup(g_entry[0], g_entry[2], usr_list)
        group_accounts[g_entry[0]] = unix_grp
    return group_accounts


def check_valid_declared_groups(unix_group_map: dict, config: dict) -> None:
    if not config["declared_groups"]:
        raise Exception(f"Top-level Key 'declared_groups' are not found")

    def check_group_in_key_exist(grp_entry: dict, key: str) -> None:
        for unix_grp_name in grp_entry[key].keys():
            if not unix_grp_name in unix_group_map:
                raise Exception(
                    f"The group with name '{unix_grp_name}' declared in declared_groups/{grp_name}/{key}/ does not exist on your system."
                )

        for grp_name, grp_entry in config["declared_groups"].items():
            if grp_name in unix_group_map:
                raise Exception(
                    f"Declared (virtual) group name '{grp_name}' collides with a real unix group name."
                )
            if not "groups" in grp_entry or len(grp_entry["groups"]) < 1:
                raise Exception(
                    f"Declared group '{grp_name}' lacks the key 'groups' or has no entries."
                )
            check_group_in_key_exist(grp_entry, "groups")
            check_group_in_key_exist(grp_entry, "whitelist")

            if (
                grp_entry["defaultaccount"]
                and not grp_entry["defaultaccount"] in config["accounts"]
            ):
                raise Exception(
                    f"Defaultaccount specified in declared_groups/{grp_name} is not defined in the accounts section."
                )


def add_declared_groups_from_config(unix_group_map: dict, config: dict) -> None:
    if not "declared_groups" in config:
        return
    check_valid_declared_groups(unix_group_map, config)
    for new_grp, grp_entry in config['declared_groups'].items():
        group_users = groups_to_users(grp_entry.get("groups") or [], unix_group_map)
        white_users = groups_to_users(grp_entry.get("whitelist") or [], unix_group_map)
        added_users = grp_entry.get("add_users") or []
        excld_users = grp_entry.get("exclude_users") or []
        users = merge_users(group_users, added_users, excld_users, white_users)
        print(users)
        unix_group_map[new_grp] = UnixGroup(new_grp, -1, users)


def merge_users(
    group_users: List[str] = [],
    extra_users: List[str] = [],
    excluded_users: List[str] = [],
    intersect_users: List[str] = [],
) -> List[str]:
    user_set = set()
    if group_users:
        user_set.update(group_users)
    if extra_users:
        user_set.update(extra_users)
    if excluded_users:
        user_set.discard(*excluded_users)
    if intersect_users:
        user_set.intersection(intersect_users)
    return list(user_set)


def get_inverse_group_map(group_map: dict) -> dict:
    user_to_grp_map = {}

    for grp_name, grp in group_map.items():
        for usr_name in grp.users:
            user_to_grp_map.setdefault(usr_name, set()).add(grp_name)
    return user_to_grp_map


def groups_to_users(group_names: List[list], group_map: dict) -> List[str]:
    users = []
    for g_name in group_names:
        g_users = group_map.get(g_name)
        if not g_users:
            raise Exception(f'unix_group_map does not contain unix group: "{g_name}"')
        users.extend(g_users.users)
    return users
