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
        self.test1 = JSONStr(" - $4,312,555.52  ")

    def test_methods(self):
        self.assertEqual(self.test1.to_float(), JSONFloat(-4312555.52))