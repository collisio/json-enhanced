import unittest
from pathlib import Path
from unittest import skip

import jsonutils as js
from jsonutils.base import JSONDict, JSONNode, JSONObject
from jsonutils.exceptions import JSONPathException

BASE_PATH = Path(js.__file__).parent.resolve()


class JsonTest(unittest.TestCase):
    def test_dict_builds(self):
        path1 = [(("A", "B"), True), (("A", "C"), False)]

        path3 = [
            (("A",), 1),
            (("B", 0), 2),
            (("B", 1, "A"), True),
            (("B", 1, "B"), False),
        ]

        path6 = [
            (("A", 0, 0, "B"), "A/0/0/B"),
            (("A", 2, "A"), "A/2/A"),
            (("A", 1, "B", 0), "A/1/B/0"),
        ]
        path4 = [(("A", 1), 1), (("A", 0, 0), 2)]

        self.assertDictEqual(
            JSONObject.from_path(path1), {"A": {"B": True, "C": False}}
        )

        self.assertIsInstance(JSONObject.from_path(path1), JSONNode)

        self.assertDictEqual(
            JSONObject.from_path(path3), {"A": 1, "B": [2, {"A": True, "B": False}]}
        )
        self.assertDictEqual(
            JSONObject.from_path(path6),
            {"A": [[{"B": "A/0/0/B"}], {"B": ["A/1/B/0"]}, {"A": "A/2/A"}]},
        )
        self.assertDictEqual(JSONObject.from_path(path4), {"A": [[2], 1]})

    def test_list_builds(self):
        path1 = [
            ((0, "A"), 1),
            ((0, "B"), 2),
            ((1, "C"), 3),
            ((1, "D"), 4),
        ]
        path2 = [
            ((2, 3, 0), 1),
            ((0, "A", 1), 2),
            ((1,), "B"),
            ((2, 0), 20),
            ((2, 1), 21),
            ((2, 2), 22),
            ((0, "A", 0), 1),
            ((0, "A", 2), 3),
        ]
        path3 = [((1,), "A"), ((0, "B"), "B")]
        self.assertListEqual(
            JSONObject.from_path(path1), [{"A": 1, "B": 2}, {"C": 3, "D": 4}]
        )
        self.assertListEqual(
            JSONObject.from_path(path2), [{"A": [1, 2, 3]}, "B", [20, 21, 22, [1]]]
        )
        self.assertListEqual(JSONObject.from_path(path3), [{"B": "B"}, "A"])

    def test_fail_path_builds(self):
        path1 = [(("A",), 1), (("A", "B"), 1)]  # incompatible paths
        path2 = [(("A", "B"), 1), (("A",), 1)]  # incompatible paths
        path3 = [(("A", 0), 1), (("A", 2), 2)]  # not a connected list
        path4 = [(("A",), 1), ((0,), 1)]  # incompatible root structure
        path5 = {
            (1, 2): "A",
            (1, "A"): "B",
            (0,): "C",
        }  # assign an incompatible key
        path6 = {(0, 0, 0): 1, (0, 0): 2}
        path7 = {("A", "A"): 1, ("A", 0): 2}
        path8 = {(0, "A"): 1, (0, 0): 2}
        for path in (path1, path2, path3, path4, path5, path6, path7, path8):
            self.assertRaisesRegex(
                JSONPathException,
                "node structure is incompatible",
                lambda: JSONObject.from_path(path),
            )

    def test_to_from_path(self):
        test = JSONObject.open(BASE_PATH / "tests/balance-sheet-example-test.json")
        self.assertDictEqual(
            test.json_decode, JSONObject.from_path(test.to_path()).json_decode
        )
