# ---- BASE OBJECT ----
class JsonMaster:
    def __new__(cls, data):

        if isinstance(data, dict):
            return JsonDict(data)
        elif isinstance(data, list):
            return JsonList(data)
        elif isinstance(data, str):
            return JsonStr(data)
        elif isinstance(data, float):
            return JsonFloat(data)
        elif isinstance(data, int):
            return JsonInt(data)
        else:
            raise TypeError(f"Wrong data's format: {type(data)}")

    def _send_query(self, **q):

        childs = self._child_objects
        if len(childs) < 1:
            print(self)
        for child in childs:
            child._send_query(**q)


# ---- SINGLE OBJECTS ----
class JsonStr(str, JsonMaster):
    def __new__(cls, value):
        return super().__new__(cls, value)

    def __init__(self, value):
        self._child_objects = []


class JsonFloat(float, JsonMaster):
    def __new__(cls, value):
        return super().__new__(cls, value)

    def __init__(self, value):
        self._child_objects = []


class JsonInt(int, JsonMaster):
    def __new__(cls, value):
        return super().__new__(cls, value)

    def __init__(self, value):
        self._child_objects = []


# ---- COMPOUND OBJECTS ----


class JsonList(list, JsonMaster):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._child_objects = []
        self._assign_childs()

    def _assign_childs(self):

        for i, item in enumerate(self):

            if isinstance(item, list):
                child = JsonList(item)
            elif isinstance(item, dict):
                child = JsonDict(item)
            elif isinstance(item, str):
                child = JsonStr(item)
            elif isinstance(item, float):
                child = JsonFloat(item)
            elif isinstance(item, int):
                child = JsonInt(item)
            else:
                raise TypeError(f"Wrong data's format: {type(item)}")

            self.__setitem__(i, child)
            self._child_objects.append(child)

    def query(self, **q):

        return self._send_query(**q)


class JsonDict(dict, JsonMaster):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._child_objects = []
        self._assign_childs()

    def _assign_childs(self):

        for key, value in self.items():

            if isinstance(value, list):
                child = JsonList(value)
            elif isinstance(value, dict):
                child = JsonDict(value)
            elif isinstance(value, str):
                child = JsonStr(value)
            elif isinstance(value, float):
                child = JsonFloat(value)
            elif isinstance(value, int):
                child = JsonInt(value)
            else:
                raise TypeError(f"Wrong data's format: {type(value)}")

            self.__setitem__(key, child)
            self._child_objects.append(child)

    def query(self, **q):

        return self._send_query(**q)
