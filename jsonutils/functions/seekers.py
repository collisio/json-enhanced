# Functions to find elements in a JSONObject


import json
from functools import reduce
from operator import getitem

# from jsonutils.base import JSONNull, JSONSingleton
from jsonutils.exceptions import JSONPathException


class Default:
    pass


class _EmptyType(type):
    def __bool__(self):
        return False


class empty(metaclass=_EmptyType):
    """
    This object represents an empty element.
    Its boolean value is False, as should be expected.
    """

    pass


# def _inner_join_overwriting_with_null(node1, node2):
#     """
#     In an inner_join, an output will only be returned if both nodes are non empty.
#     When overwrite_with_null=True, then we return always node2, regardless of whether it is null or not.
#     """
#     if any(isinstance(node, _EmptyType) for node in (node1, node2)):
#         return empty
#     return node2


# def _inner_join_non_overwriting_with_null(node1, node2):
#     """
#     In an inner_join, an output will only be returned if both nodes are non empty.
#     When overwrite_with_null=False, then we return node2 only if it is not null.
#     Otherwise, node1 will be returned.
#     """
#     if any(isinstance(node, _EmptyType) for node in (node1, node2)):
#         return empty
#     return node2 if not isinstance(node2, JSONNull) else node1


# def _outer_join_overwriting_with_null(node1, node2):
#     """
#     In an outer_join, the non-empty value will be returned. If both nodes are empty then
#     the output will be an empty class.
#     When overwrite_with_null=True, then we return always node2, regardless of whether it is null or not.
#     """
#     empty_number = 0
#     args = (node1, node2)
#     for idx, node in enumerate(args):
#         if isinstance(node, _EmptyType):
#             empty_number += 1
#             empty_id = idx
#     if empty_number == 2:
#         return empty
#     if empty_number == 1:
#         return args[empty_id - 1]
#     return node2


# def _outer_join_non_overwriting_with_null(node1, node2):
#     """
#     In an outer_join, the non-empty value will be returned. If both nodes are empty then
#     the output will be an empty class.
#     When overwrite_with_null=False, then we return node2 only if it is not null.
#     Otherwise, node1 will be returned.
#     """

#     empty_number = 0
#     args = (node1, node2)
#     for idx, node in enumerate(args):
#         if isinstance(node, _EmptyType):
#             empty_number += 1
#             empty_id = idx
#     if empty_number == 2:
#         return empty
#     if empty_number == 1:
#         return args[empty_id - 1]
#     return node2 if not isinstance(node2, JSONNull) else node1


# def _left_join_overwriting_with_null(node1, node2, direct_order=True):
#     """
#     In a left_join, we keep the left node when any of the two nodes are empty.
#     """

#     if isinstance(node1, _EmptyType):
#         return empty
#     if isinstance(node2, _EmptyType):
#         return node1

#     return (
#         _inner_join_overwriting_with_null(node1, node2)
#         if direct_order
#         else _inner_join_overwriting_with_null(node2, node1)
#     )


# def _left_join_non_overwriting_with_null(node1, node2, direct_order=True):
#     """
#     In a left_join, we keep the left node when any of the two nodes are empty.
#     """

#     if isinstance(node1, _EmptyType):
#         return empty
#     if isinstance(node2, _EmptyType):
#         return node1

#     return (
#         _inner_join_non_overwriting_with_null(node1, node2)
#         if direct_order
#         else _inner_join_non_overwriting_with_null(node2, node1)
#     )


# def _right_join_overwriting_with_null(node1, node2):
#     """
#     In a right_join, we keep the right node when any of the two nodes are empty.
#     """

#     return _left_join_overwriting_with_null(node2, node1, direct_order=False)


# def _right_join_non_overwriting_with_null(node1, node2):
#     """
#     In a right_join, we keep the right node when any of the two nodes are empty.
#     """

#     return _left_join_non_overwriting_with_null(node2, node1, direct_order=False)


# def _choose_value(node1, node2, overwrite_with_null=True, merge_type="inner_join"):
#     """
#     Given two singleton nodes with the same path as arguments, choose an appropiate output node.
#     Preference order by default: singleton > null > empty

