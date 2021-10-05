from jsonutils.exceptions import JSONSchemaError
from jsonutils.utils.dict import UUIDdict


class SchemaSwitcher:
    """
    The task of this object is to guess which type of schema the data entered as an argument follows.
    """

    # #TODO review this
    def __new__(cls, data):
        if not isinstance(data, dict):
            raise JSONSchemaError(
                f"Wrong data type in schema. data must be a dict, not {type(data)}. {data}"
            )

        # decide what kind of schema this data belongs to
        return SchemaSwitcher._decide_schema(data)

    def _decide_schema(data):

        try:
            data_type = data.pop("type")
        except KeyError:
            # if key 'type' is not in this dict, schema must be a inner dict from items key
            return SchemaItemsDict(data)
        else:
            # schema object is apparently a SchemaNodeDict,
            # but it could be a SchemaItemsDict if the value of 'type' key is itself a dictionary.
            if isinstance(data_type, dict):
                return SchemaItemsDict(data)
            elif isinstance(data_type, int):  # in this case must be a SchemaNodeDict
                schema = SchemaNodeDict(
                    data_type,
                    required=data.pop("required", None),
                    actions=data.pop("actions", None),
                    items=data.pop("items", None),
                )
                if data:
                    # If there are still items in the dictionary, the schema is invalid because all valid keys have been used and deleted.
                    raise JSONSchemaError(
                        f"Exception validating schema: unknown key in {data}"
                    )
                return schema
            else:
                raise JSONSchemaError(f"Exception validating schema: {data_type}")


class SchemaBase:
    def __init__(self, *args, **kwargs):
        self._child_objects = UUIDdict()


class SchemaNodeDict(SchemaBase):
    """
    keys
    ----
        type: the type of current schema node (Dict, List, Str, Float, Int, Datetime, Bool, Null)
        required: if current schema node needs to be present in json, regardless of its value (e.g.: null)

    Schema
    ------

    {
        "type": Type1 | Type2 | Type3,
        "actions": {
            "contains": 1,
            "length__gt": 3,
        },
        "items": {
            "item1": {
                "type": Type1 | Type2,
                "required": True,
            }
        }
    }
    """

    def __init__(self, type_, required=False, actions=None, items=None):

        # validate args
        self._validate_args(required, actions, items)

        self.type_ = type_
        self.required = required
        self.actions = actions
        self.items = items

        super().__init__()

    def _validate_args(self, required, actions, items):
        if not isinstance(required, bool):
            raise JSONSchemaError(
                f"Exception validating schema. Argument 'required' must be a bool, not {type(required)}"
            )
        if not isinstance(actions, (dict, type(None))):
            raise JSONSchemaError(
                f"Exception validating schema. Argument 'actions' must be a dict, not {type(actions)}"
            )
        if not isinstance(items, (dict, type(None))):
            raise JSONSchemaError(
                f"Exception validating schema. Argument 'items' must be a dict, not {type(items)}"
            )


class SchemaItemsDict(dict, SchemaBase):
    """
    Schema
    ------

    {
        "item1": {
            "type": Type1 | Type2,
            "required": False,
            "action": {
                "gte": 2
            }
        }
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        SchemaBase.__init__(self, *args, **kwargs)
