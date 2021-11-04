import unittest

from jsonutils.functions.seekers import DefaultDict, DefaultList
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

    def test_default_dict(self):
        test1 = DefaultDict()
        test2 = DefaultDict()

        test1["A"][0]["B"] = "A/0/B"
        self.assertDictEqual(test1, {"A": [{"B": "A/0/B"}]})

        test1["A"][1] = "A/1"
        self.assertDictEqual(test1, {"A": [{"B": "A/0/B"}, "A/1"]})

        self.assertRaisesRegex(
            Exception, "is already registered", lambda: test1["A"].__setitem__(0, 1)
        )
        self.assertRaisesRegex(
            Exception,
            "'str' object has no attribute '__setitem__'",
            lambda: test1["A"][1].__setitem__("A", 1),
        )

        test2["A"] = None
        self.assertDictEqual(test2, {"A": None})

    def test_default_list(self):
        test1 = DefaultList()
        test2 = DefaultList()

        test1[2][3][0] = 1
        test1[0]["A"][1] = 2

        self.assertEqual(test1[2][3][0], 1)
        self.assertEqual(test1[0]["A"][1], 2)

        test2[0] = None
        self.assertListEqual(test2, [None])