#     Arguments
#     ---------
#         node1: a node type, or empty
#         node2: a node type, or empty
#         overwrite_with_null: type of behaviour when a null value is found on node2
#         merge_type: type of behaviour when a missing path is found (node1 or node2 is empty)
#     Returns
#     -------
#         A node object or empty
#     """
#     # TODO define a compose method which call this private function over all its elements,
#     # with an append_compose option (if True, then composed objects (dict and list) will be appended)
#     # ---- TYPE CHECK ----

#     if not all(isinstance(x, (JSONSingleton, _EmptyType)) for x in (node1, node2)):
#         raise TypeError(
#             f"First two arguments must be node or empty instances:\n{type(node1)}\n{type(node2)}"
#         )

#     if not isinstance(merge_type, str):
#         raise TypeError(
#             f"Argument 'merge_type' must be an str instance, not {type(merge_type)}"
#         )

#     merge_type = merge_type.lower().strip()

#     if not isinstance(overwrite_with_null, bool):
#         raise TypeError(
#             f"Argument 'overwrite_with_null' must be a bool instance, not {type(overwrite_with_null)}"
#         )

#     if not merge_type in ("inner_join", "outer_join", "left_join", "right_join"):
#         raise ValueError(
#             f"Argument 'merge_type' must be one of the following: 'inner_join', 'outer_join', 'left_join', 'right_join'"
#         )

#     # --- variation cases ----
#     # We have 3 elements (NA, empty, singleton) that we have to arrange in pairs, allowing repetitions.
#     # So, the number of variations will be 3^2 = 9.
#     # Note that the combination "empty, empty" is not possible. However, we include it for consistency
#     # =========== combinations ============
#     #    node1                     node2
#     # =====================================
#     #     NA                        NA
#     #     NA                       empty
#     #    empty                      NA
#     #    empty                     empty
#     #     NA                      singleton
#     #  singleton                    NA
#     #    empty                    singleton
#     #  singleton                   empty
#     #  singleton                  singleton

#     if merge_type == "inner_join":
#         if overwrite_with_null:
#             return _inner_join_overwriting_with_null(node1, node2)
#         else:
#             return _inner_join_non_overwriting_with_null(node1, node2)
#     if merge_type == "outer_join":
#         if overwrite_with_null:
#             return _outer_join_overwriting_with_null(node1, node2)
#         else:
#             return _outer_join_non_overwriting_with_null(node1, node2)
#     if merge_type == "left_join":
#         if overwrite_with_null:
#             return _left_join_overwriting_with_null(node1, node2)
#         else:
#             return _left_join_non_overwriting_with_null(node1, node2)
#     if merge_type == "right_join":
#         if overwrite_with_null:
#             return _right_join_overwriting_with_null(node1, node2)
#         else:
#             return _right_join_non_overwriting_with_null(node1, node2)


def is_iterable(obj):
    """Check if obj is an iterable"""
    try:
        _ = iter(obj)
    except TypeError:
        return False

    return True


def _eval_object(obj, iterable):
    """Eval composed object on iterable path"""

    if not is_iterable(iterable):
        raise TypeError(
            f"Argument 'iterable' must be an iterable, not {type(iterable)}"
        )

    return reduce(getitem, iterable, obj)


def _set_object(obj, iterable, value):
    """
    The generalization of setitem for nested paths.
    First, it retrieves the iterable[:-1] item, and then it calls setitem method over such an item.
    """
    if not isinstance(iterable, (list, tuple)):
        raise TypeError(
            f"Argument 'iterable' must be a tuple or list instance, not {type(iterable)}"
        )
    get_path = iterable[:-1]
    set_path = iterable[-1]
    retrieved_obj = _eval_object(obj, get_path)
    retrieved_obj[set_path] = value


def _check_types(path, value):
    """
    Assert path and value has the right types
    """
    if not isinstance(path, (tuple, list)):
        raise JSONPathException(
            f"First element of iterables must be a tuple object with json path items, not {type(path)}"
        )
    if not path:
        raise JSONPathException("Path list must have a length greater on equal than 1")
    if isinstance(value, (str, float, int, bool, type(None))) or value in (
        {},
        [],
    ):
        pass
    else:
        raise JSONPathException(f"Path's value must be a singleton, not {value}")


