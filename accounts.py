import logging
import queue
from dataclasses import dataclass
from typing import List, Set, Tuple
from utils import execute_command
from user import User

logger = logging.getLogger(__name__)

# All other values not listed here have a reset value of '-1'
RESET_VALUES = {"parent": "root", "qos":"", "organization": ""}
DEFAULT_VALUES = {"parent": "root", "qos":"", "fairshare": 1}


@dataclass(frozen=False)
class Account:
    # Core
    name: str
    description: str
    parent: str = None
    cluster: str = None

    # Limits
    fairshare: str = None
    defaultqos: str = None
    grptresmins: str = None
    grptres: str = None
    grpjobs: str = None
    grpsubmitjob: str = None
    grpwall: str = None
    maxtresmins: str = None
    maxtres: str = None
    maxjobs: str = None
    maxnodes: str = None
    maxsubmitjobs: str = None
    maxwall: str = None
    organization: str = None
    priority: str = None
    qos: str = None

    def __post_init__(self) -> None:
        # Convert everything except Nones to lowercase strings
        for k in Account.__dataclass_fields__.keys():
            if not getattr(self, k) is None:
                setattr(self, k, str(getattr(self, k)).lower())

        # Fill in default values if necessary
        for k, v in DEFAULT_VALUES.items():
            if not getattr(self, k) or getattr(self, k) == "":
                setattr(self, k, str(v))

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, Account):
            return False
        return self.__dict__ == obj.__dict__

    def get_fields(self, exclude_fields=[]) -> Tuple[str, str]:
        field_keys = filter(
            lambda x: x not in exclude_fields, self.__dataclass_fields__.keys()
        )
        field_keys = filter(lambda x: getattr(self, x) is not None, field_keys)
        return list(map(lambda key: (key, getattr(self, key)), field_keys))


def get_account_fields(exclude_fields=[]) -> List[str]:
    field_keys = filter(
        lambda x: x not in exclude_fields, Account.__dataclass_fields__.keys()
    )
    return list(field_keys)


def get_existing_accounts() -> dict:
    acc_fields = get_account_fields()
    acc_fmt = ",".join(acc_fields)
    acc_fmt = acc_fmt.replace("name", "account")
    acc_fmt = acc_fmt.replace("parent", "parentname")
    name_index = acc_fields.index("name")
    cmd = f"$(which sacctmgr) -nrP show accounts WithAssoc format=User,{acc_fmt}"
    accounts = execute_command(cmd, dry_run=False, hide_log=True)
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


def get_overlapping_accounts(existing_accs: dict, cfg_accs: dict) -> List[str]:
    existing_names = set(existing_accs.keys())
    return list(existing_names.intersection(cfg_accs.keys()))


def get_removable_accounts(
    existing_accs: List[Account], cfg_accs: List[Account]
) -> Set[str]:
    existing_names = [s.name for s in existing_accs]
    cfg_names = [s.name for s in cfg_accs]
    return set(existing_names).difference(cfg_names)


def get_new_accounts(existing_accs: List[Account], cfg_accs: List[Account]) -> Set[str]:
    existing_names = [s.name for s in existing_accs]
    cfg_names = [s.name for s in cfg_accs]
    return set(cfg_names).difference(existing_names)


def topological_sort(acc_dict: dict) -> List[str]:
    child_map = {"root": []}

    # Build child graph
    tmp_acc_dict = acc_dict.copy()
    while len(tmp_acc_dict) > 0:
        key = list(tmp_acc_dict.keys()).pop()
        parent_key = acc_dict[key].parent
        if parent_key is None or parent_key == "":
            parent_key = "root"
        if not parent_key in child_map:
            child_map[parent_key] = [key]
        else:
            child_map[parent_key].append(key)
        del tmp_acc_dict[key]

    # Add accounts breadth-first to the final list of keys
    sorted_arr = []
    fifo = queue.Queue()

    # Initial fifo
    for k in child_map["root"]:
        fifo.put(k)

    # Breadth-first traversal
    while not fifo.empty():
        key = fifo.get()
        sorted_arr.append(key)
        if key in child_map:
            for k in child_map[key]:
                fifo.put(k)

    return sorted_arr


