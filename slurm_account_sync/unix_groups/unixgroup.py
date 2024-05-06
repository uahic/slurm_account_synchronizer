import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UnixGroup:
    name: str
    gid: int  # -1 means 'virtual group'
    users: List[str] = field(default_factory=list)

    def has_user(self, name: str) -> bool:
        return name in self.users

