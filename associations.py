import logging
from dataclasses import dataclass, field
from typing import List, Tuple
from utils import execute_command
from groups import groups_to_users
from collections import defaultdict

logger = logging.getLogger(__name__)

DEFAULT_VALUES = {"fairshare": 1}


@dataclass()
class Association:
    user: str
    cluster: str
    account: str
    partition: str
    fairshare: str = None
    grpjobs: str = None
    grptres: str = None
    grpsubmit: str = None
    grpwall: str = None
    grptresmins: str = None
    maxjobs: str = None
    maxtres: str = None
    maxtrespernode: str = None
    maxsubmitjobs: str = None
    maxwall: str = None
    maxtresmins: str = None
    qos: str = None
    defaultqos: str = None
    grptresrunmins: str = None
    grpjobsaccrue: str = None
    maxjobsaccrue: str = None

    def get_hash(self) -> int:
        hash_val = hash(
            " ".join(
                map(
                    lambda x: str(getattr(self, x)),
                    ["cluster", "account", "user", "partition"],
                )
            )
        )
        return hash_val

    def __post_init__(self) -> None:
        # Convert everything except Nones to lowercase strings
        for k in Association.__dataclass_fields__.keys():
            if not getattr(self, k) is None:
                setattr(self, k, str(getattr(self, k)).lower())

        # Fill in default values if necessary
        for k, v in DEFAULT_VALUES.items():
            if not getattr(self, k) or getattr(self, k) == "":
                setattr(self, k, str(v))

    def get_settings(self) -> Tuple[str, str]:
        required_fields = ["cluster", "account", "user", "partition"]
        field_keys = filter(
            lambda x: x not in required_fields, self.__dataclass_fields__.keys()
        )
        field_keys = filter(lambda x: getattr(self, x) is not None, field_keys)
        return list(map(lambda key: (key, getattr(self, key)), field_keys))


def get_association_fields(exclude_fields=[]) -> List[str]:
    field_keys = filter(
        lambda x: x not in exclude_fields, Association.__dataclass_fields__.keys()
    )
    return list(field_keys)


groups: List[str] = field(default_factory=list)
assoc_format = ",".join(Association.__dataclass_fields__.keys())


def user_associations_from_config(
    config: dict, unix_group_map: dict
) -> List[Association]:
    defaults = config["defaults"]
    assoc_section = config["associations"]
    associations = []

    if assoc_section is None:
        return []

    for _, assoc_entry in assoc_section.items():
        groups = assoc_entry.get("groups") or []
        users = groups_to_users(groups, unix_group_map)
        values = [
            assoc_entry.get(key) or defaults.get(key)
            for key in get_association_fields(exclude_fields=["user"])
        ]
        for usr in users:
            assoc = Association(usr.lower(), *values)
            associations.append(assoc)
    return associations


def empty_str_to_none(arr: List) -> List:
    return [i or None for i in arr]


def get_existing_associations() -> List[Association]:
    cmd = f"$(which sacctmgr) -snorP show associations format={assoc_format}"
    records = execute_command(cmd, hide_log=True)
    assocs = map(lambda rec: Association(*empty_str_to_none(rec.split("|"))), records)
    assocs = filter(lambda assoc: assoc.user and assoc.user != "root", assocs)
    return list(assocs)


def get_with_defaults(obj: object, attr: str, default=""):
    if hasattr(obj, attr):
        return getattr(obj, attr)
    else:
        return default


def create_association(assoc: Association, dry_run=False) -> None:
    # A single user can be created in multiple account combinations
    cmd = f"$(which sacctmgr) -i add user {assoc.user} account={assoc.account}"
    if assoc.cluster:
        cmd += f" cluster={assoc.cluster}"
    if assoc.partition:
        cmd += f" partition={assoc.partition}"

    assoc_settings = assoc.get_settings()
    for t in assoc_settings:
        if getattr(assoc, t[0])!=None:
            cmd += f" {t[0]}={t[1]}"
    result = execute_command(cmd, dry_run=dry_run)


