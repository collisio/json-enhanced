# This module contains the base objects needed
import ast
import json
import os
import re
from datetime import date, datetime
from uuid import uuid4

import requests

import jsonutils.config as config
from jsonutils.encoders import JSONObjectEncoder
from jsonutils.exceptions import JSONDecodeException
from jsonutils.functions.parsers import (
    _parse_query,
    parse_bool,
    parse_datetime,
    parse_float,
    url_validator,
)
from jsonutils.query import QuerySet
from jsonutils.utils.dict import UUIDdict
from jsonutils.utils.retry import retry_function


class JSONPath:
    """
    Object representing a JSON path for a given JSON object.
    Don't instanciate it directly.
    """

    def __new__(cls, s=""):
        obj = super().__new__(cls)
        obj._string = s  # pretty path
        obj._path = ""  # python json path
        return obj

    @property
    def data(self):
        return self._string

    @property
    def expr(self):
        return self._path

    def relative_to(self, child):
        """Calculate jsonpath relative to child's jsonpath"""
        # TODO review this algorithm, because it fails when a key has /

        if not isinstance(child, JSONNode):
            raise TypeError(
                f"child argument must be a JSONNode instance, not {type(child)}"
            )
        if child.jsonpath._path:
            root = child.jsonpath._path
        else:
            root = ""
        full_path = self._path

        common_prefix = os.path.commonprefix([root, full_path])

        return full_path.replace(common_prefix, "")

    def _update(self, **kwargs):
        if (key := kwargs.get("key")) is not None:
            self._string = str(key) + "/" + self._string
            self._path = f'["{key}"]' + self._path
        elif (index := kwargs.get("index")) is not None:
            self._string = str(index) + "/" + self._string
            self._path = f"[{index}]" + self._path

    def __eq__(self, other):
        return (self._string == other) or (self._path == other)

    def __repr__(self):
        return self._string


class JSONObject:
    """
    This class acts as a switcher. It will return the corresponding object instance for a given data.
    This class does not contain any instances of.
    """

    def __new__(cls, data=None, raise_exception=False):
        if not isinstance(raise_exception, bool):
            raise TypeError(
                f"raise_exception argument must be a boolean, not {type(raise_exception)}"
            )
        if isinstance(data, JSONNode):
            return data
        elif isinstance(data, dict):
            return JSONDict(data)
        elif isinstance(data, (list, tuple)):
            return JSONList(data)
        elif isinstance(data, bool):
            return JSONBool(data)
        elif isinstance(data, type(None)):
            return JSONNull(data)
        elif isinstance(data, str):
            return JSONStr(data)
        elif isinstance(data, (date, datetime)):
            return JSONStr(data.isoformat())
        elif isinstance(data, float):
            return JSONFloat(data)
        elif isinstance(data, int):
            return JSONInt(data)
        else:
            if not raise_exception:
                return JSONUnknown(data)
            else:
                raise JSONDecodeException(f"Wrong data's format: {type(data)}")

    @classmethod
    def open(cls, file):
        """
        Open an external JSON file.
        If a valid url string is passed, then it will try to make a get request to such a target and decode a json file
        """
        if url_validator(file):
            req = retry_function(requests.get, file, raise_exception=False)
            try:
                data = req.json()
            except Exception as e:
                raise JSONDecodeException(
                    f"Selected URL has no valid json file. Details: {e}"
                )
            else:
                return cls(data)
        with open(file) as f:
            data = json.load(f)
        return cls(data)


