import unittest
from unittest.case import skip

import jsonutils as js
from jsonutils.base import JSONObject

# from jsonutils.functions.seekers import _choose_value, empty


@skip
class ChooseValueTest(unittest.TestCase):
    def setUp(self):
        self.node_str1 = JSONObject("string1")
        self.node_str2 = JSONObject("string2")
        self.node_null = JSONObject(None)
        self.node_bool = JSONObject(False)
        self.node_dict = JSONObject({"A": True})
        self.empty = empty

    def test_inner_join_overwritting_null(self):

        self.assertEqual(
            _choose_value(
                self.node_str1,
                self.node_str2,
                overwrite_with_null=True,
                merge_type="inner_join",
            ),
            self.node_str2,
        )
        self.assertEqual(
            _choose_value(
                self.node_str1,
                self.node_null,
                overwrite_with_null=True,
                merge_type="inner_join",
            ),
            self.node_null,
        )
        self.assertEqual(
            _choose_value(
                self.node_null,
                self.node_str1,
                overwrite_with_null=True,
                merge_type="inner_join",
            ),
            self.node_str1,
        )

        self.assertEqual(
            _choose_value(
                self.empty,
                self.node_str2,
                overwrite_with_null=True,
                merge_type="inner_join",
            ),
            self.empty,
        )
        self.assertEqual(
            _choose_value(
                self.node_bool,
                self.empty,
                overwrite_with_null=True,
                merge_type="inner_join",
            ),
            self.empty,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.empty,
                overwrite_with_null=True,
                merge_type="inner_join",
            ),
            self.empty,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.node_null,
                overwrite_with_null=True,
                merge_type="inner_join",
            ),
            self.empty,
        )

        self.assertRaisesRegex(
            TypeError,
            "First two arguments must be node or empty instances",
            lambda: _choose_value(
                self.node_str1,
                self.node_dict,
                overwrite_with_null=True,
                merge_type="inner_join",
            ),
        )

    def test_inner_join_non_overwritting_null(self):

        self.assertEqual(
            _choose_value(
                self.node_str1,
                self.node_str2,
                overwrite_with_null=False,
                merge_type="inner_join",
            ),
            self.node_str2,
        )
        self.assertEqual(
            _choose_value(
                self.node_str1,
                self.node_null,
                overwrite_with_null=False,
                merge_type="inner_join",
            ),
            self.node_str1,
        )
        self.assertEqual(
            _choose_value(
                self.node_null,
                self.node_str1,
                overwrite_with_null=False,
                merge_type="inner_join",
            ),
            self.node_str1,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.node_str2,
                overwrite_with_null=False,
                merge_type="inner_join",
            ),
            self.empty,
        )
        self.assertEqual(
            _choose_value(
                self.node_bool,
                self.empty,
                overwrite_with_null=False,
                merge_type="inner_join",
            ),
            self.empty,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.empty,
                overwrite_with_null=False,
                merge_type="inner_join",
            ),
            self.empty,
        )

    def test_outer_join_overwritting_null(self):

        self.assertEqual(
            _choose_value(
                self.node_str1,
                self.node_str2,
                overwrite_with_null=True,
                merge_type="outer_join",
            ),
            self.node_str2,
        )
        self.assertEqual(
            _choose_value(
                self.node_str1,
                self.node_null,
                overwrite_with_null=True,
                merge_type="outer_join",
            ),
            self.node_null,
        )
        self.assertEqual(
            _choose_value(
                self.node_null,
                self.node_str1,
                overwrite_with_null=True,
                merge_type="outer_join",
            ),
            self.node_str1,
        )

        self.assertEqual(
            _choose_value(
                self.empty,
                self.node_str2,
                overwrite_with_null=True,
                merge_type="outer_join",
            ),
            self.node_str2,
        )
        self.assertEqual(
            _choose_value(
                self.node_bool,
                self.empty,
                overwrite_with_null=True,
                merge_type="outer_join",
            ),
            self.node_bool,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.empty,
                overwrite_with_null=True,
                merge_type="outer_join",
            ),
            self.empty,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.node_null,
                overwrite_with_null=True,
                merge_type="outer_join",
            ),
            self.node_null,
        )

        self.assertRaisesRegex(
            TypeError,
            "First two arguments must be node or empty instances",
            lambda: _choose_value(
                self.node_str1,
                self.node_dict,
                overwrite_with_null=True,
                merge_type="outer_join",
            ),
        )

    def test_outer_join_non_overwritting_null(self):

        self.assertEqual(
            _choose_value(
                self.node_str1,
                self.node_str2,
                overwrite_with_null=False,
                merge_type="outer_join",
            ),
            self.node_str2,
        )
        self.assertEqual(
            _choose_value(
                self.node_str1,
                self.node_null,
                overwrite_with_null=False,
                merge_type="outer_join",
            ),
            self.node_str1,
        )
        self.assertEqual(
            _choose_value(
                self.node_null,
                self.node_str1,
                overwrite_with_null=False,
                merge_type="outer_join",
            ),
            self.node_str1,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.node_str2,
                overwrite_with_null=False,
                merge_type="outer_join",
            ),
            self.node_str2,
        )
        self.assertEqual(
            _choose_value(
                self.node_bool,
                self.empty,
                overwrite_with_null=False,
                merge_type="outer_join",
            ),
            self.node_bool,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.empty,
                overwrite_with_null=False,
                merge_type="outer_join",
            ),
            self.empty,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.node_null,
                overwrite_with_null=False,
                merge_type="outer_join",
            ),
            self.node_null,
        )

    def test_left_join_overwritting_null(self):

        self.assertEqual(
            _choose_value(
                self.node_str1,
                self.node_str2,
                overwrite_with_null=True,
                merge_type="left_join",
            ),
            self.node_str2,
        )
        self.assertEqual(
            _choose_value(
                self.node_str1,
                self.node_null,
                overwrite_with_null=True,
                merge_type="left_join",
            ),
            self.node_null,
        )
        self.assertEqual(
            _choose_value(
                self.node_null,
                self.node_str1,
                overwrite_with_null=True,
                merge_type="left_join",
            ),
            self.node_str1,
        )

        self.assertEqual(
            _choose_value(
                self.empty,
                self.node_str2,
                overwrite_with_null=True,
                merge_type="left_join",
            ),
            self.empty,
        )
        self.assertEqual(
            _choose_value(
                self.node_bool,
                self.empty,
                overwrite_with_null=True,
                merge_type="left_join",
            ),
            self.node_bool,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.empty,
                overwrite_with_null=True,
                merge_type="left_join",
            ),
            self.empty,
        )
        self.assertEqual(
            _choose_value(
                self.empty,
                self.node_null,
                overwrite_with_null=True,
                merge_type="left_join",
            ),
            self.empty,
        )

        self.assertRaisesRegex(
            TypeError,
            "First two arguments must be node or empty instances",
            lambda: _choose_value(
                self.node_str1,
                self.node_dict,
                overwrite_with_null=True,
                merge_type="left_join",
            ),
        )