def delete_association(
    user: str, account: str, cluster=None, partition=None, dry_run=False
) -> None:
    cmd = f"$(which sacctmgr) -i delete user name={user} account={account}"
    if cluster:
        cmd += f" cluster={cluster}"
    if partition:
        cmd += f" partition={partition}"
    result = execute_command(cmd, dry_run=dry_run)


def modify_association(
    assoc: Association, prev_assoc: Association, dry_run=False
) -> None:
    assoc_settings = assoc.get_settings()
    # Check if we even have optional attributes != None
    if not assoc_settings:
        return
    cmd = f"$(which sacctmgr) -i modify user where name={assoc.user} account={assoc.account}"
    if assoc.cluster:
        cmd += f" cluster={assoc.cluster}"
    if assoc.partition:
        cmd += f" partition={assoc.partition}"
    cmd += f" set "

    diff_counter = 0
    for t in assoc_settings:
        if getattr(assoc, t[0]) != getattr(prev_assoc, t[0]):
            cmd += f" {t[0]}={t[1]}"
            diff_counter += 1
    if diff_counter > 0:
        result = execute_command(cmd, dry_run=dry_run)


def create_association_map(assocs: List[Association]) -> defaultdict:
    def multi_dict(K, type) -> dict:
        if K == 1:
            return defaultdict(type)
        else:
            return defaultdict(lambda: multi_dict(K - 1, type))

    assoc_map = multi_dict(4, str)
    for assoc in assocs:
        assoc_map[assoc.account][assoc.user][assoc.partition][assoc.cluster] = assoc
    return assoc_map


def check_illegal_association_overlaps(
    assocs: List[Association], association_map: dict
) -> None:
    for a in assocs:
        none_assoc = association_map[a.account][a.user]
        if a.partition is not None and None in none_assoc:
            raise Exception(
                f"Found conflict in association specifications. You cannot define [Account={a.account}, User={a.user}, Partition={a.partition}] and in another association the same Account/User combination without partition. Specifying no partition already means that all partitions are included."
            )


def create_associations(
    assocs: List[Association], prev_assocs: List[Association], dry_run=False
) -> None:
    prev_assoc_map = create_association_map(prev_assocs)

    for a in assocs:
        prev_acc_user_map = prev_assoc_map[a.account][a.user]
        prev_acc_user_partition = prev_acc_user_map[a.partition]
        # print(f"[{a.account}][{a.user}][{a.partition}][{a.cluster}]")
        # print(prev_acc_user_partition)
        if len(prev_acc_user_partition) < 1 and not prev_acc_user_map[None]:
            create_association(a, dry_run=dry_run)


def update_and_delete_associations(
    assocs: List[Association], prev_assocs: List[Association], dry_run=False
) -> None:
    # Index: [account, user, partition, cluster]
    cur_assoc_map = create_association_map(assocs)
    prev_assoc_map = create_association_map(prev_assocs)

    # For assocs: check if counterpart exists in prev_assocs, then either update or create them.
    for a in assocs:
        prev_acc_user_p = prev_assoc_map[a.account][a.user]

        if a.partition in prev_acc_user_p and a.cluster in prev_acc_user_p[a.partition]:
            modify_association(
                a, prev_acc_user_p[a.partition][a.cluster], dry_run=dry_run
            )
        elif None in prev_acc_user_p:
            if cur_assoc_map[a.account][a.user][None][a.cluster]:
                raise Exception(
                    f"The account-user association [Account={a.account}, User={a.user}] has been specified without any partition-specification before. Now the requested partition={a.partition} is in conflict to that. You can't add the same user to an account with Check your .yml specification file."
                )
            else:
                # Remove general association
                delete_association(
                    a.user,
                    a.account,
                    partition=a.partition,
                    cluster=a.cluster,
                    dry_run=dry_run,
                )

    assoc_hashs = set()
    for a in assocs:
        assoc_hashs.add(a.get_hash())

    for a in prev_assocs:
        if a.user == a.account:
            continue
        if a.get_hash() not in assoc_hashs:  # association no longer present
            delete_association(
                a.user,
                a.account,
                partition=a.partition,
                cluster=a.cluster,
                dry_run=dry_run,
            )