class JSONNode:
    """
    This is the base class for all JSON objects (compose or singleton).

    Attributes:
    -----------
        _child_objects:
        key: last dict parent key where the object comes from
        index: las list parent index where the object comes from
        parent: last parent object where this object comes from
        _id: unique uuid4 hex identifier of object
    """

    def __init__(self, *args, **kwargs):

        self.key = None
        self.index = None
        self.parent = None
        self._id = uuid4().hex

    def _set_new_uuid(self):

        self._id = uuid4().hex
        return self._id

    def json_encode(self, **kwargs):
        return json.dumps(self, cls=JSONObjectEncoder, **kwargs)

    @property
    def json_decode(self):
        return json.loads(json.dumps(self, cls=JSONObjectEncoder))

    @property
    def jsonpath(self):
        parent = self
        path = JSONPath()
        while parent is not None:
            path._update(key=parent.key, index=parent.index)
            parent = parent.parent
        return path

    @property
    def root(self):
        """Get root object from current node object"""

        parent = self
        last = parent
        while parent is not None:
            last = parent
            parent = parent.parent
        return last

    def __str__(self):
        return self.json_encode(indent=4)

    # ---- ACTION METHODS ----
    def gt_action(self, other):
        from jsonutils.functions.actions import _gt

        return _gt(self, other)

    def gte_action(self, other):
        from jsonutils.functions.actions import _gte

        return _gte(self, other)

    def lt_action(self, other):
        from jsonutils.functions.actions import _lt

        return _lt(self, other)

    def lte_action(self, other):
        from jsonutils.functions.actions import _lte

        return _lte(self, other)

    def exact_action(self, other):
        from jsonutils.functions.actions import _exact

        return _exact(self, other)

    def contains_action(self, other):
        from jsonutils.functions.actions import _contains

        return _contains(self, other)

    def icontains_action(self, other):
        from jsonutils.functions.actions import _icontains

        return _icontains(self, other)

    def in_action(self, other):
        from jsonutils.functions.actions import _in

        return _in(self, other)

    def regex_action(self, other):
        from jsonutils.functions.actions import _regex

        return _regex(self, other)

    def fullregex_action(self, other):
        from jsonutils.functions.actions import _fullregex

        return _fullregex(self, other)

    def isnull_action(self, other):
        from jsonutils.functions.actions import _isnull

        return _isnull(self, other)

    def length_action(self, other):
        from jsonutils.functions.actions import _length

        return _length(self, other)

    def type_action(self, other):
        from jsonutils.functions.actions import _type

        return _type(self, other)


class JSONCompose(JSONNode):
    """
    This is the base class for JSON composed objects.
    Composed objects can be dict or list instances.
    Composed objects can send queries to children (which can be also compose or singleton objects)
    """

    is_composed = True

    def __init__(self, *args, **kwargs):
        """
        By initializing instance, it assign types to child items
        """
        super().__init__(*args, **kwargs)
        self._child_objects = UUIDdict()
        self._assign_children()

    def _assign_children(self):
        """Any JSON object can be a child for a given compose object"""
        if isinstance(self, JSONDict):
            for key, value in self.items():
                child = JSONObject(value)
                child.key = key
                child.parent = self
                self.__setitem__(key, child)

        elif isinstance(self, JSONList):
            for index, item in enumerate(self):
                child = JSONObject(item)
                child.index = index
                child.parent = self
                self.__setitem__(index, child)

    def query(self, recursive_=None, include_parent_=None, **q):
        # within a particular parent node, each child in _child_objects registry must have a unique key
        if recursive_ is None:
            recursive_ = config.recursive_queries
        if include_parent_ is None:
            include_parent_ = config.include_parents
        queryset = QuerySet()
        queryset._root = self  # the node which sends the query
        children = self._child_objects.values()
        for child in children:
            # if child satisfies query request, it will be appended to the queryset object
            check, obj = _parse_query(child, include_parent_, **q)
            if check:
                queryset.append(obj)
            # if child is also a compose object, it will send the same query to its children recursively
            if child.is_composed and recursive_:
                queryset += child.query(include_parent_=include_parent_, **q)
        return queryset


class JSONSingleton(JSONNode):
    """
    This is the base class for JSON singleton objects.
    A singleton object has no children
    Singleton object might be: JSONStr, JSONFloat, JSONInt, JSONBool, JSONNull.
    """

    is_composed = False


# ---- COMPOSE OBJECTS ----
class JSONDict(dict, JSONCompose):
    """ """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        JSONCompose.__init__(self, *args, **kwargs)

    def __dir__(self):
        # for autocompletion stuff
        if config.autocomplete_only_nodes:
            return self.keys()
        else:
            return list(self.keys()) + super().__dir__()

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:  # if a key error is thrown, then it will call __dir__
            raise AttributeError

    def __setitem__(self, k, v):
        """
        When setting a new child, we must follow this steps:
            1 - Initialize child
            2 - Remove old child item from _child_objects dictionary
            3 - Assign new child item to _child_objects dictionary
        """

        # ---- initalize child ----
        child = JSONObject(v)
        child.key = k
        child.parent = self

        # ---- remove old child ----
        prev_child = super().get(k)  # old child (maybe None)
        try:
            self._child_objects.pop(
                prev_child._id, None
            )  # we must remove current child item. If not, it would still appear in queries
        except AttributeError:
            pass

        # ---- assign new child ----
        self._child_objects[child._id] = child

        return super().__setitem__(k, child)

    def copy(self):
        obj = type(self)(self)
        obj.__dict__.update(self.__dict__)
        return obj

    # ---- COMPARISON METHODS ----
    def __eq__(self, other):
        return super().__eq__(other)

    def __gt__(self, other):
        return False

    def __ge__(self, other):
        return False

    def __lt__(self, other):
        return False

    def __le__(self, other):
        return False


