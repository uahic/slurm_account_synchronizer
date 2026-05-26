import logging
from typing import List
from ..shell import execute_command
from ..users.user import User

logger = logging.getLogger(__name__)


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
    if ("root" in removable_user_names):
        removable_user_names.remove("root")
    return removable_user_names


def delete_unused_users(users: List[User], dry_run=False) -> None:
    removable_users = get_removable_users(users)
    for name in removable_users:
        delete_user(name, dry_run=dry_run)

