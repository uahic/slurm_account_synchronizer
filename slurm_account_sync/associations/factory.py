import logging
from dataclasses import dataclass, field
from typing import List, Tuple
from shell import execute_command
from ..unix_groups.utils import groups_to_users

# from groups import groups_to_users
from collections import defaultdict

logger = logging.getLogger(__name__)


from association import (
    Association,
    get_association_fields,
)


def get_user_associations_from_config(
    config: dict, unix_groups: dict
) -> List[Association]:
    defaults = config["defaults"]
    assoc_section = config["associations"]
    associations = []

    if assoc_section is None:
        return []

    for _, assoc_entry in assoc_section.items():
        groups = assoc_entry.get("groups") or []
        users = groups_to_users(groups, unix_groups)
        users.extend(assoc_entry.get("extra_users") or [])
        values = [
            assoc_entry.get(key) or defaults.get(key)
            for key in get_association_fields(exclude_fields=["user"])
        ]
        for usr in users:
            assoc = Association(usr.lower(), *values)
            associations.append(assoc)
    return associations
