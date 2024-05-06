from typing import List


def empty_str_to_none(arr: List) -> List:
    return [i or None for i in arr]