def _json_from_path(iterable):
    """
    Build a JSONObject from a list/dict of path/value pairs.
    Examples
    --------

    res1 = JSONObject.from_path(
        [
            (
                ("A", "B"),
                True
            ),
            (
                ("A", "C"),
                False
            )
        ]
    )
    >> res1
        {
            "A": {
                "B": True,
                "C": False
            }
        }

    res2 = JSONObject.from_path(
        {
            (1, "A", 0): "1/A/0",
            (0, "A", 1, "B"): "0/A/1/B",
            (0, "A", 1, "C"): "0/A/1/C",
            (0, "A", 2): "0/A/2",
            (0, "A", 0, 0): "0/A/0/0"
        }
    )
    >> res2
        [
            {
                "A": [
                    "0/A/0/0",
                    {
                        "B": "0/A/1/B",
                        "C": "0/A/1/C"
                    },
                    "0/A/2"
                ]
            },
            {
                "A": [
                    "1/A/0"
                ]
            }
        ]

    """
    if not isinstance(iterable, (dict, list)):
        raise TypeError(
            f"Argument 'iterable' must be a list or dict, not {type(iterable)}"
        )

    if not iterable:
        raise ValueError(
            "Argument 'iterable' must have a length greater or equals than 1"
        )
    if isinstance(iterable, dict):
        iterable = iterable.items()
    initial_check = False
    for path, value in iterable:
        # check path and value have right types (path is a list or tuple, and value is not composed)
        _check_types(path, value)
        # build the schema dict inline
        if not initial_check:
            root_key = path[0]
            if isinstance(root_key, str):
                initial_object = DefaultDict()
            elif isinstance(root_key, int):
                initial_object = DefaultList()
            else:
                raise JSONPathException(f"Unknown object's type: {type(root_key)}")
            initial_check = True
        try:
            _set_object(initial_object, path, value)
        except Exception:
            raise JSONPathException("node structure is incompatible")

    # change inner dict by lists
    # we must serialize the default dict
    try:
        serialized_dict = initial_object.serialize()
    except Exception:  # it can be not serializable if it contains empty items (not connected list)
        raise JSONPathException("node structure is incompatible")

    return serialized_dict


class NaN:
    """
    Empty item in a not connected list.
    This object can only be present within a DefaultList.
    Do not instantiate it directly
    """

    def __init__(self, parent, index):
        self.parent = parent
        self.index = index

    def __getitem__(self, k):
        if isinstance(k, str):
            new_obj = DefaultDict()
            new_obj.parent = self.parent
            new_obj.index = self.index
            self.parent.__osetitem__(self.index, new_obj)
            parent_dict = self.parent.__ogetitem__(self.index)
            return parent_dict.__getitem__(k)
        elif isinstance(k, int):
            new_obj = DefaultList()
            new_obj.parent = self.parent
            new_obj.index = self.index
            self.parent.__osetitem__(self.index, new_obj)
            parent_list = self.parent.__ogetitem__(self.index)
            return parent_list.__getitem__(self.index)

    def __setitem__(self, k, v):

        idx = self.index
        parent = self.parent  # this is a DefaultList

        if isinstance(k, str):
            default_dict = DefaultList._superset(parent, idx, default=DefaultDict)
            default_dict.__setitem__(k, v)
            return
        elif isinstance(k, int):
            default_list = DefaultList._superset(parent, idx, default=DefaultList)
            default_list.__setitem__(k, v)
            return
        else:
            raise TypeError(f"Key 'k' must be an str or int instance, not {type(k)}")

    def __repr__(self):
        return "NaN"


