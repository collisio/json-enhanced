from json import JSONEncoder
from base import JSONBool


class JSONObjectEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, JSONBool):
            return o._data
        return super().default(o)