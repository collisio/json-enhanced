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
    def test_methods(self):
        self.assertEqual(
            JSONStr(" - $4,312,555.52  ").to_float(), JSONFloat(-4312555.52)
        )
        self.assertEqual(
            JSONStr(" + $4,312,555.520  ").to_float(), JSONFloat(4312555.52)
        )
