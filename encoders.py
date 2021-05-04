from json import JSONEncoder


class JSONObjectEncoder(JSONEncoder):
    """
    We need this custom encoder in order to be able to use json.dumps on a JSONObject instance, due to the presence of JSONBool type,
    which is not JSON serializable
    """

    def default(self, o):
        from base import JSONBool, JSONNone

        if isinstance(o, (JSONBool, JSONNone)):
            return o._data
        return super().default(o)
