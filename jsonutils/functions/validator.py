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

    def _from_items(schema):
        pass

    errors = []

    def _recursive_traversing(schema, path=""):

        if not isinstance(schema, dict):
            return

        # if schema is a valid dict
        try:
            data_type = schema.pop("type")
        except KeyError:  # if key 'type' is not in this dict, schema must be a inner dict from items key
            _from_items(schema)
        else:
            # schema object is apparently a node dictionary,
            # but it could be an inner dictionary if the value of 'key' is itself a dictionary.
            object_type = type(data_type)
            if object_type is dict:  # this must be a inner key from items dict
                _from_items(schema)
            elif (
                object_type is int
            ):  # in this case it is already a singleton, "as expected".
                pass
            else:  # otherwise, schema will be invalid
                raise JSONSchemaError(f"Exception validating schema: {data_type}")

    is_valid_data = False if errors else True

    return is_valid_data, errors
