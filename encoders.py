from json import JSONEncoder
from base import JSONBool


class JSONObjectEncoder(JSONEncoder):
    """
    We need this custom encoder in order to be able to use json.dumps on a JSONObject instance, due to the presence of JSONBool type,
    which is not JSON serializable
    """
    
    def default(self, o):
        if isinstance(o, JSONBool):
            return o._data
        return super().default(o)