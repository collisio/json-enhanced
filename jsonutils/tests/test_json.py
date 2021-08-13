import json
from jsonutils.exceptions import JSONQueryException
import unittest
from datetime import datetime

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
)
from jsonutils.encoders import JSONObjectEncoder
from jsonutils.query import All, QuerySet, SingleQuery


class JsonTest(unittest.TestCase):
    def setUp(self):
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

        self.assertEqual(test.data.datetime, JSONStr("2021-01-01T00:00:00"))

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

        test1.append({"fake": True})

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

        self.assertEqual(test1[0].index, 0)
        self.assertEqual(test1[1].index, 1)
        self.assertEqual(test1[2].index, 2)

        self.assertEqual(test1[0]["Float"].key, "Float")
        self.assertEqual(test1[2]["fake"].key, "fake")
        self.assertEqual(test1[2]["fake"].jsonpath, JSONPath("2/fake/"))

        self.assertTrue(test1.query(fake=True).exists())

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

        self.assertEqual(self.test1[0].key, None)
        self.assertEqual(self.test1[1].key, None)
        self.assertEqual(self.test1[0]["Float"].key, "Float")
        self.assertEqual(self.test1[0]["Int"].key, "Int")
        self.assertEqual(self.test1[0]["Str"].key, "Str")
        self.assertEqual(self.test1[1]["Dict"].key, "Dict")
        self.assertEqual(self.test1[1]["Dict"]["Float"].key, "Float")
        self.assertEqual(self.test1[1]["Dict"]["List"].key, "List")

    def test_parents(self):
        """Check every child object has the right parent object"""

        self.assertEqual(self.test1.parent, None)
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

    def test_queries(self):

        self.assertEqual(self.test3.query(Bool="true"), [JSONBool(True)])
        self.assertEqual(self.test3.query(Bool__type=str), [])
        self.assertEqual(self.test3.query(Bool__type=bool), [JSONBool(True)])
        self.assertEqual(self.test5.query(Str__length=7), ["string1", "string2"])
        self.assertEqual(self.test5.query(Str__length=0), [])
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
        # self.test8 = JSONObject(
        #     {
        #         "data_list": [
        #             {"name": "", "id": 0, "list": [], "tuple": (), "none": None},
        #             {},
        #         ]
        #     }
        # )
        self.assertEqual(self.test8.query(list__isnull=True), QuerySet([[]]))
        self.assertEqual(self.test8.query(tuple__isnull=True), QuerySet([[]]))
        self.assertEqual(self.test8.query(none__isnull=True), QuerySet([None]))
        self.assertEqual(self.test8.query(id__isnull=True), QuerySet())
        self.assertEqual(self.test6.query(data__1=True), QuerySet([[False, True]]))
        # UNCOMMENT THIS WHEN IMPLEMENTED
        # self.assertEqual(
        #     self.test6.query(text__regex=r"(?:2|5)", pos__0__gte=2),
        #     [
        #         {"text": "dummy text 2", "pos": [3, 2]},
        #         {"text": "dummy text 5", "pos": [4, 1]},
        #     ],
        # )

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
        test6 = self.test6.copy()

        test6.query(data__0=True).update("OK")
        test.data.team.query(name__contains="e").update("Veronica")

        self.assertEqual(test.data.team.query(name__contains="e"), ["Veronica"])
        self.assertEqual(test6.query(data__0=True), [])
        self.assertEqual(test6.query(data="OK"), ["OK"])

    def test_all_queries(self):
        test = JSONObject({"A": {"A": 1, "B": 2}, "B": ["A", {"A": 2}]})

        self.assertEqual(test.query(A=All), [{"A": 1, "B": 2}, "$1", 2])
        self.assertEqual(test.query(B=All), [2, ["A", {"A": 2}]])