def delete_accounts(name: str, dry_run=False) -> None:
    if name:
        cmd = f"$(which sacctmgr) -i delete account {name}"
        if dry_run:
            logger.info(cmd)
        else:
            result = execute_command(cmd)
            logger.debug(result)


def create_account(account: Account, dry_run=False) -> None:
    cmd = f'$(which sacctmgr) -i create account {account.name} description="{account.description}"'

    acc_fields = account.get_fields(exclude_fields=["name", "description"])
    for field in acc_fields:
        cmd += f" {field[0]}={field[1]}"
    result = execute_command(cmd, dry_run=dry_run)


def get_attribute_diffs(
    account: Account, prev_account: Account
) -> List[Tuple[str, str]]:
    diff_arr = []
    field_keys = get_account_fields(exclude_fields=["name", "cluster"])
    for key in field_keys:
        value = getattr(account, key)
        prev_value = getattr(prev_account, key)
        if value != prev_value:
            diff_arr.append((key, prev_value, value))
    return diff_arr


def modify_account(account: Account, prev_account: Account, dry_run=False) -> None:
    if account.cluster != prev_account.cluster:
        logger.warn(
            f"Slurm does not allow to modify the cluster attribute [before={prev_account.cluster}, requested={account.cluster}]. Ignoring."
        )

    diff_arr = get_attribute_diffs(account, prev_account)

    if len(diff_arr) == 0:
        return

    cmd = f"$(which sacctmgr) -i modify account where name={account.name}"
    if account.cluster:
        cmd += f" cluster={account.cluster}"
    cmd += f" set"

    for t in diff_arr:
        key = t[0]
        value = t[2]
        prev_value = t[1]
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

    result = execute_command(cmd, dry_run=dry_run)


def account_from_cfg_entry(entry: dict, defaults: dict) -> Account:
    values = [
        entry.get(key) or defaults.get(key)
        for key in get_account_fields(exclude_fields=["name"])
    ]
    acc = Account(entry["name"].lower(), *values)
    return acc


def accounts_from_config(config: dict) -> List[Account]:
    defaults = config["defaults"]
    cfg_accounts = config["accounts"]
    accounts = []
    for name, entry in cfg_accounts.items():
        entry["name"] = name
        acc = account_from_cfg_entry(entry, defaults)
        accounts.append(acc)
    return accounts


def add_user_accounts(users: List[User], accounts: List[Account], config: dict) -> None:
    for usr in users:
        acc = Account(
            usr.user,
            f"User Account for {usr.user}",
            cluster=config["defaults"]["cluster"],
            qos=config["defaults"]["qos"],
            defaultqos=config["defaults"]["defaultqos"]
        )
        accounts.append(acc)


def delete_unused_accounts(accs: List[Account], dry_run=False) -> None:
    prev_accounts = get_existing_accounts()
    removable_accs = get_removable_accounts(prev_accounts.values(), accs)
    for name in removable_accs:
        delete_accounts(name, dry_run=dry_run)


def create_accounts(accs: List[Account], dry_run=False) -> None:
    acc_map = {acc.name: acc for acc in accs}
    sorted_acc_keys = topological_sort(acc_map)

    prev_accounts = get_existing_accounts()

    for name in sorted_acc_keys:
        if not name in prev_accounts:
            create_account(acc_map[name], dry_run=dry_run)

def modify_accounts(accs: List[Account], dry_run=False) -> None:
    acc_map = {acc.name: acc for acc in accs}
    sorted_acc_keys = topological_sort(acc_map)

    prev_accounts = get_existing_accounts()
    updatable_keys = get_overlapping_accounts(prev_accounts, acc_map)

    for name in updatable_keys:
        modify_account(acc_map[name], prev_accounts[name], dry_run=dry_run)
