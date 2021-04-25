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

    def _send_query(self):

        childs = self._child_objects
        if len(childs) < 1:
            print(self)
        for child in childs:
            child._send_query()


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
    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)
        self._child_objects = []
        self._assign_childs()

    def _assign_childs(self) -> None:

        for i, item in enumerate(self):

            if isinstance(item, list):
                child = JsonList(item)
                self.__setitem__(i, child)
            elif isinstance(item, dict):
                child = JsonDict(item)
                self.__setitem__(i, child)
            elif isinstance(item, str):
                child = JsonStr(item)
                self.__setitem__(i, child)
            elif isinstance(item, float):
                child = JsonFloat(item)
                self.__setitem__(i, child)
            elif isinstance(item, int):
                child = JsonInt(item)
                self.__setitem__(i, child)
            else:
                raise TypeError(f"Wrong data's format: {type(item)}")

            self._child_objects.append(child)


class JsonDict(dict, JsonMaster):
    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)
        self._child_objects = []
        self._assign_childs()

    def _assign_childs(self) -> None:

        for key, value in self.items():

            if isinstance(value, list):
                child = JsonList(value)
                self.__setitem__(key, child)
            elif isinstance(value, dict):
                child = JsonDict(value)
                self.__setitem__(key, child)
            elif isinstance(value, str):
                child = JsonStr(value)
                self.__setitem__(key, child)
            elif isinstance(value, float):
                child = JsonFloat(value)
                self.__setitem__(key, child)
            elif isinstance(value, int):
                child = JsonInt(value)
                self.__setitem__(key, child)
            else:
                raise TypeError(f"Wrong data's format: {type(value)}")

            self._child_objects.append(child)
