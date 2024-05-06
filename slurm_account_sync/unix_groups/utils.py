from typing import List

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