class DefaultList(list):

    __osetitem__ = list.__setitem__
    __ogetitem__ = list.__getitem__

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args, **kwargs)
        obj.parent = None
        obj.key = None
        obj.index = None
        return obj

    @staticmethod
    def _superset(obj, idx, v=Default, default=None):
        if default is None:
            default = DefaultList
        if v is Default:
            v = default()
        if isinstance(v, default):
            v.parent = obj
            v.index = idx
        n = len(obj)
        obj.extend((NaN(parent=obj, index=i) for i in range(n, idx + 1)))
        obj.__osetitem__(idx, v)
        return obj.__ogetitem__(idx)

    def __getitem__(self, i):
        if isinstance(i, int):
            try:
                return super().__getitem__(i)
            except IndexError:
                default_list = self._superset(self, i, default=DefaultList)
                return default_list
        elif isinstance(i, str):
            parent = self.parent
            index = self.index
            if parent is None or index is None:
                raise NotImplementedError
            default_dict = self._superset(parent, index, default=DefaultDict)
            return default_dict.__getitem__(i)

    def __setitem__(self, i, v):

        if isinstance(i, int):
            try:
                item = super().__getitem__(i)
                if isinstance(
                    item, NaN
                ):  # if a NaN object, we allow to set it despite already registered key
                    raise IndexError
            except IndexError:  # only set item if it is not already registered
                self._superset(self, i, v)
                return
            raise Exception(f"Key {i} is already registered")
        elif isinstance(i, str):
            parent = self.parent
            index = self.index
            if self:  # if this DefaultList has any element, it cannot set a key path
                raise NotImplementedError
            default_dict = self._superset(parent, index, default=DefaultDict)
            return default_dict.__setitem__(i, v)

    def serialize(self):
        """Returns a new Python's native dict from a DefaultDict object"""

        return json.loads(json.dumps(self))


class DefaultDict(dict):
    """
    A dict schema with a default behaviour when setting new keys or indexes
    """

    __osetitem__ = dict.__setitem__
    __ogetitem__ = dict.__getitem__

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args, **kwargs)
        obj.parent = None
        obj.key = None
        obj.index = None
        return obj

    @staticmethod
    def _superset(obj, k, v=Default, default=None):
        """
        It will call essentially `obj[k] = v; return obj[k]`, but if v is a DefaultDict (default behaviour),
        then it will assign v a parent (obj) and a key (k), indicating the path from which the element is derived.
        Arguments
        ---------
            k: key index
            v: target value to set
            default: DefaultDict or DefaultList
        """
        if default is None:
            default = DefaultDict

        if v is Default:
            v = default()
        if isinstance(v, default):
            v.parent = obj
            v.key = k
        obj.__osetitem__(k, v)
        return obj.__ogetitem__(k)

    def __getitem__(self, k):

        if isinstance(k, str):
            try:  # if key is already in dict, simply returns it
                return super().__getitem__(k)
            except KeyError:  # if key is not in dict, register it to self by assigning a parent and a key
                return self._superset(self, k, default=DefaultDict)
        elif isinstance(k, int):
            parent = self.parent
            key = self.key
            if parent is None or key is None:
                raise NotImplementedError
            default_list = self._superset(parent, key, default=DefaultList)
            return default_list.__getitem__(k)
        else:
            raise TypeError(f"Dict keys must be an str or int instances, not {type(k)}")

    def __setitem__(self, k, v):
        if isinstance(k, str):
            if k in self:
                raise Exception(f"Key {k} is already registered")

            # only set item if it is not already registered
            self._superset(self, k, v, default=DefaultDict)
            return
        elif isinstance(k, int):
            parent = self.parent
            key = self.key
            if self:  # to avoid setting things like x["A"]["A"] = 1; x["A"][0] = 2
                raise NotImplementedError
            default_list = self._superset(parent, key, default=DefaultList)
            return default_list.__setitem__(k, v)

    def serialize(self):
        """Returns a new Python's native dict from a DefaultDict object"""

        return json.loads(json.dumps(self))


class DefaultTuple(tuple):
    """
    Like a tuple, but returning None if getting an index out of range.
    """

    def __getitem__(self, idx):
        try:
            return super().__getitem__(idx)
        except IndexError:
            pass


def _relative_to(child_path, parent_path):

    parent_path = DefaultTuple(parent_path)

    len_child_path = len(child_path)
    len_parent_path = len(parent_path)

    if len_child_path < len_parent_path:
        raise Exception(
            "The path of the child node must have a length equal to or greater than that of the parent."
        )

    output = ()

    for i in range(len_child_path):
        child_item = child_path[i]
        parent_item = parent_path[i]

        if (
            child_item != parent_item
        ):  # if should only differ after the parent_path has been iterated over, because child_path must be contained in parent_path
            if i < len_parent_path:
                raise Exception(
                    f"This child path comes not from selected parent's path.\nchild path: {child_path}\nparent path: {parent_path}"
                )
            output += child_path[i:]
            break
    return output
