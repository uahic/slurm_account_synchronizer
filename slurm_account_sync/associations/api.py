import logging
import utils
from typing import List
from shell import execute_command
from association import Association, assoc_format, create_association_map

logger = logging.getLogger(__name__)


def get_existing_associations() -> List[Association]:
    cmd = f"$(which sacctmgr) -snorP show associations format={assoc_format}"
    records = execute_command(cmd, hide_log=True)
    assocs = map(
        lambda rec: Association(*utils.empty_str_to_none(rec.split("|"))), records
    )
    assocs = filter(lambda assoc: assoc.user and assoc.user != "root", assocs)
    return list(assocs)


def create_association(assoc: Association, dry_run=False) -> None:
    # A single user can be created in multiple account combinations
    cmd = f"$(which sacctmgr) -i add user {assoc.user} account={assoc.account}"
    if assoc.cluster:
        cmd += f" cluster={assoc.cluster}"
    if assoc.partition:
        cmd += f" partition={assoc.partition}"

    assoc_settings = assoc.get_settings()
    for t in assoc_settings:
        if getattr(assoc, t[0]) != None:
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
