import unittest
from unittest.case import skip

import jsonutils as js
from jsonutils.base import JSONObject


class SingleQueryTest(unittest.TestCase):
    def test_bool_query(self):
        test = JSONObject(
            {
                "True": 1,
                "Comp": [
                    {"True": 1, "False": 0},
                    {"True": "0", "False": ()},
                    {"True": (0,), "False": []},
                    {"True": " ", "False": {}},
                    {"True": True, "False": False},
                    {"True": [0], "False": None},
                ],
            }
        )
        self.assertListEqual(
            test.query(True__bool=True).jsonpaths(),
            [
                "True",
                "Comp/0/True",
                "Comp/1/True",
                "Comp/2/True",
                "Comp/3/True",
                "Comp/4/True",
                "Comp/5/True",
            ],
        )
        self.assertListEqual(
            test.query(False__bool=False).jsonpaths(),
            [
                "Comp/0/False",
                "Comp/1/False",
                "Comp/2/False",
                "Comp/3/False",
                "Comp/4/False",
                "Comp/5/False",
            ],
        )
