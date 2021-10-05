from jsonutils.base import JSONObject
from jsonutils.exceptions import JSONSchemaError


def _validate_data(json_object, schema):
    # TODO review this and complete
    """
    Example of a schema dict
    {
        "type": Dict,
        "items": {
            "name": {
                "type": Str | Null,
                "contains": "a"
            },
            "team": {
                "type": ListDict | Null,
                "length": 2,
                "items": {
                    "name": {
                        "type": Str | Null
                    },
                    "age": {
                        "type": Int
                    },
                    "birth": {
                        "type": Datetime | Null
                    }
                }
            }
        }
    }
    """
    pass
