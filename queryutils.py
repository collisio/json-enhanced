# This module contains utilities to parse query arguments and transforms it to a conditional expression
import re

from config.locals import DECIMAL_SEPARATOR, THOUSANDS_SEPARATOR
from exceptions import JSONQueryException, JSONSingletonException


def parse_query(child, **q):
    """
    We must determine whether the child passed as input argument matches the conditions given by the query q.
    If required actions don't match the child type, it won't throw any exception, just return False for such an object.
    """

    for k, v in q.items():
        splitted = k.split("__")
        target_key = splitted[0]
        if not target_key:
            raise JSONQueryException("Bad query")
        # first of all, if target key of query argument does not match child's key, we won't append it to querylist
        if target_key != child.key:
            return False
        try:
            target_action = splitted[1]
        except IndexError:  # default action will be exact value match
            target_action = "exact"
        else:
            try:
                target_action_extra = splitted[2]
            except IndexError:
                target_action_extra = None
        target_value = v

        # ---- MATCH ----
        if target_action == "exact":
            # child value must match with target value of query
            # TODO
            if child != target_value:
                return False

    return True  # if match has not failed, current child will be appended to queryset


def parse_float(s, decimal_sep=DECIMAL_SEPARATOR, thousands_sep=THOUSANDS_SEPARATOR):
    if decimal_sep == thousands_sep:
        raise JSONSingletonException("Decimal and Thousands separators cannot be equal")
    if isinstance(s, str):
        pipe = re.sub(r"[^0-9\s,.+-]", "", s)
        pipe = re.sub(r"(?<=[+-])\s+", "", pipe)
        pipe = pipe.replace(thousands_sep, "").replace(decimal_sep, ".")
    else:
        return float(s)
    return float(pipe)


class QuerySet(list):
    pass
