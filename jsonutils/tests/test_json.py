import json
import re
import unittest
from datetime import datetime
from pathlib import Path

import jsonutils as js
import pytz
from jsonutils.base import (
    JSONBool,
    JSONCompose,
    JSONDict,
    JSONFloat,
    JSONInt,
    JSONList,
    JSONNode,
    JSONNull,
    JSONObject,
    JSONPath,
    JSONSingleton,
    JSONStr,
    JSONUnknown,
)
from jsonutils.encoders import JSONObjectEncoder
from jsonutils.exceptions import JSONQueryException, JSONQueryMultipleValues
from jsonutils.query import All, ExtractYear, QuerySet, SingleQuery, ValuesList

BASE_PATH = Path(js.__file__).parent.resolve()


class JsonTest(unittest.TestCase):
    def setUp(self):

        js.config.native_types = False
        js.config.query_exceptions = True

        self.test1 = JSONObject(
            [
                {"Float": 2.3, "Int": 1, "Str": "string"},
                {"Dict": {"Float": 0.0, "List": [1, 2, 3]}},
            ]
        )
        self.test2 = JSONObject(True)
        self.test3 = JSONObject(
            {"List": (True, False), "Bool": True, "Dict": {"Float": 3.2}}
        )
        self.test4 = JSONObject(
            {"List": [0, 0.1, "str", None], "Dict": {"Bool": True, "None": None}}
        )

        self.test5 = JSONObject(
            [
                {
                    "Float": 1.1,
                    "Dict": {
                        "List": [{"Str": "string1", "List": [None, True, False, 1]}],
                        "Null": None,
                    },
                },
                {
                    "List": [{"Dict": {"Float": "1.2"}, "Bool": True}],
                    "Dict": {"List": [None, {"Str": "string2"}]},
                },
                {"Datetime": "2021-05-01", "Dict": {"Datetime": "2021/06/01"}},
            ]
        )

        self.test6 = JSONObject(
            {
                "position_data": [
                    {"text": "dummy text 1", "pos": [1, 2]},
                    {"text": "dummy text 2", "pos": [3, 2]},
                    {"text": "dummy text 3", "pos": [1, 4]},
                    {"text": "dummy text 4", "pos": [2, 5]},
                    {"text": "dummy text 5", "pos": [4, 1]},
                    {"text": "dummy text 6", "pos": [1, 1, 5]},
                ],
                "timestamp_data": [
                    {"value": 523687, "timestamp": "2021-05-01 08:00:00"},
                    {"value": 523689, "timestamp": "2021-05-01 09:00:00"},
                    {"value": 523787, "timestamp": "2021-05-02 08:30:00"},
                    {"value": 525687, "timestamp": "2021-05-05 18:00:25"},
                ],
                "boolean_data": [
                    {"data": [True, 1]},
                    {"data": [False, None]},
                    {"data": [0, 1]},
                    {"data": (False, True)},
                ],
            }
        )

        self.test7 = JSONObject(
            {
                "candidatos": [
                    {
                        "Nombre completo": "Fhànçaömá",
                        "Pasión": "Música",
                        "€uros": 356.3,
                    },
                    {"Nombre completo": "Üm€", "Pasión": "Comida", "€€": "28.36K €"},
                ]
            }
        )

        self.test8 = JSONObject(
            {
                "data_list": [
                    {"name": "", "id": 0, "list": [], "tuple": (), "none": None},
                    {},
                ],
                "list": [0, 1, 2],
            }
        )

    def test_unknown_types(self):
        test = JSONObject({"data": {"datetime": datetime(2021, 1, 1, 0, 0, 0)}})
        test2 = JSONObject({"data": object})

        self.assertEqual(test.data.datetime, JSONStr("2021-01-01T00:00:00"))
        self.assertTrue(test.check_valid_types())
        self.assertIsInstance(test2.data, JSONUnknown)
        self.assertEqual(
            test2.check_valid_types(),
            (False, [{"data": {"path": "data/", "type": type}}]),
        )

    def test_types(self):
        """Assert all child types are the correct ones"""

        self.assertIsInstance(self.test1, JSONList)
        self.assertIsInstance(self.test1[0], JSONDict)
        self.assertIsInstance(self.test1[0]["Float"], JSONFloat)
        self.assertIsInstance(self.test1[0]["Int"], JSONInt)
        self.assertIsInstance(self.test1[0]["Str"], JSONStr)
        self.assertIsInstance(self.test1[1], JSONDict)
        self.assertIsInstance(self.test1[1]["Dict"], JSONDict)
        self.assertIsInstance(self.test1[1]["Dict"]["Float"], JSONFloat)
        self.assertIsInstance(self.test1[1]["Dict"]["List"], JSONList)

        self.assertIsInstance(self.test3, JSONDict)
        self.assertIsInstance(self.test3["List"], JSONList)
        self.assertIsInstance(self.test3["List"][0], JSONBool)
        self.assertIsInstance(self.test3["List"][1], JSONBool)
        self.assertIsInstance(self.test3["Bool"], JSONBool)
        self.assertIsInstance(self.test3["Dict"], JSONDict)
        self.assertIsInstance(self.test3["Dict"]["Float"], JSONFloat)

        self.assertIsInstance(self.test4, JSONDict)
        self.assertIsInstance(self.test4["List"], JSONList)
        self.assertIsInstance(self.test4["List"][0], JSONInt)
        self.assertIsInstance(self.test4["List"][1], JSONFloat)
        self.assertIsInstance(self.test4["List"][2], JSONStr)
        self.assertIsInstance(self.test4["List"][3], JSONNull)
        self.assertIsInstance(self.test4["Dict"], JSONDict)
        self.assertIsInstance(self.test4["Dict"]["Bool"], JSONBool)
        self.assertIsInstance(self.test4["Dict"]["None"], JSONNull)

    def test_append_method(self):

        test1 = self.test1.copy()
        test2 = self.test5.copy()

        test1.append({"fake": True})
        test2.append(test1._1.Dict.List, serialize_nodes=True)

        self.assertEqual(test2[-1], test1._1.Dict.List)
        self.assertNotEqual(test2[-1]._0.jsonpath, test1._1.Dict.List._0.jsonpath)
        self.assertEqual(test2[-1]._0.jsonpath, "3/0/")

        test2.append(test1._1.Dict.List, serialize_nodes=False)
        # if not serializing nodes, the new appended jsonpath will not match the path within test2 jsonobject
        self.assertEqual(test2[-1], test1._1.Dict.List)
        self.assertEqual(test2[-1]._0.jsonpath, test1._1.Dict.List._0.jsonpath)

        self.assertIsInstance(test1, JSONList)
        self.assertIsInstance(test1[0], JSONDict)
        self.assertIsInstance(test1[0]["Float"], JSONFloat)
        self.assertIsInstance(test1[0]["Int"], JSONInt)
        self.assertIsInstance(test1[0]["Str"], JSONStr)
        self.assertIsInstance(test1[1], JSONDict)
        self.assertIsInstance(test1[1]["Dict"], JSONDict)
        self.assertIsInstance(test1[1]["Dict"]["Float"], JSONFloat)
        self.assertIsInstance(test1[1]["Dict"]["List"], JSONList)
        self.assertIsInstance(test1[2], JSONDict)
        self.assertIsInstance(test1[2]["fake"], JSONBool)

        self.assertEqual(test1[0].parent, test1)
        self.assertEqual(test1[1].parent, test1)
        self.assertEqual(test1[2].parent, test1)

        self.assertEqual(test1[0]._index, 0)
        self.assertEqual(test1[1]._index, 1)
        self.assertEqual(test1[2]._index, 2)

        self.assertEqual(test1[0]["Float"]._key, "Float")
        self.assertEqual(test1[2]["fake"]._key, "fake")
        self.assertEqual(test1[2]["fake"].jsonpath, JSONPath("2/fake/"))

        self.assertTrue(test1.query(fake=True).exists())
        self.assertEqual(test1.query_key(".*ak.*").keys().first(), "fake")

    def test_list_set_items(self):

        test1 = self.test1.copy()

        test1[1] = ["A", {"B": None}]

        self.assertIsInstance(test1, JSONList)
        self.assertIsInstance(test1[0], JSONDict)
        self.assertIsInstance(test1[0]["Float"], JSONFloat)
        self.assertIsInstance(test1[0]["Int"], JSONInt)
        self.assertIsInstance(test1[0]["Str"], JSONStr)
        self.assertIsInstance(test1[1], JSONList)
        self.assertIsInstance(test1[1][0], JSONStr)
        self.assertIsInstance(test1[1][1], JSONDict)
        self.assertIsInstance(test1[1][1]["B"], JSONNull)

    def test_dict_set_items(self):

        test3 = self.test3.copy()

        test3["new_key"] = {"key": [None, "None"]}

        self.assertIsInstance(test3, JSONDict)
        self.assertIsInstance(test3["List"], JSONList)
        self.assertIsInstance(test3["List"][0], JSONBool)
        self.assertIsInstance(test3["List"][1], JSONBool)
        self.assertIsInstance(test3["Bool"], JSONBool)
        self.assertIsInstance(test3["Dict"], JSONDict)
        self.assertIsInstance(test3["Dict"]["Float"], JSONFloat)
        self.assertIsInstance(test3["new_key"], JSONDict)
        self.assertIsInstance(test3["new_key"]["key"], JSONList)
        self.assertIsInstance(test3["new_key"]["key"][0], JSONNull)
        self.assertIsInstance(test3["new_key"]["key"][1], JSONStr)

        self.assertEqual(test3["List"].parent, test3)
        self.assertEqual(test3["Bool"].parent, test3)
        self.assertEqual(test3["new_key"].parent, test3)
        self.assertEqual(test3["new_key"]["key"].parent, test3["new_key"])
        self.assertEqual(test3["new_key"]["key"][0].parent, test3["new_key"]["key"])

        self.assertEqual(
            test3["new_key"]["key"][0].jsonpath, JSONPath("new_key/key/0/")
        )

    def test_keys(self):
        """
        Check that all nodes coming directly from dictionary keys have their corresponding key associated with them.
        """

        # Nodes coming from a list do not have an associated key, but an "index" attribute.
        self.assertEqual(self.test1[0]._key, None)
        self.assertEqual(self.test1[1]._key, None)
        self.assertEqual(self.test1[0]._index, 0)
        self.assertEqual(self.test1[1]._index, 1)
        # --------------------------------------------------------------------------------
        self.assertEqual(self.test1[0]["Float"]._key, "Float")
        self.assertEqual(self.test1[0]["Int"]._key, "Int")
        self.assertEqual(self.test1[0]["Str"]._key, "Str")
        self.assertEqual(self.test1[1]["Dict"]._key, "Dict")
        self.assertEqual(self.test1[1]["Dict"]["Float"]._key, "Float")
        self.assertEqual(self.test1[1]["Dict"]["List"]._key, "List")

    def test_parents(self):
        """Check every child object has the right parent object"""

        # the parent of the root node must be None
        self.assertEqual(self.test1.parent, None)

        # the parent of both two list elements must be the list itself
        self.assertEqual(
            self.test1[0].parent,
            JSONList(
                [
                    {"Float": 2.3, "Int": 1, "Str": "string"},
                    {"Dict": {"Float": 0.0, "List": [1, 2, 3]}},
                ]
            ),
        )
        self.assertEqual(
            self.test1[1].parent,
            JSONList(
                [
                    {"Float": 2.3, "Int": 1, "Str": "string"},
                    {"Dict": {"Float": 0.0, "List": [1, 2, 3]}},
                ]
            ),
        )
        # -----------------------------------------
        self.assertEqual(
            self.test1[0]["Float"].parent,
            JSONDict({"Float": 2.3, "Int": 1, "Str": "string"}),
        )
        self.assertEqual(
            self.test1[1]["Dict"].parent,
            JSONDict({"Dict": {"Float": 0.0, "List": [1, 2, 3]}}),
        )
        self.assertEqual(
            self.test1[1]["Dict"]["Float"].parent,
            JSONDict({"Float": 0.0, "List": [1, 2, 3]}),
        )
        self.assertEqual(
            self.test1[1]["Dict"]["List"].parent,
            JSONDict({"Float": 0.0, "List": [1, 2, 3]}),
        )
        self.assertEqual(
            self.test1[1]["Dict"]["List"][0].parent,
            JSONList([1, 2, 3]),
        )
        self.assertEqual(
            self.test1[1]["Dict"]["List"][1].parent,
            JSONList([1, 2, 3]),
        )

    def test_roots_in_queryset(self):
        self.assertEqual(self.test6.query(data__1=True)._root, self.test6)
        self.assertEqual(
            self.test6.position_data.query(pos__1="44")._root, self.test6.position_data
        )

    def test_root(self):
        """
        Verify that any child nodes within the json structure share the same unique root
        """
        self.assertEqual(self.test6.position_data._0.root, self.test6)
        self.assertEqual(self.test6.position_data._1.root, self.test6)
        self.assertEqual(self.test6.root, self.test6)

    def test_paths(self):

        self.assertEqual(
            self.test1.query(List__contains=2).first().jsonpath,
            JSONPath("1/Dict/List/"),
        )
        self.assertEqual(
            self.test1.query(List__contains=2).first().jsonpath.expr,
            '[1]["Dict"]["List"]',
        )

    def test_json_serializable(self):
        """Assert that the JSONObject is serializable"""

        self.assertEqual(
            json.dumps(self.test1).replace('"', "'"), self.test1.__repr__()
        )
        self.assertEqual(
            json.dumps(self.test2, cls=JSONObjectEncoder).replace('"', "'"),
            self.test2.__repr__().lower(),
        )
        self.assertEqual(
            json.dumps(self.test3, cls=JSONObjectEncoder).replace('"', "'"),
            self.test3.__repr__().replace("True", "true").replace("False", "false"),
        )

        self.assertEqual(
            json.dumps(self.test4, cls=JSONObjectEncoder),
            '{"List": [0, 0.1, "str", null], "Dict": {"Bool": true, "None": null}}',
        )

    def test_get(self):
        test = self.test6
        test2 = self.test1

        self.assertEqual(
            test.get(timestamp="2021-05-01 08:00:00"),
            test.query(timestamp="2021-05-01 08:00:00").first(),
        )

        self.assertRaises(JSONQueryMultipleValues, lambda: test.get(pos__0=1))

        self.assertEqual(test2.get(Float=2.3), test2.query(Float="2.3").first())
        self.assertRaises(JSONQueryMultipleValues, lambda: test2.get(Float__gt="-1"))
        self.assertRaises(JSONQueryException, lambda: test2.get(Float__gt="-1"))

        self.assertRaisesRegex(
            JSONQueryException,
            "The query has not returned any result",
            lambda: test.get(timestamp="1895-01-01"),
        )

    def test_queries(self):

        test = JSONObject.open(BASE_PATH / "tests/balance-sheet-example-test.json")

        # check isnull query
        self.assertEqual(JSONObject(dict(A=True)).query(A__isnull=True), [])
        self.assertEqual(JSONObject(dict(A=True)).query(A__isnull=False), [True])
        self.assertEqual(JSONObject(dict(A=False)).query(A__isnull=True), [])
        self.assertEqual(JSONObject(dict(A=False)).query(A__isnull=False), [False])
        # ------------------
        self.assertEqual(self.test3.query(fakke="true").first(), JSONNull(None))
        self.assertEqual(self.test3.query(fakke="true").last(), JSONNull(None))
        self.assertEqual(self.test3.query(Bool="true"), [JSONBool(True)])
        self.assertEqual(self.test3.query(Bool__type=str), [])
        self.assertEqual(self.test3.query(Bool__type="str"), [])
        self.assertEqual(self.test3.query(Bool__type=bool), [JSONBool(True)])
        self.assertEqual(self.test3.query(Bool__type="bool"), [JSONBool(True)])
        self.assertEqual(self.test4.query(None__type=None), [JSONNull(None)])
        self.assertEqual(self.test4.query(None__type="None"), [JSONNull(None)])
        self.assertEqual(self.test5.query(Str__type="str"), ["string1", "string2"])
        self.assertEqual(self.test5.query(Str__type="None"), [])
        self.assertEqual(self.test5.query(Str__length=7), ["string1", "string2"])
        self.assertEqual(self.test5.query(Str__length=0), [])
        self.assertEqual(self.test5.query(Str__startswith="st"), ["string1", "string2"])
        self.assertEqual(self.test5.query(Str__startswith="fake"), [])
        self.assertEqual(self.test5.query(Str__endswith=1), ["string1"])
        self.assertEqual(self.test5.query(Str__endswith=2), ["string2"])
        self.assertEqual(self.test5.query(Str__endswith=3), [])
        self.assertEqual(self.test5.query(Str__endswith=(1, 2)), ["string1", "string2"])
        self.assertEqual(
            self.test5.query(Str__endswith=(1, "2")), ["string1", "string2"]
        )
        self.assertEqual(
            self.test5.query(Str__endswith=["1", 2]), ["string1", "string2"]
        )
        self.assertEqual(
            self.test5.query(Str__endswith=["1", "2"]), ["string1", "string2"]
        )
        self.assertEqual(
            self.test5.query(Str__type="singleton"), ["string1", "string2"]
        )
        self.assertEqual(
            self.test5.query(Datetime__type=datetime), self.test5.query(Datetime=All)
        )
        self.assertRaises(JSONQueryException, lambda: self.test5.query(Str__length="1"))
        self.assertEqual(
            self.test3.query(List__contains=True), [[JSONBool(True), JSONBool(False)]]
        )
        self.assertEqual(
            self.test1.query(Dict__contains=["Float", "List"]).last(),
            {"Float": 0.0, "List": [1, 2, 3]},
        )
        self.assertEqual(
            self.test4.query(Dict__in=("Bool", "None", "Other")),
            [{"Bool": True, "None": None}],
        )
        self.assertEqual(
            self.test4.query(Dict__in=("Bool", "Other")),
            [],
        )
        self.assertEqual(
            self.test4.query(List__in=("0", "0.1", "str", None)),
            [[0, 0.1, "str", None]],
        )
        self.assertEqual(
            self.test5.query(Bool__contains=True),
            [True],
        )
        self.assertEqual(self.test5.query(Float=1.2), QuerySet([JSONStr(1.2)]))
        self.assertEqual(
            self.test5.query(Float__gt=1), QuerySet([JSONFloat(1.1), JSONStr(1.2)])
        )
        self.assertEqual(self.test5.query(Float__gt=2), QuerySet())
        self.assertEqual(self.test5.query(Str__exact="string2"), QuerySet(["string2"]))
        self.assertEqual(
            self.test5.query(List=[None, True, False, 1], include_parent_=True),
            [JSONDict({"Str": "string1", "List": [None, True, False, 1]})],
        )
        self.assertEqual(
            self.test5.query(Str__exact="string2", include_parent_=True),
            [{"Str": "string2"}],
        )
        self.assertEqual(
            self.test5.query(List__0__contains=("Dict", "Bool")),
            [[{"Dict": {"Float": "1.2"}, "Bool": True}]],
        )
        self.assertEqual(
            self.test5.query(List__0__contains="Str"),
            [[{"Str": "string1", "List": [None, JSONBool(True), False, 1]}]],
        )
        self.assertEqual(
            self.test5.query(Datetime__gt="2021-05-01"), QuerySet(["2021/06/01"])
        )
        self.assertEqual(
            self.test5.query(Datetime__contains="2021-05"),
            QuerySet([JSONStr("2021-05-01")]),
        )
        self.assertEqual(
            self.test5.query(List__parent__contains="Str"),
            [
                [JSONNull(None), JSONBool(True), JSONBool(False), 1],
            ],
        )
        self.assertEqual(
            self.test6.query(
                timestamp__gt="2021-05-01 08:30:00",
                timestamp__lte="2021-05-02 08:30:00",
                include_parent_=True,
            ),
            [
                {"value": 523689, "timestamp": "2021-05-01 09:00:00"},
                {"value": 523787, "timestamp": "2021-05-02 08:30:00"},
            ],
        )
        self.assertEqual(self.test6.query(pos__0__gte=2), [[3, 2], [2, 5], [4, 1]])
        self.assertEqual(
            self.test6.query(pos__2__gt=2, include_parent_=True),
            [{"text": "dummy text 6", "pos": [1, 1, 5]}],
        )
        self.assertEqual(self.test6.query(pos__5__gte=2), [])
        self.assertEqual(
            self.test6.query(pos__0__gte=2, pos__1__lt=5), [[3, 2], [4, 1]]
        )
        self.assertEqual(
            self.test6.query(pos__1__in=(1, 4), include_parent_=True),
            [
                {"text": "dummy text 3", "pos": [1, 4]},
                {"text": "dummy text 5", "pos": [4, 1]},
                {"text": "dummy text 6", "pos": [1, 1, 5]},
            ],
        )
        self.assertEqual(self.test8.query(list__isnull=True), QuerySet([[]]))
        self.assertEqual(self.test8.query(tuple__isnull=True), QuerySet([[]]))
        self.assertEqual(self.test8.query(none__isnull=True), QuerySet([None]))
        self.assertEqual(self.test8.query(id__isnull=True), QuerySet())
        self.assertEqual(self.test6.query(data__1=True), QuerySet([[False, True]]))

        self.assertListEqual(
            test.query(
                filing_date__isnull=False, filing_date__notpath="all_company_filings"
            )
            .order_by("-filing_date")
            .values(date="filing_date", form_type="form_type", url="form_url"),
            [
                {"date": "2017-09-27", "form_type": "1-A/A", "url": None},
                {"date": "2017-09-06", "form_type": "1-A", "url": None},
            ],
        )

    def test_multiqueries(self):
        test = JSONObject(
            [
                {
                    "data": {
                        "data": [
                            1,
                            2,
                            {"data": 1, "date": "2021/08/01  12:00:00Z"},
                            {"data": {"data": 1, "date": "2021-08-02"}},
                        ],
                        "date": "2021/08/01  13:00:00.003Z",
                    },
                    "date": datetime(2021, 9, 8),
                }
            ]
        )

        self.assertEqual(
            self.test6.query(
                text__regex=r"(?:2|5)", pos__0__gte=2, include_parent_=True
            ),
            [
                {"text": "dummy text 2", "pos": [3, 2]},
                {"text": "dummy text 5", "pos": [4, 1]},
            ],
        )

        self.assertEqual(
            test.query(data=1, date__gte=datetime(2021, 8, 1), include_parent_=True),
            [
                {"data": 1, "date": "2021/08/01  12:00:00Z"},
                {"data": 1, "date": "2021-08-02"},
            ],
        )
        self.assertEqual(
            test.query(data__c_data__contains=1),
            [
                {
                    "data": [
                        1,
                        2,
                        {"data": 1, "date": "2021/08/01  12:00:00Z"},
                        {"data": {"data": 1, "date": "2021-08-02"}},
                    ],
                    "date": "2021/08/01  13:00:00.003Z",
                },
                {"data": 1, "date": "2021-08-02"},
            ],
        )
        self.assertEqual(
            test.annotate(date=None).query(
                data__c_data__contains=1, date__isnull=True, include_parent_=True
            ),
            [{"data": {"data": 1, "date": "2021-08-02"}, "date": None}],
        )

    def test_queries_traversing(self):

        test = self.test6

        self.assertListEqual(
            test.query(
                data__parent__parent__0__c_data__1__exact="1", include_parent_=True
            ),
            [
                {"data": [True, 1]},
                {"data": [False, None]},
                {"data": [0, 1]},
                {"data": [False, True]},
            ],
        )
        self.assertEqual(
            test.query(
                timestamp__lte="2021-05-01T23:59:00",
                timestamp__parent__c_value__contains=89,
                include_parent_=True,
            ),
            [{"value": 523689, "timestamp": "2021-05-01 09:00:00"}],
        )

    def test_single_query_exact(self):

        test_dict = JSONObject({"A": {"A": 1, "B": True}})
        test_list = JSONObject({"A": [1, "2", True, "false"]})
        test_str = JSONObject({"A": "lorep ipsum", "B": {"B1": [1, 2]}})
        test_bool = JSONObject({"A": True})

        self.assertTrue(
            SingleQuery("A", {"A": 1, "B": True})._check_against_node(test_dict.A)
        )
        self.assertFalse(SingleQuery("A", ["A", "B"])._check_against_node(test_dict.A))

        self.assertTrue(SingleQuery("A", "lorep ipsum")._check_against_node(test_str.A))
        self.assertFalse(SingleQuery("A", "lorepipsum")._check_against_node(test_str.A))
        self.assertTrue(
            SingleQuery("A__exact", "lorep ipsum")._check_against_node(test_str.A)
        )
        self.assertFalse(
            SingleQuery("A__exact", "lorepipsum")._check_against_node(test_str.A)
        )

        self.assertTrue(
            SingleQuery("A", [1, "2", True, "false"])._check_against_node(test_list.A)
        )
        self.assertTrue(
            SingleQuery("A", [1, 2, True, False])._check_against_node(test_list.A)
        )
        self.assertTrue(
            SingleQuery(
                "B1__parent__parent__c_A__exact", "lorep ipsum"
            )._check_against_node(test_str.B.B1)
        )

    def test_single_query_gt(self):
        test_float = JSONObject({"A": 1.3})
        test_list = JSONObject({"A": [2, 3], "B": []})

        self.assertTrue(SingleQuery("A__gt", 1)._check_against_node(test_float.A))
        self.assertTrue(SingleQuery("A__gt", [1, 2])._check_against_node(test_list.A))
        self.assertTrue(
            SingleQuery("A__gt", [1, 2, 5])._check_against_node(test_list.A)
        )
        self.assertTrue(SingleQuery("A__gt", [1])._check_against_node(test_list.A))
        self.assertFalse(SingleQuery("A__gt", 1)._check_against_node(test_list.A))
        self.assertFalse(SingleQuery("A__gt", [])._check_against_node(test_list.A))
        self.assertFalse(SingleQuery("A__gt", type)._check_against_node(test_list.A))
        self.assertFalse(SingleQuery("A__gt", [3, 2])._check_against_node(test_list.A))
        self.assertFalse(
            SingleQuery("A__gt", [1, 3, 5])._check_against_node(test_list.A)
        )
        self.assertFalse(
            SingleQuery("B__gt", [1, 3, 5])._check_against_node(test_list.B)
        )
        self.assertFalse(SingleQuery("B__gt", [])._check_against_node(test_list.B))

    def test_single_queries(self):
        test = JSONObject(
            [{"A": [1, 2], "B": {"A": "123"}}, {"date": "2021-05-04T09:08:00"}]
        )

        q1 = SingleQuery("A__contains", 1)
        q2 = SingleQuery("A__in", (0, 2, 1, 3))
        q3 = SingleQuery("A__in", (0, 2))
        q4 = SingleQuery("A__contains", 3)
        q5 = SingleQuery("date", datetime(2021, 5, 4, 9, 8, 0, tzinfo=pytz.utc))
        q6 = SingleQuery("B__c_A", 123)

        self.assertTrue(q1._check_against_node(test._0.A))
        self.assertTrue(q2._check_against_node(test._0.A))
        self.assertFalse(q3._check_against_node(test._0.A))
        self.assertTrue(q4._check_against_node(test._0.B.A))
        self.assertTrue(q5._check_against_node(test._1.date))
        self.assertTrue(q6._check_against_node(test._0.B))

    def test_update(self):

        test = JSONObject(
            {
                "data": {
                    "cik": "0005852352",
                    "fileNumber": "052-065820",
                    "team": [
                        {"name": "David", "bio": "An enthusiast", "date": "2021-05-08"},
                        {"name": "Alex", "bio": "A musician", "date": "2020-01-03"},
                    ],
                },
                "comments": [
                    {
                        "date": "2021-01-01T08:00:00",
                        "text": "Ouuu yeahhh",
                        "responses": 0,
                    },
                    {
                        "date": "2021-01-02T09:30:00",
                        "text": "That sounds quite good",
                        "responses": 22,
                    },
                ],
            }
        )
        test2 = JSONObject(dict(A=1, B=2))
        test6 = self.test6.copy()

        self.assertEqual(test2.query(A=All).update_ifnonnull(None), (0, 1))
        self.assertDictEqual(test2, dict(A=1, B=2))
        self.assertEqual(
            test2.query(A=All).update_ifnonnull(lambda x: None if x == 1 else 3), (0, 1)
        )
        self.assertDictEqual(test2, dict(A=1, B=2))
        self.assertEqual(
            test2.query(A=All).update_ifnonnull(lambda x: 0 if x + 1 == 2 else 3),
            (1, 0),
        )
        self.assertDictEqual(test2, dict(A=0, B=2))

        self.assertEqual(test6.query(data__0=True).update("OK"), (1, 0))
        self.assertEqual(
            test.data.team.query(name__contains="e").update("Veronica"), (1, 0)
        )

        self.assertEqual(test.data.team.query(name__contains="e"), ["Veronica"])
        self.assertEqual(test6.query(data__0=True), [])
        self.assertEqual(test6.query(data="OK"), ["OK"])
        self.assertEqual(
            test6.query(pos__2__gt=3, text__contains=6).update(lambda x: x[:2]), (1, 0)
        )
        self.assertEqual(test6.position_data._5.pos, [1, 1])
        self.assertEqual(test6.position_data.query(pos__2=All), [])
        self.assertEqual(test6.position_data.query(pos=(1, 1)), [[1, 1]])

    def test_all_queries(self):
        test = JSONObject({"A": {"A": 1, "B": 2}, "B": ["A", {"A": 2}]})

        self.assertEqual(test.query(A=All), [{"A": 1, "B": 2}, "$1", 2])
        self.assertEqual(test.query(B=All), [2, ["A", {"A": 2}]])

    def test_setters(self):

        test = JSONObject({"data": [{"A": 1, "B": 2}]})
        test2 = JSONObject({"key": "mykey", "index": 1, "nested": {"index": "2"}})
        test3 = JSONObject([1, 2, {"A": [3, 4]}])

        self.assertEqual(
            test.query(data__0__contains="B"), QuerySet([[{"A": 1, "B": 2}]])
        )

        test.data._0.B = 555

        self.assertFalse(test.query(B=2).exists())
        self.assertEqual(test.query(B=555), [555])

        self.assertEqual(test2.key, "mykey")
        self.assertEqual(test2.index, "1")
        self.assertEqual(test2.nested.index, 2)

        test2.key = 111
        test2.index = 222
        test2.nested.index = 333

        self.assertDictEqual(
            test2, JSONObject({"key": 111, "index": 222, "nested": {"index": 333}})
        )
        self.assertEqual(test2.query(key=All), [111])
        self.assertListEqual(test2.query(index=All), [333, 222])
        self.assertEqual(test2.query(index=333).first().jsonpath, "nested/index/")

        self.assertTrue(test3.query(A__contains=4).exists())

        test3._0 = "first"
        test3._1 = "second"
        test3._2.A._1 = "last"

        self.assertListEqual(test3, JSONObject(["first", "second", {"A": [3, "last"]}]))
        self.assertFalse(test3.query(A__contains=4).exists())
        self.assertTrue(test3.query(A__contains="last").exists())

    def test_annotations(self):

        test = self.test1.copy()
        test2 = self.test1.copy()
        test3 = JSONObject([1, 2, {"A": [1, 2, {"B": 3}], "B": 4}])

        self.assertEqual(
            test.annotate(a1=1, a2=2),
            JSONObject(
                [
                    {"Float": 2.3, "Int": 1, "Str": "string", "a1": 1, "a2": 2},
                    {
                        "Dict": {"Float": 0.0, "List": [1, 2, 3], "a1": 1, "a2": 2},
                        "a1": 1,
                        "a2": 2,
                    },
                ]
            ),
        )

        self.assertEqual(test._1.Dict.a2.jsonpath, "1/Dict/a2/")
        self.assertEqual(test.query(a1=1).count(), 3)
        self.assertNotEqual(test, self.test1)

        self.assertEqual(
            test2.annotate(a1={"status": "OK"}).query(a1__contains="status"),
            [{"status": "OK"}, {"status": "OK"}, {"status": "OK"}],
        )

        self.assertEqual(
            test3.annotate(C=1, D=2),
            JSONObject(
                [1, 2, {"A": [1, 2, {"B": 3, "C": 1, "D": 2}], "B": 4, "C": 1, "D": 2}]
            ),
        )

        # now we remove the annotations and check if recovers original object

        test._remove_annotations()

        self.assertEqual(test, self.test1)
        self.assertFalse(test.query(a1=All).exists())

    def test_pop(self):

        test = JSONObject({"data": [{"name": "Dan", "age": 30}]})

        self.assertSetEqual(set(test.data._0._child_objects.values()), {"Dan", 30})
        self.assertEqual(test.data._0.name, "Dan")

        # remove a child

        test.data._0.pop("name")

        self.assertSetEqual(set(test.data._0._child_objects.values()), {30})
        self.assertFalse(test.query(name=All).exists())
        self.assertIsNone(test.data._0.name)

    def test_multiparent(self):
        test = JSONObject(
            {
                "root": {
                    "root_list": [0, {"child": {"A": 1}}, {"child2": {"A": 1}}],
                    "root_dict": {"child": {"A": 1}, "key": [0, "key"]},
                }
            }
        )

        self.assertEqual(test.query(A__parents__c_key__1__contains="ey"), ["1"])
        self.assertEqual(test.query(A__parents__c_key__1__contains="ey", A=1), ["1"])
        self.assertFalse(
            test.query(A__parents__c_key__1__contains="ey", A__gt=1).exists()
        )
        self.assertEqual(test.query(A__parents__c_key__1__contains="ey").count(), 1)
        self.assertEqual(
            test.query(A__parents__c_key__1__contains="ey").first().jsonpath,
            "root/root_dict/child/A/",
        )
        self.assertEqual(
            test.get(A__parents__0=0, A__parents__index=1, throw_exceptions_=True), 1
        )
        self.assertEqual(
            test.get(
                A__parents__0=0, A__parents__index=1, throw_exceptions_=True
            ).jsonpath,
            "root/root_list/1/child/A/",
        )
        self.assertIsNone(
            test.get(
                A__parents__0=0,
                A__parents__index=0,
                throw_exceptions_=False,
                native_types_=True,
            )
        )
        self.assertRaisesRegex(
            JSONQueryException,
            "Lookup parents can only be included once",
            lambda: test.get(A__parents__parents__0=0),
        )

    def test_values(self):

        js.config.query_exceptions = False

        test = JSONObject(
            {
                "id": 1234,
                "company": {
                    "name": "NAME",
                    "filing_set": [
                        {
                            "date": "2021-01-01",
                            "data": {"field1": 1, "field2": 2},
                            "type": "C",
                        },
                        {
                            "date": "2022-01-01",
                            "data": {"field1": 3, "field2": 4},
                            "type": "A",
                        },
                    ],
                },
                "date": "2022-02-02",
                "filing": {"field1": 5},
            }
        )
        test2 = JSONObject(
            {
                "data": {
                    "id": "0008523621",
                    "amount": 55856212.25,
                    "success": False,
                    "team": [
                        {
                            "name": "David G. García",
                            "age": 36,
                            "hobbies": ["music", "reading"],
                        },
                        {
                            "name": "Alexander D. Diego",
                            "age": 31,
                            "hobbies": ["cooking", "music", "sports", "yoga"],
                        },
                        {"name": "David A. Márquez", "age": 28, "hobbies": None},
                        {
                            "name": "Peter C. Jackson",
                            "age": 31,
                            "hobbies": ["sports", "reading", "tennis", "smoke"],
                            "staff": True,
                        },
                    ],
                },
                "updated_at": "2021-05-01T09:30:00",
                "comments": {
                    "data": "structured",
                    "amount": 2,
                    "comments": [
                        0,
                        {
                            "name": "Peter K. Márquez",
                            "text": "Great!",
                            "valuation": 10,
                            "timestamp": "2020-03-01",
                        },
                        1,
                        {
                            "name": "Jacob H. Stack",
                            "text": "Bad!",
                            "valuation": 1,
                            "timestamp": "2021-03-05",
                            "staff": True,
                        },
                    ],
                },
            }
        )

        self.assertEqual(
            test.get(field1=1, field1__parents__c_type="C").values("date"),
            {"date": "2021-01-01"},
        )
        self.assertEqual(
            test.get(field1=1, field1__parents__c_type="C").values("date", "name"),
            {"date": "2021-01-01", "name": "NAME"},
        )
        self.assertEqual(
            test.get(field1=1, field1__parents__c_type="C").values(
                datetime="date", new_name="name"
            ),
            {"datetime": "2021-01-01", "new_name": "NAME"},
        )
        self.assertEqual(
            test.get(field1=1, field1__parents__c_type="C").values(
                "date", new_name="name"
            ),
            {"date": "2021-01-01", "new_name": "NAME"},
        )
        self.assertEqual(
            test.get(
                field1__parents__c_date__year=2022, field1__notpath="filing"
            ).values("date", "type", "id"),
            {"date": "2021-01-01", "type": "C", "id": 1234},
        )
        self.assertEqual(
            test.get(field1__parents__c_date__year=2022, field1__notpath="filing")
            .values("date", "type", "id")
            .id,
            1234,
        )

        self.assertEqual(
            test2.get(staff=True).values("timestamp", "age"),
            {"timestamp": None, "age": 31},
        )
        self.assertEqual(
            test2.get(fake=True).values("timestamp", "age"),
            {"timestamp": None, "age": None},
        )
        self.assertIsNone(
            test2.get(fake=True).values("timestamp", "age").timestamp,
        )

    def test_distinct(self):

        self.assertEqual(
            self.test6.query(timestamp__year=2021)
            .order_by("-timestamp")
            .distinct(lambda x: ExtractYear(x).year),
            ["2021-05-05 18:00:25"],
        )

    def test_delete(self):
        test = JSONObject(
            [
                {
                    "data": [{"name": "Dan", "age": 30}, {"name": "Hel", "age": 31}],
                    "date": datetime(2021, 1, 1),
                },
                {"data": {"name": "Fel", "age": "27"}},
            ]
        )

        self.assertEqual(test.query(date__year=2021).delete(), 1)
        self.assertEqual(test.query(date__year=2021), [])
        self.assertEqual(test.query(data=All).delete(), 2)
        self.assertEqual(test.query(data=All), [])
        self.assertEqual(test, [{}, {}])

    def test_query_keys(self):

        test = JSONObject({"name": {"NAME": "Dan", "name": True}})

        self.assertListEqual(
            test.query_key(js.I(".*na.*")).distinct(lambda x: x._key).keys(),
            ValuesList(["name", "NAME"]),
        )

        self.assertListEqual(
            test.query_key(".*ame", exact=All), [{"NAME": "Dan", "name": True}, True]
        )
        self.assertListEqual(
            test.query_key(re.compile(".*AmE", re.I), exact=All),
            [{"NAME": "Dan", "name": True}, "Dan", True],
        )
        self.assertListEqual(
            test.query_key(re.compile(".*AmE", re.I), type__=bool),
            QuerySet([True]),
        )
        self.assertListEqual(
            test.query_key(
                js.I(".*AmE"),
                type__=bool,
                parent={"NAME": "Dan", "name": True},
            ),
            QuerySet([True]),
        )
        self.assertListEqual(
            test.query_key(
                re.compile(".*AmE", re.I),
                type__=bool,
                parent__key="name",
            ),
            QuerySet([True]),
        )
        self.assertListEqual(
            test.query_key(
                re.compile(".*AmE", re.I),
                type__=bool,
                path="fake",
            ),
            QuerySet([]),
        )

    def test_traverse_json(self):
        # TODO what if a key has an explicit "
        test = JSONObject([{"A": 1, "B": {"B1": 2, "B2": [3, 4]}}])

        self.assertListEqual(
            test.traverse_json().values("path", flat=True),
            [
                "[0]",
                '[0]["A"]',
                '[0]["B"]',
                '[0]["B"]["B1"]',
                '[0]["B"]["B2"]',
                '[0]["B"]["B2"][0]',
                '[0]["B"]["B2"][1]',
            ],
        )
