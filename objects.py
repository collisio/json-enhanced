# ---- SINGLE OBJECTS ----
class JsonStr(str):
    pass


class JsonFloat(float):
    pass


class JsonInt(int):
    pass


# ---- COMPOUND OBJECTS ----


class JsonList(list):
    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)
        self._assign_types()

    def _assign_types(self) -> None:

        for i, item in enumerate(self):

            if isinstance(item, list):
                self.__setitem__(i, JsonList(item))
            elif isinstance(item, dict):
                self.__setitem__(i, JsonDict(item))
            elif isinstance(item, str):
                self.__setitem__(i, JsonStr(item))
            elif isinstance(item, float):
                self.__setitem__(i, JsonFloat(item))
            elif isinstance(item, int):
                self.__setitem__(i, JsonInt(item))
            else:
                raise TypeError(f"wrong data's format: {type(item)}")


class JsonDict(dict):
    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)
        self._assign_types()

    def _assign_types(self) -> None:

        for key, value in self.items():

            if isinstance(value, list):

                self.__setitem__(key, JsonList(value))

            elif isinstance(value, dict):

                self.__setitem__(key, JsonDict(value))

            elif isinstance(value, str):

                self.__setitem__(key, JsonStr(value))

            elif isinstance(value, float):

                self.__setitem__(key, JsonFloat(value))

            elif isinstance(value, int):

                self.__setitem__(key, JsonInt(value))

            else:

                raise TypeError(f"wrong data's format: {type(value)}")


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

            raise TypeError(f"wrong data's format: {type(data)}")
