# This module contains the base objects needed
import json
import os
import sys
from datetime import date, datetime
from uuid import uuid4

import requests
from bs4 import BeautifulSoup

import jsonutils.config as config
from jsonutils.cache import memoized_method
from jsonutils.encoders import JSONObjectEncoder
from jsonutils.exceptions import (
    JSONDecodeException,
    JSONNotFoundException,
    JSONQueryException,
    JSONQueryMultipleValues,
)
from jsonutils.functions.decorators import catch_exceptions
from jsonutils.functions.parsers import (
    _parse_html_table,
    _parse_query,
    _parse_query_key,
    _to_django_model,
    parse_bool,
    parse_datetime,
    parse_float,
    parse_timestamp,
    url_validator,
)
from jsonutils.query import All, KeyQuerySet, ParentList, QuerySet
from jsonutils.utils.dict import UUIDdict, ValuesDict
from jsonutils.utils.retry import retry_function

try:
    DjangoQuerySet = sys.modules["django"].db.models.QuerySet
except Exception:
    DjangoQuerySet = type(None)


class JSONPath:
    """
    Object representing a JSON path for a given JSON object.
    Don't instanciate it directly.
    """

    def __new__(cls, s=""):
        obj = super().__new__(cls)
        obj._string = s  # pretty path
        obj._path = ""  # python json path
        obj._keys = []  # list of dict keys
        return obj

    @property
    def data(self):
        return self._string

    @property
    def expr(self):
        return self._path

    @property
    def keys(self):
        return list(reversed(self._keys))

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
            self._keys.append(key)
        elif (index := kwargs.get("index")) is not None:
            self._string = str(index) + "/" + self._string
            self._path = f"[{index}]" + self._path
            self._keys.append(index)

    def __eq__(self, other):
        return (self._string == other) or (self._path == other)

    def __repr__(self):
        return self._string


class JSONObject:
    """
    This class acts as a switcher. It will return the corresponding object instance for a given data.
    This class does not contain any instances of.
    """

    _RESERVED_ATTRIBUTES = (
        "_key",
        "_index",
        "parent",
        "_id",
        "_child_objects",
        "_is_annotation",
    )

    def __new__(cls, data=None, raise_exception=False, serialize_nodes=False):
        """
        Params:
        ------
            data: the json data that is going to be parsed.
            raise_exception: if True, then an exception will be raised if data type is not known. Otherwise, a JSONUnknown
                instance will be created for such a data.
            serialize_nodes: if True and data represents a node instance, then take it as a raw data, discarding
                all its old node attributes.
        """
        if not isinstance(raise_exception, bool):
            raise TypeError(
                f"raise_exception argument must be a boolean, not {type(raise_exception)}"
            )
        if isinstance(data, JSONNode):
            if serialize_nodes:
                return cls(data._data)
            else:
                return data
        elif isinstance(data, type(None)):
            return JSONNull(data)
        elif isinstance(data, dict):
            return JSONDict(data)
        elif isinstance(data, (list, tuple, DjangoQuerySet)):
            return JSONList(data)
        elif isinstance(data, bool):
            return JSONBool(data)
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
    def open(cls, file, raise_exception=True, **kwargs):
        """
        Open an external JSON file.
        If a valid url string is passed, then it will try to make a get/post request to such a target and decode a json file
        """
        # decide whether to use requests.get or requests.post by checking kwargs
        if kwargs.get("json") or kwargs.get("data"):
            FUNCTION = requests.post
        else:
            FUNCTION = requests.get
        file = str(file)
        if url_validator(file):
            req = retry_function(
                FUNCTION, file, raise_exception=raise_exception, **kwargs
            )
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

    @classmethod
    def loads(cls, string, **kwargs):
        """
        This is a wrapper for json.loads. It takes a json string as argument and returns a JSONNode instance
        """

        try:
            data = json.loads(string, **kwargs)
        except Exception as e:
            raise JSONDecodeException(
                f"Error when parsing the json string. Error message: {e}"
            )
        else:
            return cls(data)

    @staticmethod
    def read_html_table(
        data,
        raise_exception=True,
        attrs={},
        recursive=True,
        parse_links=False,
        link_prefix=None,
        **kwargs,
    ):
        if not isinstance(data, str):
            raise TypeError(f"Argument data must be an str instance")

        if url_validator(data):
            try:
                req = retry_function(requests.get, data, **kwargs)
            except Exception:
                if raise_exception:
                    raise
                else:
                    return

            soup = BeautifulSoup(req.content, "lxml")
            table = soup.find("table", attrs, recursive)

            if not table:
                if raise_exception:
                    raise JSONNotFoundException(
                        "A table matching the required parameters has not been found on the selected website."
                    )
                else:
                    return

            try:
                result = _parse_html_table(
                    table,
                    parse_links,
                    link_prefix,
                )
            except Exception:
                if raise_exception:
                    raise
                else:
                    result = None

            return result

        else:  # data is already an html string
            soup = BeautifulSoup(data, "lxml")
            table = soup.find("table", attrs, recursive)

            if not table:
                if raise_exception:
                    raise JSONNotFoundException(
                        "A table matching the required parameters has not been found on the selected website."
                    )
                else:
                    return

            try:
                result = _parse_html_table(
                    table,
                    parse_links,
                    link_prefix,
                )
            except Exception:
                if raise_exception:
                    raise
                else:
                    result = None

            return result


