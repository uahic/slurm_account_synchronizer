import logging
from dataclasses import dataclass
from typing import List, Tuple

logger = logging.getLogger(__name__)

RESET_VALUES = {"parent": "root", "qos": "", "organization": ""}
DEFAULT_VALUES = {"parent": "root", "fairshare": 1}


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

    def get_fields(self, exclude_fields=None) -> Tuple[str, str]:
        if exclude_fields is None:
            exclude_fields = []
        field_keys = filter(
            lambda x: x not in exclude_fields, self.__dataclass_fields__.keys()
        )
        field_keys = filter(lambda x: getattr(self, x) is not None, field_keys)
        return list(map(lambda key: (key, getattr(self, key)), field_keys))

    def get_difference(self, other: object) -> List[Tuple[str, str]]:
        diff_arr = []
        field_keys = get_account_fields(exclude_fields=["name", "cluster"])
        for key in field_keys:
            value = getattr(self, key)
            if value is None:
                continue  # not specified in config — leave existing value as-is
            other_value = getattr(other, key)
            if value != (other_value or ""):
                diff_arr.append((key, other_value, value))
        return diff_arr


def get_account_fields(exclude_fields=None) -> List[str]:
    if exclude_fields is None:
        exclude_fields = []
    field_keys = filter(
        lambda x: x not in exclude_fields, Account.__dataclass_fields__.keys()
    )
    return list(field_keys)
