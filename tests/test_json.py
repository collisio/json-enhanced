import json
import unittest

from base import (
    JSONBool,
    JSONCompose,
    JSONDict,
    JSONFloat,
    JSONInt,
    JSONList,
    JSONMaster,
    JSONNone,
    JSONObject,
    JSONSingleton,
    JSONStr,
)
from encoders import JSONObjectEncoder
from queryutils import QuerySet


class JsonTest(unittest.TestCase):
    def setUp(self):
        self.test1 = JSONObject(
            [
                {"Float": 2.3, "Int": 1, "Str": "string"},
                {"Dict": {"Float": 0.0, "List": [1, 2, 3]}},
            ]
        )
        self.test2 = JSONObject(True)
        self.test3 = JSONObject(
            {"List": [True, False], "Bool": True, "Dict": {"Float": 3.2}}
        )
        self.test4 = JSONObject(
            {"List": [0, 0.1, "str", None], "Dict": {"Bool": True, "None": None}}
        )

        self.test5 = JSONObject(
            [
                {
                    "Float": 1.1,
                    "Dict": {
                        "List": [{"Str": "string1", "List": [None, True, False, 1]}],
                        "Null": None,
                    },
                },
                {
                    "List": [{"Dict": {"Float": 1.2}, "Bool": True}],
                    "Dict": {"List": [None, {"Str": "string2"}]},
                },
            ]
        )

    def test_types(self):
        """Assert all child types are the correct ones"""

        self.assertIsInstance(self.test1, JSONList)
        self.assertIsInstance(self.test1[0], JSONDict)
        self.assertIsInstance(self.test1[0]["Float"], JSONFloat)
        self.assertIsInstance(self.test1[0]["Int"], JSONInt)
        self.assertIsInstance(self.test1[0]["Str"], JSONStr)
        self.assertIsInstance(self.test1[1], JSONDict)
        self.assertIsInstance(self.test1[1]["Dict"], JSONDict)
        self.assertIsInstance(self.test1[1]["Dict"]["Float"], JSONFloat)
        self.assertIsInstance(self.test1[1]["Dict"]["List"], JSONList)

        self.assertIsInstance(self.test3, JSONDict)
        self.assertIsInstance(self.test3["List"], JSONList)
        self.assertIsInstance(self.test3["List"][0], JSONBool)
        self.assertIsInstance(self.test3["List"][1], JSONBool)
        self.assertIsInstance(self.test3["Bool"], JSONBool)
        self.assertIsInstance(self.test3["Dict"], JSONDict)
        self.assertIsInstance(self.test3["Dict"]["Float"], JSONFloat)

        self.assertIsInstance(self.test4, JSONDict)
        self.assertIsInstance(self.test4["List"], JSONList)
        self.assertIsInstance(self.test4["List"][0], JSONInt)
        self.assertIsInstance(self.test4["List"][1], JSONFloat)
        self.assertIsInstance(self.test4["List"][2], JSONStr)
        self.assertIsInstance(self.test4["List"][3], JSONNone)
        self.assertIsInstance(self.test4["Dict"], JSONDict)
        self.assertIsInstance(self.test4["Dict"]["Bool"], JSONBool)
        self.assertIsInstance(self.test4["Dict"]["None"], JSONNone)

    def test_json_serializable(self):
        """Assert that the JSONObject is serializable"""

        self.assertEqual(
            json.dumps(self.test1).replace('"', "'"), self.test1.__repr__()
        )
        self.assertEqual(
            json.dumps(self.test2, cls=JSONObjectEncoder).replace('"', "'"),
            self.test2.__repr__().lower(),
        )
        self.assertEqual(
            json.dumps(self.test3, cls=JSONObjectEncoder).replace('"', "'"),
            self.test3.__repr__().replace("True", "true").replace("False", "false"),
        )

        self.assertEqual(
            json.dumps(self.test4, cls=JSONObjectEncoder),
            '{"List": [0, 0.1, "str", null], "Dict": {"Bool": true, "None": null}}',
        )

    def test_queries(self):

        self.assertEqual(
            self.test5.query(Float=1.2), QuerySet([JSONFloat(1.2)])
        )
        self.assertEqual(
            self.test5.query(Float__gt=1), QuerySet([JSONFloat(1.1), JSONFloat(1.2)])
        )
