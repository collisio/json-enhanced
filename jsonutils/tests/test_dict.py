import unittest

from jsonutils.utils.dict import TranslationDict


class JsonTest(unittest.TestCase):
    def test_default_keys(self):

        test = TranslationDict(a=1, b=2)
        self.assertEqual(test["a"], 1)
        self.assertEqual(test["b"], 2)
        self.assertEqual(test["c"], "c")
        self.assertEqual(test[1], 1)
        self.assertEqual(test[object], object)

    def test_default_custom(self):

        test = TranslationDict({"a": 1, "b": 2, "in": 3}, default_="OK")
        self.assertEqual(test["a"], 1)
        self.assertEqual(test["b"], 2)
        self.assertEqual(test["in"], 3)
        self.assertEqual(test["c"], "OK")
        self.assertEqual(test[1], "OK")
        self.assertEqual(test[object], "OK")
