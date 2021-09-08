import unittest
from jsonutils.base import JSONObject
import jsonutils as js


class JsonTest(unittest.TestCase):
    def test_sum(self):
        test = JSONObject(
            [
                {"name": "Paul", "age": 28},
                {"name": "Greece", "age": 22},
                {"name": "Val", "age": None},
            ]
        )

        self.assertEqual(test.query(age__in=(28, "22")).sum(), 50)
        self.assertEqual(test.query(age=js.All).sum(), 50)
        self.assertEqual(test.query(age__gt=25).sum(), 28)
        self.assertIsNone(test.query(age="fake").sum())