class JSONNode:
    """
    This is the base class for all JSON objects (compose or singleton).

    Attributes:
    -----------
        _child_objects:
        _key: last dict parent key where the object comes from
        _index: las list parent index where the object comes from
        parent: last parent object where this object comes from
        _id: unique uuid4 hex identifier of object
    """

    __odir__ = object.__dir__  # rename old __dir__ method to __odir__
    __osetattr__ = object.__setattr__

    def __init__(self, *args, **kwargs):

        self._key = None
        self._index = None
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
            path._update(key=parent._key, index=parent._index)
            parent = parent.parent
        return path

    @property
    def parent_list(self):
        pl = ParentList()

        parent = self
        last = parent
        while parent is not None:
            last = parent
            parent = parent.parent
            pl.append(last)

        return pl[1:]

    @property
    def root(self):
        """Get root object from current node object"""

        parent = self
        last = parent
        while parent is not None:
            last = parent
            parent = parent.parent
        return last

    def values(self, *keys, search_upwards=True, flat=False, **kwargs):
        if flat is True and len(keys) > 1:
            raise ValueError(
                "If flat argument is selected, you can only set one key value"
            )
        output_dict = ValuesDict({k: None for k in keys})

        if kwargs:
            output_dict.update({k: None for k in kwargs})

        for key in keys:
            obj = self
            if "__" in key:  # traverse by childs in this case
                child_key = key.split("__")[-1]
                if not child_key:
                    raise ValueError("Wrong syntax within query values request")
                output_dict[key] = obj.parent.get(
                    **{child_key: All}, native_types_=True, throw_exceptions_=False
                )
                continue
            while True:
                if isinstance(obj, JSONDict):
                    if key in obj:
                        output_dict[key] = obj[key]._data
                        break
                if (
                    search_upwards
                ):  # TODO search_upwards can be a number (number of recursive upwards lookings)
                    obj = obj.parent
                    if obj is None:
                        break
                else:
                    break

        if kwargs:
            for k, v in kwargs.items():
                obj = self
                if "__" in v:  # traverse by childs in this case
                    child_key = v.split("__")[-1]
                    if not child_key:
                        raise ValueError("Wrong syntax within query values request")
                    output_dict[k] = obj.parent.get(
                        **{child_key: All}, native_types_=True, throw_exceptions_=False
                    )
                    continue
                while True:
                    if isinstance(obj, JSONDict):
                        if v in obj:
                            output_dict[k] = obj[v]._data
                            break
                    if search_upwards:
                        obj = obj.parent
                        if obj is None:
                            break
                    else:
                        break

        return output_dict if not flat else list(output_dict.values())[0]

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

    def key_action(self, other):
        from jsonutils.functions.actions import _key

        return _key(self, other)

    def index_action(self, other):
        from jsonutils.functions.actions import _index

        return _index(self, other)

    def path_action(self, other):
        from jsonutils.functions.actions import _path

        return _path(self, other)

    def notpath_action(self, other):
        from jsonutils.functions.actions import _notpath

        return _notpath(self, other)

    def startswith_action(self, other):
        from jsonutils.functions.actions import _startswith

        return _startswith(self, other)

    def endswith_action(self, other):
        from jsonutils.functions.actions import _endswith

        return _endswith(self, other)

    def apply_action(self, other):
        from jsonutils.functions.actions import _apply

        return _apply(self, other)


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

    @property
    def _data(self):
        return super().json_decode

    def _assign_children(self):
        """Any JSON object can be a child for a given compose object"""
        if isinstance(self, JSONDict):
            for key, value in self.items():
                self.__setitem__(key, value)

        elif isinstance(self, JSONList):
            for index, item in enumerate(self):
                self.__setitem__(index, item)

    def query(
        self,
        recursive_=None,
        include_parent_=None,
        stop_at_match_=None,
        native_types_=None,
        **q,
    ):
        if not isinstance(stop_at_match_, (int, type(None))):
            raise TypeError(
                f"Argument stop_at_match_ must be an integer or NoneType, not {type(stop_at_match_)}"
            )

        # within a particular parent node, each child in _child_objects registry must have a unique key

        # ---- DYNAMIC CONFIG ----
        if recursive_ is None:
            recursive_ = config.recursive_queries
        if include_parent_ is None:
            include_parent_ = config.include_parents
        if native_types_ is None:
            native_types_ = config.native_types
        # ------------------------
        queryset = QuerySet()
        if native_types_:
            queryset._native_types = True
        queryset._root = self  # the node which sends the query
        children = self._child_objects.values()
        for child in children:
            # if child satisfies query request, it will be appended to the queryset object
            check, obj = _parse_query(child, include_parent_, **q)
            if check:
                queryset.append(obj)
                if stop_at_match_ and queryset.count() >= stop_at_match_:
                    return queryset

            # if child is also a compose object, it will send the same query to its children recursively
            if child.is_composed and recursive_:
                queryset += child.query(
                    recursive_=recursive_,
                    include_parent_=include_parent_,
                    stop_at_match_=stop_at_match_,
                    native_types_=native_types_,
                    **q,
                )
        return queryset

    def get(
        self,
        recursive_=None,
        include_parent_=None,
        throw_exceptions_=None,
        native_types_=None,
        **q,
    ):

        # ---- DYNAMIC CONFIG ----
        if recursive_ is None:
            recursive_ = config.recursive_queries
        if include_parent_ is None:
            include_parent_ = config.include_parents
        if throw_exceptions_ is None:
            throw_exceptions_ = config.query_exceptions
        if native_types_ is None:
            native_types_ = config.native_types
        # ------------------------
        query = self.query(
            recursive_=recursive_,
            include_parent_=include_parent_,
            stop_at_match_=2,
            native_types_=native_types_,
            **q,
        )

        if not query.exists():
            if throw_exceptions_:
                raise JSONQueryException("The query has not returned any result")
            else:
                return None if native_types_ else JSONNull(None)
        elif query.count() > 1:
            if throw_exceptions_:
                raise JSONQueryMultipleValues("More than one value returned by query")
            else:
                return query.first()
        else:
            return query.first()

    def annotate(self, **kwargs):
        """
        Annotate key:value pairs in each dict's child.
        If a key already exists, then ignore it.

        Example
        -------

        import jsonutils as js

        data = js.JSONObject(
            {
                "A": [
                    {
                        "A1": 1
                    },
                    {
                        "A2": 2
                    }
                ],
                "B": {
                    "B1": 1,
                    "B2": 2
                }
            }
        )

        >> data.annotate(C=3, D=4)
            {
                "A": [
                    {
                        "A1": 1,
                        "C": 3,
                        "D": 4
                    },
                    {
                        "A2": 2,
                        "C": 3,
                        "D": 4
                    }
                ],
                "B": {
                    "B1": 1,
                    "B2": 2,
                    "C": 3,
                    "D": 4
                },
                "C": 3,
                "D": 4
            }
        """

        if isinstance(self, JSONDict):
            _registered_keys = set()
            for key, value in kwargs.items():
                # if key from annotation is not in dict keys, register it
                if key not in self.keys():
                    child = JSONObject(value)
                    child._key = key
                    child.parent = self
                    child._is_annotation = True
                    self.__setitem__(key, child)
                    _registered_keys.add(child._id)

            for ch in self._child_objects.values_except(_registered_keys):
                if ch.is_composed:
                    ch.annotate(**kwargs)
        elif isinstance(self, JSONList):
            for ch in self._child_objects.values():
                if ch.is_composed:
                    ch.annotate(**kwargs)
        return self

    def query_key(
        self,
        pattern,
        recursive_=None,
        include_parent_=None,
        stop_at_match_=None,
        native_types_=None,
        **q,
    ):
        if not isinstance(stop_at_match_, (int, type(None))):
            raise TypeError(
                f"Argument stop_at_match_ must be an integer or NoneType, not {type(stop_at_match_)}"
            )

        # within a particular parent node, each child in _child_objects registry must have a unique key

        # ---- DYNAMIC CONFIG ----
        if recursive_ is None:
            recursive_ = config.recursive_queries
        if include_parent_ is None:
            include_parent_ = config.include_parents
        if native_types_ is None:
            native_types_ = config.native_types
        # ------------------------
        queryset = KeyQuerySet()
        if native_types_:
            queryset._native_types = True
        queryset._root = self  # the node which sends the query
        children = self._child_objects.values()
        for child in children:
            # if child satisfies query request, it will be appended to the queryset object
            check, obj = _parse_query_key(child, pattern, include_parent_, **q)
            if check:
                queryset.append(obj)
                if stop_at_match_ and queryset.count() >= stop_at_match_:
                    return queryset

            # if child is also a compose object, it will send the same query to its children recursively
            if child.is_composed and recursive_:
                queryset += child.query_key(
                    pattern,
                    recursive_=recursive_,
                    include_parent_=include_parent_,
                    stop_at_match_=stop_at_match_,
                    native_types_=native_types_,
                    **q,
                )
        return queryset

    def _remove_annotations(self, recursive=True):

        if isinstance(self, JSONDict):
            for key, value in list(self.items()):
                if "_is_annotation" in value.__odir__():
                    self.pop(key)
                if value.is_composed and recursive:
                    value._remove_annotations()

        elif isinstance(self, JSONList):
            for item in self:
                if item.is_composed and recursive:
                    item._remove_annotations()

    @catch_exceptions
    def _eval_path(self, path, fail_silently=False):
        """
        Evaluate JSONCompose object over a jsonpath
        """
        # TODO add test
        if isinstance(path, str):
            aux = JSONPath()
            aux._path = path
            path = aux
        return eval(f"self{path.expr}")

    def traverse_json(self):
        """
        Traverse recursively over all json data
        """

        output_list = QuerySet()

        children = self._child_objects.values()
        for child in children:
            serialized_child = child._data
            output_list.append(
                JSONObject({"path": child.jsonpath.expr, "value": serialized_child})
            )
            if child.is_composed:
                output_list += child.traverse_json()

        return output_list

    def check_valid_types(self):
        """Check if json object has valid types (not unknown types)"""

        queryset = self.query_key("*", type__="unknown")
        if queryset.exists():
            errors = [
                {
                    item._key: {"path": item.jsonpath.data, "type": item._type}
                    for item in queryset
                }
            ]
            return False, errors
        else:
            return True, None

    def validate_schema(self, schema):
        """Validate against a json schema with defined types"""
        from jsonutils.functions.validator import _validate_data

        return _validate_data(self, schema)


