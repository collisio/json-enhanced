# This module contains utilities to parse query arguments and transforms it to a conditional expression


def parse_query(child, **q):
    """We must determine whether the child passed as input argument matches the conditions given by the query q"""

    for k, v in q.items():
        splitted = k.split("__")
        target_key = splitted[0]
        if target_key != child.key:
            return False
        try:
            target_action = splitted[1]
        except IndexError:
            target_action = None
        else:
            try:
                target_action_extra = splitted[2]
            except IndexError:
                target_action_extra = None
        target_value = v
    return True


class QuerySet(list):
    pass