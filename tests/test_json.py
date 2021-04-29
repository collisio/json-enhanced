import unittest
from base import (
    JSONCompose,
    JSONDict,
    JSONFloat,
    JSONInt,
    JSONList,
    JSONMaster,
    JSONObject,
    JSONSingleton,
    JSONStr,
)


class JsonTest(unittest.TestCase):

    def test_types(self):
        """Assert all child types are the correct ones"""
        test1 = JSONObject(
            [
                {
                    "Float": 2.3,
                    "Int": 1,
                    "Str": "string"
                },
                {
                    "Dict": {
                        "Float": 0.,
                        "List": [1,2,3]
                    }
                }
            ]
        )

        self.assertIsInstance(test1, JSONList)
        self.assertIsInstance(test1[0], JSONDict)
        self.assertIsInstance(test1[0]["Float"], JSONFloat)
        self.assertIsInstance(test1[0]["Int"], JSONInt)
        self.assertIsInstance(test1[0]["Str"], JSONStr)

        self.assertIsInstance(test1[1], JSONDict)
        self.assertIsInstance(test1[1]["Dict"], JSONDict)
        self.assertIsInstance(test1[1]["Dict"]["Float"], JSONFloat)
        self.assertIsInstance(test1[1]["Dict"]["List"], JSONList)