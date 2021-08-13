"""This module provides json serializers for the json objects"""

from json import JSONEncoder


class JSONObjectEncoder(JSONEncoder):
    """
    We need this custom encoder in order to be able to use json.dumps on a JSONObject instance, due to the presence of JSONBool type,
    which is not JSON serializable
    """

    def default(self, o):
        from jsonutils.base import JSONBool, JSONNull

        if isinstance(o, (JSONBool, JSONNull)):
            return o._data
        return super().default(o)
