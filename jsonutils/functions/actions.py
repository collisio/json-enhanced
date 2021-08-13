"""
We define here the interactions between a query and a particular node.
Nodes can be of the following types:
    JSONList, JSONDict, JSONStr, JSONBool, JSONInt, JSONFloat, JSONNull
whereas query target values can be:
    list/tuple, dict, str, date/datetime, bool, int/float, null

So we have up to 49 checks for each action:
============================
  NODE     |    QUERY_VALUE
============================
JSONList -----> list/tuple
         -----> dict
         -----> str
         -----> date/datetime
         -----> bool
         -----> float/int 
         -----> null

JSONDict -----> list/tuple
         -----> dict
         -----> str
         -----> date/datetime
         -----> bool
         -----> float/int
         -----> null
    .
    .
    .
"""

import re
from datetime import date, datetime

import pytz
from jsonutils.base import (
    JSONBool,
    JSONCompose,
    JSONDict,
    JSONFloat,
    JSONInt,
    JSONList,
    JSONNull,
    JSONSingleton,
    JSONStr,
)
from jsonutils.exceptions import JSONQueryException
from jsonutils.functions.parsers import parse_datetime, parse_float
from jsonutils.query import All


def _gt(node, requested_value):
    """
    Greather than action

           \ req_value  |  dict  |  list/tuple  |  bool  |  float/int  |  str  |  datetime  |  null
      node  \           |        |              |        |             |       |            |
    ================================================================================================
           JSONDict     |    X   |       X      |    X   |      X      |   X   |     X      |   X
                        |        |              |        |             |       |            |
           JSONList     |    X   |       V      |    X   |      X      |   X   |     X      |   X
                        |        |              |        |             |       |            |
           JSONStr      |    X   |       X      |    X   |      V      |   V   |     V      |   X
                        |        |              |        |             |       |            |
           JSONBool     |    X   |       X      |    X   |      X      |   X   |     X      |   X
                        |        |              |        |             |       |            |
           JSONInt      |    X   |       X      |    X   |      V      |   V   |     X      |   X
                        |        |              |        |             |       |            |
           JSONFloat    |    X   |       X      |    X   |      V      |   V   |     X      |   X
                        |        |              |        |             |       |            |
           JSONNull     |    X   |       X      |    X   |      X      |   X   |     X      |   X
    """

    if isinstance(node, JSONList):
        if isinstance(requested_value, (list, tuple)):
            requested_value = list(requested_value)

            len_node = len(node)
            len_requ = len(requested_value)
            length = min((len_node, len_requ))
            success_number = 0
            control_success = False
            for i in range(length):
                if node[i] > requested_value[i]:
                    success_number += 1
                    control_success = True
            if success_number == length and control_success:
                return True
            else:
                return False
    elif isinstance(node, JSONDict):
        return False
    elif isinstance(node, JSONSingleton):
        # if dealing with singletons, call its rich comparison methods
        return node > requested_value


def _gte(node, requested_value):
    """
    Greather-equal than action. Matches are the same as _gt action
    """
    if isinstance(node, JSONList):
        if isinstance(requested_value, (list, tuple)):
            requested_value = list(requested_value)

            len_node = len(node)
            len_requ = len(requested_value)
            length = min((len_node, len_requ))
            success_number = 0
            control_success = False
            for i in range(length):
                if node[i] >= requested_value[i]:
                    success_number += 1
                    control_success = True
            if success_number == length and control_success:
                return True
            else:
                return False
    elif isinstance(node, JSONDict):
        return False
    elif isinstance(node, JSONSingleton):
        # if dealing with singletons, call its rich comparison methods
        return node >= requested_value


def _lt(node, requested_value):
    """
    Lower than action. Matches are the same as _gt action
    """
    if isinstance(node, JSONList):
        if isinstance(requested_value, (list, tuple)):
            requested_value = list(requested_value)

            len_node = len(node)
            len_requ = len(requested_value)
            length = min((len_node, len_requ))
            success_number = 0
            control_success = False
            for i in range(length):
                if node[i] < requested_value[i]:
                    success_number += 1
                    control_success = True
            if success_number == length and control_success:
                return True
            else:
                return False
    elif isinstance(node, JSONDict):
        return False
    elif isinstance(node, JSONSingleton):
        # if dealing with singletons, call its rich comparison methods
        return node < requested_value


def _lte(node, requested_value):
    """
    Lower-equal than action. Matches are the same as _gt action
    """
    if isinstance(node, JSONList):
        if isinstance(requested_value, (list, tuple)):
            requested_value = list(requested_value)

            len_node = len(node)
            len_requ = len(requested_value)
            length = min((len_node, len_requ))
            success_number = 0
            control_success = False
            for i in range(length):
                if node[i] <= requested_value[i]:
                    success_number += 1
                    control_success = True
            if success_number == length and control_success:
                return True
            else:
                return False
    elif isinstance(node, JSONDict):
        return False
    elif isinstance(node, JSONSingleton):
        # if dealing with singletons, call its rich comparison methods
        return node <= requested_value