class JSONList(list, JSONCompose):
    """ """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        JSONCompose.__init__(self, *args, **kwargs)

    def append(self, item):

        child = JSONObject(item)
        child.index = self.__len__()
        child.parent = self

        self._child_objects[child._id] = child
        return super().append(child)

    def copy(self):
        obj = type(self)(self)
        obj.__dict__.update(self.__dict__)
        return obj

    def length(self):
        return self.__len__()

    def __dir__(self):
        if config.autocomplete_only_nodes:
            return [f"_{i}" for i in range(len(self))]
        else:
            return [f"_{i}" for i in range(len(self))] + super().__dir__()

    def __getattr__(self, name):
        """We access child list items by _0, _1, etc"""

        try:
            return self.__getitem__(int(name.replace("_", "")))
        except ValueError:
            raise AttributeError

    def __setitem__(self, index, item):

        # ---- initialize child ----
        child = JSONObject(item)
        child.index = index
        child.parent = self

        # ---- remove old child ----
        prev_child = super().__getitem__(index)
        try:
            self._child_objects.pop(prev_child._id, None)
        except AttributeError:
            pass

        # ---- assign new child ----
        self._child_objects[child._id] = child

        return super().__setitem__(index, child)

    # ---- COMPARISON METHODS ----
    def __eq__(self, other):
        return super().__eq__(other)

    def __gt__(self, other):
        result = super().__gt__(other)
        if result == NotImplemented:
            return False
        else:
            return result

    def __ge__(self, other):
        result = super().__ge__(other)
        if result == NotImplemented:
            return False
        else:
            return result

    def __lt__(self, other):
        result = super().__lt__(other)
        if result == NotImplemented:
            return False
        else:
            return result

    def __le__(self, other):
        result = super().__le__(other)
        if result == NotImplemented:
            return False
        else:
            return result


# ---- SINGLETON OBJECTS ----
class JSONStr(str, JSONSingleton):
    def __new__(cls, string):
        obj = super().__new__(cls, string)
        obj._data = string
        return obj

    # converters
    def to_float(self, **kwargs):
        """
        Try to parse a python float64 from self string.
        Examples:
        --------
        >> from base import JSONStr
        >> JSONStr(" $5.3USD ").to_float()
            5.3
        >> JSONStr(" -$ 4,450,326.58 ").to_float()
            -4450326.58
        """

        return parse_float(self, **kwargs)

    def to_datetime(self, **kwargs):
        """Try to parse an aware datetime object from self string"""

        return parse_datetime(self, **kwargs)

    def to_bool(self):
        """Trye to parse a bool object from self string."""

        return parse_bool(self)

    # comparison magic methods
    # if data types are not compatible, then return False (no error thrown)
    # when querying, other will correspond to target query value (ex: Float__gt=<other>)
    # TODO implement clever parsing option
    def __eq__(self, other):
        # if target_value is a number, we first convert self str instance to float
        if isinstance(other, bool):
            try:
                return self.to_bool() == other
            except Exception:
                return False
        elif isinstance(other, (float, int)):
            try:
                return self.to_float() == other
            except Exception:
                return False
        # if target_value is a datetime
        elif isinstance(other, (date, datetime)):
            try:
                return self.to_datetime() == parse_datetime(other)
            except Exception:
                return False
        # if target_value is a str
        elif isinstance(other, str):
            if parse_datetime(
                other, only_check=True
            ):  # if target value is a datetime string
                try:
                    return self.to_datetime() == parse_datetime(other)
                except Exception:
                    return False
            else:
                try:
                    return super().__eq__(other)
                except Exception:
                    return False
        # otherwise (maybe list, dict, none)
        else:
            return False

    def __gt__(self, other):
        if isinstance(other, bool):
            return False
        # if target_value is a number
        if isinstance(other, (float, int)):
            try:
                return self.to_float() > other
            except Exception:
                return False
        # if target_value is a datetime
        elif isinstance(other, datetime):
            try:
                return self.to_datetime() > parse_datetime(other)
            except Exception:
                return False
        # if target_value is a str
        elif isinstance(other, str):
            if parse_datetime(
                other, only_check=True
            ):  # if target value is a datetime string
                try:
                    return self.to_datetime() > parse_datetime(other)
                except Exception:
                    return False
            else:
                try:
                    return super().__gt__(other)
                except Exception:
                    return False
        # otherwise (maybe list, dict, none, bool)
        else:
            return False

    def __ge__(self, other):
        if isinstance(other, bool):
            return False
        # if target_value is a number
        if isinstance(other, (float, int)):
            try:
                return self.to_float() >= other
            except Exception:
                return False
        # if target_value is a datetime
        elif isinstance(other, datetime):
            try:
                return self.to_datetime() >= parse_datetime(other)
            except Exception:
                return False
        # if target_value is a str
        elif isinstance(other, str):
            if parse_datetime(
                other, only_check=True
            ):  # if target value is a datetime string
                try:
                    return self.to_datetime() >= parse_datetime(other)
                except Exception:
                    return False
            else:
                try:
                    return super().__ge__(other)
                except Exception:
                    return False
        # otherwise (maybe list, dict, none, bool)
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, bool):
            return False
        # if target_value is a number
        if isinstance(other, (float, int)):
            try:
                return self.to_float() < other
            except Exception:
                return False
        # if target_value is a datetime
        elif isinstance(other, datetime):
            try:
                return self.to_datetime() < parse_datetime(other)
            except Exception:
                return False
        # if target_value is a str
        elif isinstance(other, str):
            if parse_datetime(
                other, only_check=True
            ):  # if target value is a datetime string
                try:
                    return self.to_datetime() < parse_datetime(other)
                except Exception:
                    return False
            else:
                try:
                    return super().__lt__(other)
                except Exception:
                    return False
        # otherwise (maybe list, dict, none, bool)
        else:
            return False

    def __le__(self, other):
        if isinstance(other, bool):
            return False
        # if target_value is a number
        if isinstance(other, (float, int)):
            try:
                return self.to_float() <= other
            except Exception:
                return False
        # if target_value is a datetime
        elif isinstance(other, datetime):
            try:
                return self.to_datetime() <= parse_datetime(other)
            except Exception:
                return False
        # if target_value is a str
        elif isinstance(other, str):
            if parse_datetime(
                other, only_check=True
            ):  # if target value is a datetime string
                try:
                    return self.to_datetime() <= parse_datetime(other)
                except Exception:
                    return False
            else:
                try:
                    return super().__le__(other)
                except Exception:
                    return False
        # otherwise (maybe list, dict, none, bool)
        else:
            return False


