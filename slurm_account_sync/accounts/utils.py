import logging
import queue
from typing import List

logger = logging.getLogger(__name__)


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


def get_overlapping_accounts(existing_accs: dict, cfg_accs: dict) -> List[str]:
    existing_names = set(existing_accs.keys())
    return list(existing_names.intersection(cfg_accs.keys()))