def _exact(node, requested_value):
    """
    An exact match.
    In an exact match, only same types are checked, except for JSONStr, which is more versatile.

           \ req_value  |  dict  |  list/tuple  |  bool  |  float/int  |  str  |  datetime  |  null
      node  \           |        |              |        |             |       |            |
    ================================================================================================
           JSONDict     |    V   |       X      |    X   |      X      |   X   |     X      |   X
                        |        |              |        |             |       |            |
           JSONList     |    X   |       V      |    X   |      X      |   X   |     X      |   X
                        |        |              |        |             |       |            |
           JSONStr      |    X   |       X      |    V   |      V      |   V   |     V      |   X
                        |        |              |        |             |       |            |
           JSONBool     |    X   |       X      |    V   |      X      |   V   |     X      |   X
                        |        |              |        |             |       |            |
           JSONInt      |    X   |       X      |    X   |      V      |   V   |     X      |   X
                        |        |              |        |             |       |            |
           JSONFloat    |    X   |       X      |    X   |      V      |   V   |     X      |   X
                        |        |              |        |             |       |            |
           JSONNull     |    X   |       X      |    X   |      X      |   X   |     X      |   V
    """

    if requested_value == All:
        return True

    if isinstance(node, JSONDict):
        if isinstance(requested_value, dict):
            return node == requested_value
        else:
            return False
    elif isinstance(node, JSONList):
        if isinstance(requested_value, (list, tuple)):
            return node == list(requested_value)
        else:
            return False
    elif isinstance(node, JSONSingleton):
        return node == requested_value
    else:
        return False


def _contains(node, requested_value):
    """
    This method analyzes whether a given JSONObject contains the object specified by the <other> parameter, and returns a boolean.
    <self> will be the current child instance within the JSONObject, whereas <other> will be the current query target value.
    Examples in a query method:
    --------------------------
    >> obj = JSONObject(
        {
            "data": {
                "cik": "0008547852",
                "country": "USA",
                "live": False
            },
            "team": [
                "Daniel",
                "Alex",
                "Catherine",
                None
            ]
        }
    )

    >> obj.query(data__contains="cik")  # in this case the "cik" string object will play the role of <other> (the target query value).
                                        # On the other hand, <self> in this case will take the value of the "data" dictionary (JSONDict)
        [{'cik': '0008547852', 'country': 'USA', 'live': False}]

    >> obj.query(cik__contains=85) # now the 85 integer object will be <other> object, whereas <self> will be the "cik" string object.
        ['0008547852']

    >> obj.query(team__contains=["Alex", "Daniel"]) # in this case target JSONObject must contains both "Alex" and "Daniel" strings
        [['Daniel', 'Alex', 'Catherine', None]]

    >> obj.query(team__contains=None).first()
        ['Daniel', 'Alex', 'Catherine', None]
    """

    # TODO implement clever parsing
    if isinstance(node, JSONStr):
        # if target object is an string, contains will return True if target value/s are present within it.
        if isinstance(requested_value, str):
            return requested_value in node
        elif isinstance(requested_value, (float, int)):
            # if target value is a number, we convert it first to a string and then check if it is present within self
            return str(requested_value) in node
        elif isinstance(requested_value, (list, tuple)):
            # if target value is a list, then check if all its items are present in self string
            return all(str(x) in node for x in requested_value)
    elif isinstance(node, JSONDict):
        # if target object is a dict, contains will return True if target value/s are present within its keys.
        if isinstance(requested_value, str):
            return requested_value in node.keys()
        elif isinstance(requested_value, (list, tuple)):
            return all(x in node.keys() for x in requested_value)
    elif isinstance(node, JSONList):
        # if target object is a list, contains will return True if target value are present within its elements.
        if isinstance(requested_value, (list, tuple)):
            return all(x in node for x in requested_value)
        else:
            return True if requested_value in node else False
    elif isinstance(node, JSONBool):
        if isinstance(requested_value, bool):
            return node._data == requested_value
    elif isinstance(node, JSONNull):
        if isinstance(requested_value, type(None)):
            return node._data == requested_value
    elif isinstance(node, (JSONFloat, JSONInt)):
        if isinstance(requested_value, (int, float, str)):
            return str(requested_value) in str(node)
    return False


