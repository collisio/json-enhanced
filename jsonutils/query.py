import re
import warnings
from datetime import date, datetime
from typing import Union

import jsonutils.base as base
import jsonutils.config as config
import jsonutils.functions.parsers as parsers
from jsonutils.exceptions import JSONQueryException
from jsonutils.utils.dict import ValuesDict


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

        if not isinstance(node, base.JSONNode):
            raise JSONQueryException(
                f"child argument must be JSONNode type, not {type(node)}"
            )
        # if child key does not match the target query key, returns False, because this is a single query
        if node._key != self.target_key:
            return False

        # grab a list of node actions, without the action suffix
        node_actions = [
            i.replace("_action", "") for i in dir(base.JSONNode) if i.endswith("action")
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


class ParentList(list):
    pass


class ValuesList(list):
    """
    Like a QuerySet, but only some methods.
    Attributes:
    ----------
        _root: the root json object from which the entire queryset is derived
    """

    def __init__(self, *args):
        super().__init__(*args)
        self._root = None

    def first(self):

        try:
            return self.__getitem__(0)
        except IndexError:
            return

    def last(self):
        try:
            return self.__getitem__(-1)
        except IndexError:
            return

    def exists(self):
        return True if self.__len__() > 0 else False

    def count(self):
        return self.__len__()

    def distinct(self):
        """
        Returns unique values
        """

        # TODO add test for this
        # TODO dict option for counting unique values
        unique_values = ValuesList()
        unique_values._root = self._root
        for item in self:
            if item not in unique_values:
                unique_values.append(item)
        return unique_values


class QuerySet(list):
    """
    This is a queryset object.
    Attributes:
    ----------
        _root: the root json object from which the entire queryset is derived
        _list_of_root_nodes: if this is a list of root nodes, coming from a parsed json instead of from a query
    """

    def __init__(self, *args, list_of_root_nodes=False):
        super().__init__(*args)
        self._root = None
        self._native_types = None
        self._list_of_root_nodes = list_of_root_nodes

    def first(self):

        try:
            result = self.__getitem__(0)
        except IndexError:
            return
        if not self._native_types:
            return result
        else:  # if native_types_ is selected
            return result._data

    def last(self):

        try:
            result = self.__getitem__(-1)
        except IndexError:
            return
        if not self._native_types:
            return result if self.__len__() > 0 else None
        else:  # if native_types_ is selected
            return result._data if self.__len__() > 0 else None

    def exists(self):
        return True if self.__len__() > 0 else False

    def count(self):
        return self.__len__()

    def delete(self):
        if self._list_of_root_nodes:
            return
        deleted_objects = 0
        for item in self:
            path = item.parent.jsonpath.relative_to(self._root)
            try:
                exec(f"self._root{path}.pop(item._key)")
            except Exception:
                continue
            else:
                deleted_objects += 1
        return deleted_objects

    def update(self, new_obj):
        """
        Update elements of queryset (inplace) within JSONObject from which they are derived (self._root)
        """
        if self._list_of_root_nodes:
            return  # TODO if list of root nodes, call each node's query

        # TODO add test for update when callables
        is_callable = callable(new_obj)

        updated_objects = 0
        not_updated_objects = 0

        for item in self:
            path = item.jsonpath.relative_to(self._root)
            if is_callable:
                try:
                    exec(f"self._root{path} = new_obj(self._root{path})")
                except Exception:
                    not_updated_objects += 1
                else:
                    updated_objects += 1
            else:
                exec(f"self._root{path} = new_obj")
                updated_objects += 1

        return (updated_objects, not_updated_objects)

    def update_ifnonnull(self, new_obj):
        """
        Update elements of queryset (inplace) within JSONObject from which they are derived (self._root),
        only if new_obj is non null
        """
        if self._list_of_root_nodes:
            return  # TODO if list of root nodes, call each node's query

        # TODO add test for update when callables
        is_callable = callable(new_obj)

        updated_objects = 0
        not_updated_objects = 0

        for item in self:
            path = item.jsonpath.relative_to(self._root)
            if is_callable:
                try:
                    updated_value = new_obj(
                        self._root._eval_path(path, fail_silently=True)
                    )
                    if not updated_value and updated_value != 0:
                        raise Exception
                    exec(f"self._root{path} = updated_value")
                except Exception:
                    not_updated_objects += 1
                else:
                    updated_objects += 1
            else:
                try:
                    if not new_obj and new_obj != 0:
                        raise Exception
                    exec(f"self._root{path} = new_obj")
                except Exception:
                    not_updated_objects += 1
                else:
                    updated_objects += 1

        return (updated_objects, not_updated_objects)

    def distinct(self, transform=None):
        """
        Returns unique values in a querylist
        Arguments:
        ---------
            transform: if selected, then applies such a function on each item in the queryset before checking
        """
        cls = self.__class__

        # TODO add test for this
        # TODO dict option for counting unique values
        unique_values = cls()
        unique_values._root = self._root
        unique_values._native_types = self._native_types

        transformed_values = set()

        if transform is None:
            for item in self:
                if item not in unique_values:
                    unique_values.append(item)
            return unique_values
        else:
            for item in self:
                obj = item
                try:
                    obj = transform(item)
                except Exception:
                    pass
                if obj not in transformed_values:
                    transformed_values.add(obj)
                    unique_values.append(item)
            return unique_values

    def filter(self, **q):
        # TODO add test

        cls = self.__class__

        output = cls()
        output._root = self._root
        output._native_types = self._native_types

        if (
            self._list_of_root_nodes
        ):  # If we are dealing with a list of root nodes, we must call the query function of each of them
            for item in self:
                if item.query(**q).exists():
                    output.append(item)
            return output
        else:
            for item in self:
                if item.parent.query(**q).exists():
                    output.append(item)
            return output

    def filter_key(self, pattern, **q):
        # TODO add test

        cls = self.__class__

        output = cls()
        output._root = self._root
        output._native_types = self._native_types

        if (
            self._list_of_root_nodes
        ):  # If we are dealing with a list of root nodes, we must call the query function of each of them
            for item in self:
                if item.query_key(pattern, **q).exists():
                    output.append(item)
            return output
        else:
            for item in self:
                if item.parent.query_key(pattern, **q).exists():
                    output.append(item)
            return output

    def values(self, *keys, search_upwards=True, flat=False, **kwargs):
        """
        This method changes the values returned by the queryset.
        The returned values will be python types.

        Arguments
        ---------
            search_upwards: The function will try to search for the specified keys among the parents of each object

        """

        if self._list_of_root_nodes:
            return

        values_list = ValuesList(
            (
                item.values(*keys, search_upwards=search_upwards, flat=flat, **kwargs)
                for item in self
            )
        )
        values_list._root = self._root
        if not values_list:
            output_dict = ValuesDict({k: None for k in keys})

            if kwargs:
                output_dict.update({k: None for k in kwargs})
            values_list.append(output_dict)
        return values_list

    def jsonpaths(self):
        """
        Returns a ValuesList with the jsonpath of each node
        """

        output = ValuesList()
        output._root = self._root

        for item in self:
            output.append(item.jsonpath)

        return output

    def order_by(self, key):
        # TODO
        if self._list_of_root_nodes:
            return
        rever = True if key.startswith("-") else False

        cls = self.__class__

        try:
            result = cls(
                sorted(
                    self,
                    key=lambda x: x.parent._get(key.replace("-", "").strip(), ""),
                    reverse=rever,
                )
            )
        except Exception as e:
            warnings.warn(f"QuerySet could not be sorted. Info: {e}")
            # print(e)
            return self

        result._root = self._root
        result._native_types = self._native_types
        return result

    # ---- GROUP OPERATIONS ----
    def sum(self):
        """Sum numbers on queryset"""

        if self._list_of_root_nodes:
            return

        if not self.exists():
            return

        result = 0
        for item in self:
            number = parsers.parse_float(item, fail_silently=True) or 0
            result += number
        return result

    def __repr__(self):
        clsname = self.__class__.__name__
        return f"<{clsname} " + super().__repr__() + ">"


class KeyQuerySet(QuerySet):
    """
    This is a QuerySet, with all its methods, but adding more useful ones for querying keys.
    """

    def keys(self):
        result = ValuesList()
        result._root = self._root
        result._native_types = self._native_types

        for item in self:
            result.append(item._key)

        return result


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


class ExtractYear:
    # TODO add more actions
    def __init__(self, data):
        self.data = parsers.parse_datetime(data, fail_silently=True)
        self.year = self.data.year if self.data else None

    def exact_action(self, query_value):
        if query_value == All:
            return True

        if not isinstance(query_value, int):
            raise JSONQueryException(
                f"Argument query_value must be an int, not {type(query_value)}"
            )

        return self.year == query_value

    def contains_action(self, query_value):
        if not isinstance(query_value, int):
            raise JSONQueryException(
                f"Argument query_value must be an int, not {type(query_value)}"
            )
        if self.data:
            return str(query_value) in str(self.year)
        else:
            return False


class Length:
    def __init__(self, data):
        self.data = data


class I:
    """Ignore case Object wrapper, for using in query_key method instead of re.compile the pattern with re.I flag"""

    def __init__(self, pattern):
        if not isinstance(pattern, str):
            raise TypeError(
                f"Argument pattern must be an str instance, not {type(pattern)}"
            )
        self.data = re.compile(pattern, re.I)
