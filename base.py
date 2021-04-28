# This module contains the base objects needed


class JSONObject:
    """
    This class acts as a switcher.
    """

    def __new__(cls, data):

        if isinstance(data, dict):
            return JSONDict(data)
        elif isinstance(data, list):
            return JSONList(data)
        elif isinstance(data, str):
            return JSONStr(data)
        elif isinstance(data, float):
            return JSONFloat(data)
        elif isinstance(data, int):
            return JSONInt(data)
        else:
            raise TypeError(f"Wrong data's format: {type(data)}")


class JSONMaster:
    """
    This is the base class for all JSON objects
    """

    def __init__(self, *args, **kwargs):

        self._child_objects = []


class JSONCompose(JSONMaster):
    """
    This is the base class for JSON composed objects.
    Composed objects can be dict or list instances.
    Composed objects can send queries to childs.
    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._assign_childs()

    def _assign_childs(self):

        if isinstance(self, JSONDict):
            for key, value in self.items():
                child = JSONObject(value)
                self.__setitem__(key, child)
                self._child_objects.append(child)

        elif isinstance(self, JSONList):
            for i, item in enumerate(self):
                child = JSONObject(item)
                self.__setitem__(i, child)
                self._child_objects.append(child)

    def query(self, **q):

        childs = self._child_objects
        if len(childs) < 1:
            print(self)
        for child in childs:
            child.query(**q)


class JSONSingleton(JSONMaster):
    """
    This is the base class for JSON singleton objects
    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)


class JSONDict(dict, JSONCompose):
    """"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        JSONCompose.__init__(self, *args, **kwargs)


class JSONList(list, JSONCompose):
    """"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        JSONCompose.__init__(self, *args, **kwargs)


class JSONStr(str, JSONSingleton):
    pass


class JSONFloat(float, JSONSingleton):
    pass


class JSONInt(int, JSONSingleton):
    pass