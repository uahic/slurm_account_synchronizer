import logging
from typing import List
from account import (
    Account,
    get_account_fields,
)
from ..users.user import User

logger = logging.getLogger(__name__)


def accounts_from_config(config: dict) -> List[Account]:
    defaults = config["defaults"]
    cfg_accounts = config["accounts"]
    accounts = []
    for name, entry in cfg_accounts.items():
        entry["name"] = name
        acc = account_from_cfg_entry(entry, defaults)
        accounts.append(acc)
    return accounts


def account_from_cfg_entry(entry: dict, defaults: dict) -> Account:
    values = [
        entry.get(key) or defaults.get(key)
        for key in get_account_fields(exclude_fields=["name"])
    ]
    acc = Account(entry["name"].lower(), *values)
    return acc


def accounts_from_user_list(users: List[User], config: dict) -> None:
    defaults = config["defaults"]
    accounts = []
    values = [
        defaults.get(key)
        for key in get_account_fields(exclude_fields=["name", "description"])
    ]
    for usr in users:
        acc = Account(
            usr.user,
            f"User Account for {usr.user}",
            *values,
            # cluster=config["defaults"]["cluster"],
            # qos=config["defaults"]["qos"],
            # defaultqos=config["defaults"]["defaultqos"],
        )
        accounts.append(acc)
    return accounts


# def add_user_accounts(users: List[User], accounts: List[Account], config: dict) -> None:
#     for usr in users:
#         acc = Account(
#             usr.user,
#             f"User Account for {usr.user}",
#             cluster=config["defaults"]["cluster"],
#             qos=config["defaults"]["qos"],
#             defaultqos=config["defaults"]["defaultqos"],
#         )
#         accounts.append(acc)
