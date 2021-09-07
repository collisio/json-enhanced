import re
from datetime import date, datetime
from typing import Union

from jsonutils.exceptions import JSONQueryException


class SingleQuery:
    """
    This class represents a single query object.
    It consists of a single key and a collection of actions that operate on that key.

    Arguments:
    ---------
        query_key: key part of the query. Must be an string
        query_value: target value of the query
    """

    def __init__(
        self,
        query_key: str,
        query_value: Union[float, int, str, None, bool, dict, list, tuple, datetime],
    ):

        if not isinstance(
            query_value,
            (
                type,
                float,
                int,
                str,
                type(None),
                bool,
                dict,
                list,
                tuple,
                date,
                datetime,
                AllChoices,
            ),
        ):
            raise JSONQueryException(
                f"Target value of query has invalid type: {type(query_value)}. Valid types are: float, int, str, None, bool, dict, list, tuple, date, datetime, allchoices"
            )

        self.target_value = query_value
        self._parse_key(query_key)

    def _parse_key(self, query_key):
        """Convert query full key in a list of actions"""

        splitted_query = [i for i in query_key.split("__") if i]

        if not splitted_query:
            raise JSONQueryException("Bad query. Missing target key")

        self.target_key = splitted_query[0]
        self.target_actions = splitted_query[1:] or ["exact"]

    def _check_against_node(self, node):
        """
        Check this single query against a target node object.
        node argument must be an instance of JSONNode.
        """
        from jsonutils.base import JSONNode

        if not isinstance(node, JSONNode):
            raise JSONQueryException(
                f"child argument must be JSONNode type, not {type(node)}"
            )
        # if child key does not match the target query key, returns False, because this is a single query
        if node._key != self.target_key:
            return False

        # grab a list of node actions, without the action suffix
        node_actions = [
            i.replace("_action", "") for i in dir(JSONNode) if i.endswith("action")
        ]
        obj = node

        actions_count = len(self.target_actions)
        for idx, action in enumerate(self.target_actions):

            # ---- MODIFICATORS ----
            if action == "parent":
                obj = obj.parent
                if obj is None:
                    return False
                if idx == actions_count - 1:
                    action = "exact"  # if parent is last action, take exact as the default one
                else:
                    continue  # continue to next action
            elif match := re.fullmatch(r"c_(\w+)", action):  # child modificator
                try:
                    obj = obj.__getitem__(match.group(1))
                except Exception:
                    return False
                if idx == actions_count - 1:
                    action = "exact"  # if child is last action, take exact as the default one
                else:
                    continue  # continue to next action
            elif action.isdigit():
                if not isinstance(obj, list):
                    return False
                try:
                    obj = obj[int(action)]
                except IndexError:
                    return False
                if idx == actions_count - 1:
                    action = "exact"  # if digit is last action, take exact as the default one
                else:
                    continue  # continue to next action

            # ---- ACTIONS ----
            # node actions can't interfer with modificators
            if action in node_actions:  # call corresponding node method
                return getattr(obj, action + "_action")(self.target_value)
            else:
                raise JSONQueryException(f"Bad query: {action}")


class Q:
    """
    A Query object. We can join different queries by means of bitand and bitor operators (& |)
    Examples
    --------
    >> obj = JSONObject(
        [
            {
                "timestamp": "2021-05-01 09:00:00",
                "value": [0.5, 0.87]
            },
            {
                "timestamp": "2021-04-02 10:30:00",
                "value": [-0.23, 1]
            },
            {
                "timestamp": "2021-06-01 08:25:30",
                "value": [0.9, 0.15]
            }
        ]
    )

    >> obj.query(Q(timestamp__gt="2021-05-01 10:00:00") | Q(value__0__gte=0.5))
        [{"timestamp": "2021-05-01 09:00:00","value": [0.5, 0.87]},{"timestamp": 2021-06-01 08:25:30, "value": [0.9, 0.15]}]
    """

    # TODO make Q object
    def __init__(self, **kwargs):

        self.AND = []
        self.OR = []
        self.NOT = []

        if len(kwargs) > 0:
            self._parse_args(kwargs)

    def _parse_args(self, kwargs):
        for k, v in kwargs.items():

            splitted = *k.split("__"), v
            self.AND.append(splitted)

    def __and__(self, other):

        if not isinstance(other, Q):
            raise TypeError(f"Cannot add instances of {type(self)} and {type(other)}")

        obj = Q()
        obj.AND = self.AND + other.AND
        return obj

    def __or__(self, other):

        if not isinstance(other, Q):
            raise TypeError(f"Cannot add instances of {type(self)} and {type(other)}")

        obj = Q()
        obj.OR = self.OR + other.OR
        return obj


class QuerySet(list):
    """
    This is a queryset object.
    Attributes:
    ----------
        _root: the root json object from which the entire queryset is derived
    """

    def __init__(self, *args):
        super().__init__(*args)
        self._root = None

    def first(self):
        return self.__getitem__(0) if self.__len__() > 0 else None

    def last(self):
        return self.__getitem__(-1) if self.__len__() > 0 else None

    def exists(self):
        return True if self.__len__() > 0 else False

    def count(self):
        return self.__len__()

    def update(self, new_obj):
        """
        Update elements of queryset within JSONObject from which they are derived (self._root)
        """

        # TODO add test for update when callables
        is_callable = callable(new_obj)

        for item in self:
            path = item.jsonpath.relative_to(self._root)
            if is_callable:
                try:
                    exec(f"self._root{path} = new_obj(self._root{path})")
                except Exception:
                    pass
            else:
                exec(f"self._root{path} = new_obj")

    def unique(self):
        """
        Returns unique values in a querylist
        """
        from jsonutils.base import JSONSingleton

        # TODO add test for this
        # TODO dict option for counting unique values
        unique_values = QuerySet()
        unique_values._root = self._root
        for idx, item in enumerate(self):
            if item not in unique_values:
                unique_values.append(item)
        return unique_values

    def filter(self, **q):
        # TODO add test
        output = QuerySet()
        output._root = self._root
        for item in self:
            if item.query(**q).exists():
                output.append(item)
        return output

    def __repr__(self):
        return "<QuerySet " + super().__repr__() + ">"


class AllChoices(type):
    pass


class All(metaclass=AllChoices):
    """
    When we request this object as a target query value, we retrieve all objects of given key

    Examples:
    --------

    >> test = JSONObject(
        {
            "A": [
                {
                    "A": 1,
                    "B": 2
                },
                {
                    "A": 2,
                    "B": 3
                }
            ]
        }
    )

    >> test.query(A=All)
        [[{"A": 1, "B": 2},{"A": 2, "B": 3}], 1, 2]
    """

    pass
