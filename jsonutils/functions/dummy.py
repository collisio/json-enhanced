import random
import string

from jsonutils.base import (
    JSONBool,
    JSONDict,
    JSONFloat,
    JSONInt,
    JSONList,
    JSONNull,
    JSONStr,
)


def dummy_json(
    min_dict_length=2,
    max_dict_length=5,
    min_list_length=2,
    max_list_length=5,
    min_str_length=10,
    max_str_length=100,
    max_depth=10,
):
    """
    Generate a dummy JSONObject instance
    """
    # TODO

    # assert argument values are correct
    assert (
        min_dict_length <= max_dict_length
    ), "Argument min_dict_length must be less or equal than max_dict_length"

    assert (
        min_list_length <= max_list_length
    ), "Argument min_list_length must be less or equal than max_list_length"

    assert (
        min_str_length <= max_str_length
    ), "Argument min_str_length must be less or equal than max_str_length"

    NODE_LIST_ALL = (
        JSONBool,
        JSONDict,
        JSONFloat,
        JSONInt,
        JSONList,
        JSONNull,
        JSONStr,
    )

    NODE_LIST_COMPOSED = (
        JSONDict,
        JSONList,
    )

    NODE_LIST_SINGLETON = (JSONStr, JSONFloat, JSONInt, JSONBool, JSONNull)

    def get_random_string(N=4):
        return "".join(random.choices(string.ascii_lowercase, k=N))

    def get_random_node(kind="all"):
        if kind == "all":
            return random.choice(NODE_LIST_ALL)
        if kind == "composed":
            return random.choice(NODE_LIST_COMPOSED)
        if kind == "singleton":
            return random.choice(NODE_LIST_SINGLETON)
        else:
            raise ValueError(
                "Argument kind can only be some of the following: 'all', 'composed' or 'singletion'"
            )

    def initialize_singleton(node):
        "node must be a JSONSingleton instance"

        if node == JSONStr:
            out = get_random_string(8)
            return JSONStr(out)
        elif node == JSONBool:
            out = random.choice((True, False))
            return JSONBool(out)
        elif node == JSONInt:
            out = random.randint(0, 10000)
            return JSONInt(1)
        elif node == JSONFloat:
            out = random.random()*100
            return JSONFloat(out)
        elif node == JSONNull:
            return JSONNull(None)
        else:
            raise TypeError(f"node argument is not a JSONSingleton instance: {node}")

    def fill_composed_node(node, it=0):
        "node must be a JSONCompose instance"

        if isinstance(node, dict):
            length = random.randint(min_dict_length, max_dict_length)
            for _ in range(length):
                key = get_random_string()
                if it < max_depth:
                    value = get_random_node(kind="all")  # a node object
                else:
                    value = get_random_node(kind="singleton")
                if value.is_composed:
                    value = value()
                    fill_composed_node(value, it + 1)
                else:
                    value = initialize_singleton(value)
                node.__setitem__(key, value)
        elif isinstance(node, list):
            length = random.randint(min_list_length, max_list_length)
            for _ in range(length):
                if it < max_depth:
                    item = get_random_node(kind="all")
                else:
                    item = get_random_node(kind="singleton")
                if item.is_composed:
                    item = item()
                    fill_composed_node(item, it + 1)
                else:
                    item = initialize_singleton(item)
                node.append(item)

    # get the initial node
    initial_node = get_random_node(kind="composed")()

    fill_composed_node(initial_node)
    return initial_node