class JSONSingleton(JSONNode):
    """
    This is the base class for JSON singleton objects.
    A singleton object has no children
    Singleton object might be: JSONStr, JSONFloat, JSONInt, JSONBool, JSONNull.
    """

    is_composed = False

    def query(self, **kwargs):
        return QuerySet()

    def get(self, **kwargs):
        return


# ---- COMPOSE OBJECTS ----
class JSONDict(dict, JSONCompose):
    """ """

    _DEFAULT = object()
    get = JSONCompose.get  # override get method
    _get = dict.get  # original get method
    values = JSONNode.values

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        JSONCompose.__init__(self, *args, **kwargs)

    def __dir__(self):
        # for autocompletion stuff
        if config.autocomplete_only_nodes:
            return list(self.keys())
        else:
            return list(self.keys()) + super().__dir__()

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:  # if a key error is thrown, then it will call __dir__
            return

    def __setitem__(self, k, v):
        """
        When setting a new child, we must follow this steps:
            1 - Initialize child
            2 - Remove old child item from _child_objects dictionary
            3 - Assign new child item to _child_objects dictionary
        """

        # ---- initalize child ----
        child = JSONObject(v)
        child._key = k
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

    def __setattr__(self, name, value):
        """To define behaviour when setting an atributte. It must register a new node if not a reserved keyword"""

        if name in JSONObject._RESERVED_ATTRIBUTES:
            return super().__setattr__(name, value)
        else:
            return self.__setitem__(name, value)

    def copy(self):
        cls = self.__class__
        obj = cls(self.json_decode)
        return obj

    def pop(self, key, default=_DEFAULT):
        """
        When removing a key from dict, we also must unregister the corresponding child
        from _child_objects dictionary
        """
        if key in self or default is self._DEFAULT:
            child = self[key]  # getting the child
            del self[key]
            self._child_objects.pop(child._id, None)  # unregister child
            return child
        else:
            return default

    def to_django_model(self, model, fail_silently=False):
        """Translates a JSON dict to Django model new instance"""

        return _to_django_model(self, model, fail_silently=fail_silently)

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

    def append(self, item, serialize_nodes=True):

        child = JSONObject(item, serialize_nodes=serialize_nodes)
        child._index = self.__len__()
        child.parent = self

        self._child_objects[child._id] = child
        return super().append(child)

    def copy(self):
        cls = self.__class__
        obj = cls(self.json_decode)
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

    def __setattr__(self, name, value):
        """To define behaviour when setting an atributte. It must register a new node if not a reserved keyword"""

        if name in JSONObject._RESERVED_ATTRIBUTES:
            return super().__setattr__(name, value)
        else:
            name = int(name.replace("_", ""))
            return self.__setitem__(name, value)

    def __setitem__(self, index, item):

        # ---- initialize child ----
        child = JSONObject(item)
        child._index = index
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
        obj._data = str(string)
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

    def to_timestamp(self, **kwargs):
        """Try to parse a POSIX timestamp string from self string"""

        return parse_timestamp(self, **kwargs)

    def to_bool(self):
        """Trye to parse a bool object from self string."""

        return parse_bool(self)

    def __hash__(self):
        return super().__hash__()

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
        obj._data = float(fl)
        return obj

    def __hash__(self):
        return super().__hash__()

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
        obj._data = int(i)
        return obj

    def __hash__(self):
        return super().__hash__()

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

    def __ne__(self, other):
        try:
            return self._data != parse_bool(other)
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

    def __ne__(self, other):
        try:
            return self._data != other
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

    def __init__(self, data):
        super().__init__()
        self._data = data
        self._type = type(data)
