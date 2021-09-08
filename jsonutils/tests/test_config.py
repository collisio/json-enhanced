import unittest

import jsonutils as js
from jsonutils.base import JSONBool, JSONDict, JSONList, JSONNull


class JsonTest(unittest.TestCase):
    def setUp(self):
        js.config.native_types = False
        js.config.query_exceptions = False

    def test_native_types(self):
        test = js.JSONObject(
            {"A": True, "B": None, "D": dict(A=True, B=None), "L": [1, 2]}
        )
        self.assertIsInstance(test.get(A=js.All), JSONBool)
        self.assertIsInstance(test.get(B=js.All), JSONNull)
        self.assertIsInstance(test.get(D=js.All), JSONDict)
        self.assertIsInstance(test.get(L=js.All), JSONList)

        js.config.native_types = True

        self.assertIsInstance(test.get(A=js.All), bool)
        self.assertIsInstance(test.get(B=js.All), type(None))
        self.assertIsInstance(test.get(D=js.All), dict)
        self.assertIsInstance(test.get(L=js.All), list)

        self.assertIsInstance(test.query(A=js.All).first(), bool)
        self.assertIsInstance(test.query(A=js.All).last(), bool)
        self.assertIsInstance(test.query(B=js.All).first(), type(None))
        self.assertIsInstance(test.query(B=js.All).last(), type(None))
