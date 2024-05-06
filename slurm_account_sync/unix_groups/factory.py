import api
import utils
import validation
from unixgroup import UnixGroup


def get_unix_groups_from_config(config: dict) -> dict:
    unix_group_map = api.get_unix_group_map()
    _add_declared_groups_from_config(unix_group_map, config)


def _add_declared_groups_from_config(unix_group_map: dict, config: dict) -> None:
    if not "declared_groups" in config:
        return
    validation.check_valid_declared_groups(unix_group_map, config)
    for new_grp, grp_entry in config["declared_groups"].items():
        group_users = utils.groups_to_users(
            grp_entry.get("groups") or [], unix_group_map
        )
        white_users = utils.groups_to_users(
            grp_entry.get("whitelist") or [], unix_group_map
        )
        added_users = grp_entry.get("add_users") or []
        excld_users = grp_entry.get("exclude_users") or []
        users = utils.merge_users(group_users, added_users, excld_users, white_users)
        print(users)
        unix_group_map[new_grp] = UnixGroup(new_grp, -1, users)
