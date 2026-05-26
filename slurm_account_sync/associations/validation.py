from typing import List
from .association import Association


def check_illegal_association_overlaps(
    assocs: List[Association], association_map: dict
) -> None:
    for a in assocs:
        none_assoc = association_map[a.account][a.user]
        if a.partition is not None and None in none_assoc:
            raise Exception(
                f"Found conflict in association specifications. You cannot define [Account={a.account}, User={a.user}, Partition={a.partition}] and in another association the same Account/User combination without partition. Specifying no partition already means that all partitions are included."
            )
