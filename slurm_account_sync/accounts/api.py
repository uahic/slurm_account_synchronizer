import logging
import utils
from .. import shell
from slurm_account_sync.accounts.account import (
    Account,
    RESET_VALUES,
    get_account_fields,
)
from typing import List, Set
from ..users.user import User

logger = logging.getLogger(__name__)


def create_account(account: Account, dry_run=False) -> None:
    cmd = f'$(which sacctmgr) -i create account {account.name} description="{account.description}"'

    acc_fields = account.get_fields(exclude_fields=["name", "description"])
    for field in acc_fields:
        cmd += f" {field[0]}={field[1]}"
    result = shell.execute_command(cmd, dry_run=dry_run)


def delete_accounts(name: str, dry_run=False) -> None:
    if name:
        cmd = f"$(which sacctmgr) -i delete account {name}"
        result = shell.execute_command(cmd, dry_run=dry_run)
        if result:
            logger.debug(result)


def modify_account(account: Account, prev_account: Account, dry_run=False) -> None:
    if account.cluster != prev_account.cluster:
        logger.warning(
            f"Slurm does not allow to modify the cluster attribute [before={prev_account.cluster}, requested={account.cluster}]. Ignoring."
        )

    differences = account.get_difference(prev_account)

    if len(differences) == 0:
        return

    cmd = f"$(which sacctmgr) -i modify account where name={account.name}"
    if account.cluster:
        cmd += f" cluster={account.cluster}"
    cmd += f" set"

    for key, prev_value, value in differences:
        # logger.info(f"Key={key}, prevVal={t[1]}, val={value}")
        if not value:
            value = RESET_VALUES.get(key)
        if value is None:
            value = -1

            if "tres" in key:
                if not prev_value:
                    continue
                else:
                    prev_tres_keys = map(
                        lambda x: x.split("=")[0] + "=-1", prev_value.split(",")
                    )
                    value = ",".join(prev_tres_keys)
        cmd += f' {key}="{value}"'

    result = shell.execute_command(cmd, dry_run=dry_run)


def get_existing_accounts() -> dict:
    acc_fields = get_account_fields()
    acc_fmt = ",".join(acc_fields)
    acc_fmt = acc_fmt.replace("name", "account")
    acc_fmt = acc_fmt.replace("parent", "parentname")
    name_index = acc_fields.index("name")
    cmd = f"$(which sacctmgr) -nrP show accounts WithAssoc format=User,{acc_fmt}"
    accounts = shell.execute_command(cmd, dry_run=False, hide_log=True)
    account_dict = {}
    for acc_rec in accounts:
        values = acc_rec.split("|")
        # Filter out user-specific associations, we are only interested in general account
        if values[0] != "":
            continue
        if values[name_index + 1] == "root":
            continue
        # Replace empty strings/Nones with particular values
        assert (
            values[name_index + 1] not in account_dict
        ), "A record of the same account appears multiple times. This should not happen."
        values = [x if x != "" else None for x in values]
        account_dict[values[name_index + 1]] = Account(*values[1:])
    return account_dict


def add_user_accounts(users: List[User], accounts: List[Account], config: dict) -> None:
    for usr in users:
        acc = Account(
            usr.user,
            f"User Account for {usr.user}",
            cluster=config["defaults"]["cluster"],
            qos=config["defaults"]["qos"],
            defaultqos=config["defaults"]["defaultqos"],
        )
        accounts.append(acc)


def delete_unused_accounts(accs: List[Account], dry_run=False) -> None:

    def get_removable_accounts(
        existing_accs: List[Account], cfg_accs: List[Account]
    ) -> Set[str]:
        existing_names = [s.name for s in existing_accs]
        cfg_names = [s.name for s in cfg_accs]
        return set(existing_names).difference(cfg_names)

    prev_accounts = get_existing_accounts()
    removable_accs = get_removable_accounts(prev_accounts.values(), accs)
    for name in removable_accs:
        delete_accounts(name, dry_run=dry_run)


def create_accounts(accs: List[Account], dry_run=False) -> None:
    acc_map = {acc.name: acc for acc in accs}
    sorted_acc_keys = utils.topological_sort(acc_map)

    prev_accounts = get_existing_accounts()

    for name in sorted_acc_keys:
        if not name in prev_accounts:
            create_account(acc_map[name], dry_run=dry_run)


def modify_accounts(accs: List[Account], dry_run=False) -> None:
    acc_map = {acc.name: acc for acc in accs}
    # sorted_acc_keys = utils.topological_sort(acc_map)

    prev_accounts = get_existing_accounts()
    updatable_keys = utils.get_overlapping_accounts(prev_accounts, acc_map)

    for name in updatable_keys:
        modify_account(acc_map[name], prev_accounts[name], dry_run=dry_run)