class JSONFloat(float, JSONSingleton):
    def __new__(cls, fl):
        obj = super().__new__(cls, fl)
        obj._data = fl
        return obj

    def __eq__(self, other):
        try:
            return super().__eq__(parse_float(other))
        except Exception:
            return False

    def __gt__(self, other):
        try:
            return super().__gt__(parse_float(other))
        except Exception:
            return False

    def __ge__(self, other):
        try:
            return super().__ge__(parse_float(other))
        except Exception:
            return False

    def __lt__(self, other):
        try:
            return super().__lt__(parse_float(other))
        except Exception:
            return False

    def __le__(self, other):
        try:
            return super().__le__(parse_float(other))
        except Exception:
            return False


class JSONInt(int, JSONSingleton):
    def __new__(cls, i):
        obj = super().__new__(cls, i)
        obj._data = i
        return obj

    def __eq__(self, other):
        try:
            return super().__float__().__eq__(parse_float(other))
        except Exception:
            return False

    def __gt__(self, other):
        try:
            return super().__float__().__gt__(parse_float(other))
        except Exception:
            return False

    def __ge__(self, other):
        try:
            return super().__float__().__ge__(parse_float(other))
        except Exception:
            return False

    def __lt__(self, other):
        try:
            return super().__float__().__lt__(parse_float(other))
        except Exception:
            return False

    def __le__(self, other):
        try:
            return super().__float__().__le__(parse_float(other))
        except Exception:
            return False


class JSONBool(JSONSingleton):
    def __init__(self, data):

        if not isinstance(data, bool):
            raise TypeError(f"Argument is not a valid boolean type: {type(data)}")
        super().__init__()
        self._data = data

    def __repr__(self):
        return str(self._data)

    def __bool__(self):
        return self._data

    def __eq__(self, other):

        try:
            return self._data == parse_bool(other)
        except Exception:
            return False

    def __gt__(self, other):
        return False

    def __ge__(self, other):
        return False

    def __lt__(self, other):
        return False

    def __le__(self, other):
        return False


class JSONNull(JSONSingleton):
    def __init__(self, data):

        if not isinstance(data, type(None)):
            raise TypeError(f"Argument is not a valid None type: {type(data)}")
        super().__init__()
        self._data = data

    def __repr__(self):
        return "None"

    def __bool__(self):
        return False

    def __eq__(self, other):
        try:
            return self._data == other
        except Exception:
            return False

    def __gt__(self, other):
        return False

    def __ge__(self, other):
        return False

    def __lt__(self, other):
        return False

    def __le__(self, other):
        return False


class JSONUnknown(JSONSingleton):
    """Unknown object"""

    pass
