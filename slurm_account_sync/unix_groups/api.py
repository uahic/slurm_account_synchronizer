import logging
from unixgroup import UnixGroup
from .. import shell

logger = logging.getLogger(__name__)


def get_unix_group_map() -> dict:
    group_accounts = {}
    cmd = f"getent group"
    group_lines = shell.execute_command(cmd)
    for g in group_lines:
        g_entry = g.split(":")
        if g_entry[0] == "root":
            continue
        usr_list = g_entry[3].split(",")
        if len(usr_list) > 0 and usr_list[-1] == "":
            del usr_list[-1]
        unix_grp = UnixGroup(g_entry[0], g_entry[2], usr_list)
        group_accounts[g_entry[0]] = unix_grp
    return group_accounts
