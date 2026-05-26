import logging
from dataclasses import dataclass, field
from typing import List, Tuple

# from groups import groups_to_users
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


def get_association_fields(exclude_fields=None) -> List[str]:
    if exclude_fields is None:
        exclude_fields = []
    field_keys = filter(
        lambda x: x not in exclude_fields, Association.__dataclass_fields__.keys()
    )
    return list(field_keys)
assoc_format = ",".join(Association.__dataclass_fields__.keys())


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