def _icontains(node, requested_value):
    """
    Case insensitive version of contains
    """

    # TODO implement clever parsing
    # TODO if self is a number and other too
    if isinstance(node, JSONStr):
        # if target object is an string, contains will return True if target value/s are present within it.
        if isinstance(requested_value, str):
            return requested_value.lower() in node.lower()
        elif isinstance(requested_value, (float, int)):
            # if target value is a number, we convert it first to a string and then check if it is present within self
            return str(requested_value) in node
        elif isinstance(requested_value, (list, tuple)):
            # if target value is a list, then check if all its items are present in self string
            try:
                return all(str(x).lower() in node.lower() for x in requested_value)
            except Exception:  # maybe if x has a unknown type # TODO possible conflict if x is an object and its str representation matches node
                return False
    elif isinstance(node, JSONDict):
        # if target object is a dict, contains will return True if target value/s are present within its keys.
        if isinstance(requested_value, str):
            try:
                return requested_value.lower() in map(str.lower, node.keys())
            except Exception:  # maybe JSONDict has integer keys. TODO handle this
                return False
        elif isinstance(requested_value, (list, tuple)):
            try:
                return all(
                    str(x).lower() in map(str.lower, node.keys())
                    for x in requested_value
                )
            except Exception:
                return False
    elif isinstance(node, JSONList):
        # if target object is a list, contains will return True if target value are present within its elements.
        # TODO modify this, must compare lower strings and ignore other objects
        if isinstance(requested_value, (list, tuple)):
            return all(x in node for x in requested_value)
        else:
            return True if requested_value in node else False
    elif isinstance(node, JSONBool):
        if isinstance(requested_value, bool):
            return node._data == requested_value
    elif isinstance(node, JSONNull):
        if isinstance(requested_value, type(None)):
            return node._data == requested_value
    return False


def _in(node, requested_value):
    # TODO complete in child method
    """
    This method, as opposed to "contains", analyzes whether a given JSONObject is contained in the iterable object specified
    by the <other> parameter
    """

    if isinstance(node, (JSONSingleton)):
        # <self> might be JSONStr, JSONFloat, JSONInt, JSONBool or JSONNull.
        if isinstance(requested_value, (str, list, tuple, dict)):
            return node in requested_value
    elif isinstance(node, JSONList):
        if isinstance(requested_value, (list, tuple)):
            return all(x in requested_value for x in node)
    elif isinstance(node, JSONDict):
        if isinstance(requested_value, (list, tuple)):
            return all(x in requested_value for x in node.keys())
    return False


def _regex(node, requested_value):
    """
    This method analyzes whether a given JSONObject matchs with target regex pattern specified by <other>.
    """

    if isinstance(node, JSONStr):
        if isinstance(requested_value, (str, re.Pattern)):
            return bool(re.search(requested_value, node))
    elif isinstance(node, (JSONInt, JSONFloat)):
        if isinstance(requested_value, (str, re.Pattern)):
            return bool(re.search(requested_value, str(node)))
    return False


def _fullregex(node, requested_value):
    """
    This method analyzes whether a given JSONObject full matchs with target regex pattern specified by <other>.
    """
    if isinstance(node, JSONStr):
        if isinstance(requested_value, (str, re.Pattern)):
            return bool(re.fullmatch(requested_value, node))
    elif isinstance(node, (JSONInt, JSONFloat)):
        if isinstance(requested_value, (str, re.Pattern)):
            return bool(re.fullmatch(requested_value, str(node)))
    return False


def _isnull(node, requested_value):
    """
    This method analyzes whether a given JSONObject is null.
    """
    if not isinstance(requested_value, bool):
        raise JSONQueryException(
            f"Requested value must be a boolean, not {type(requested_value)}"
        )
    return bool(node) != requested_value if node != 0 else False


def _length(node, requested_value):
    """
    This method analyzes whether a given JSONObject has requested length.
    """
    if not isinstance(requested_value, int):
        raise JSONQueryException(
            f"Requested value must be an int, not {type(requested_value)}"
        )
    if isinstance(node, (JSONCompose, JSONStr)):
        return node.__len__() == requested_value
    elif isinstance(node, JSONInt):
        return str(node).__len__() == requested_value
    else:
        return False


def _type(node, requested_value):
    """
    This method analyzes whether a given JSONObject has requested type.
    """
    if requested_value not in (
        dict,
        list,
        str,
        datetime,
        float,
        int,
        bool,
        None,
        "dict",
        "list",
        "str",
        "datetime",
        "float",
        "int",
        "bool",
        "None",
    ):
        raise JSONQueryException(
            f"Requested value must be a valid type, not {requested_value}"
        )

    if requested_value in (None, "None"):
        requested_value = type(None)

    if isinstance(node, JSONBool):
        if requested_value in (bool, "bool"):
            return True
        else:
            return False
    elif isinstance(node, JSONNull):
        if requested_value in (None, "None"):
            return True
        else:
            return False
    else:
        return isinstance(node, requested_value)
