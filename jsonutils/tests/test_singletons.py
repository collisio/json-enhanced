import json
import unittest
from datetime import date, datetime, tzinfo

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
    JSONSingleton,
    JSONStr,
)
from jsonutils.encoders import JSONObjectEncoder
from jsonutils.exceptions import JSONSingletonException
from jsonutils.functions.parsers import parse_datetime
from jsonutils.query import QuerySet


class JsonTest(unittest.TestCase):
    def test_str_conversions(self):
        self.assertEqual(JSONStr(" + $4312555.52US").to_float(), JSONFloat(4312555.52))
        self.assertEqual(
            JSONStr(" + $4k312k555.52US").to_float(thousands_sep="k"),
            JSONFloat(4312555.52),
        )
        self.assertEqual(
            JSONStr(" - $4,312,555.52  ").to_float(), JSONFloat(-4312555.52)
        )
        self.assertEqual(
            JSONStr(" + $$4,312,555.520 USD ").to_float(), JSONFloat(4312555.52)
        )
        self.assertEqual(
            JSONStr(" + $$4.312.555,520 USD ").to_float(
                decimal_sep=",", thousands_sep="."
            ),
            JSONFloat(4312555.52),
        )
        self.assertEqual(
            JSONStr(" - $$4 312 555.520 USD ").to_float(
                decimal_sep=".", thousands_sep=" "
            ),
            JSONFloat(-4312555.52),
        )
        self.assertEqual(
            JSONStr(" - $$4 312 555,520 USD ").to_float(
                decimal_sep=",", thousands_sep=" "
            ),
            JSONFloat(-4312555.52),
        )
        self.assertEqual(
            JSONStr(" - $$4K312K555,520 USD ").to_float(
                decimal_sep=",", thousands_sep="K"
            ),
            JSONFloat(-4312555.52),
        )
        self.assertRaisesRegex(
            JSONSingletonException,
            "Target string does not match a float number",
            lambda: JSONStr(" - $$4 312 555,520 USD ").to_float(
                decimal_sep=",", thousands_sep="K"
            ),
        )
        self.assertRaisesRegex(
            JSONSingletonException,
            "Target string does not match a float number",
            lambda: JSONStr(" - $$4k312k555,520, USD ").to_float(
                decimal_sep=",", thousands_sep="k"
            ),
        )
        self.assertRaises(
            JSONSingletonException,
            lambda: JSONStr(" - $4 312 555.520 USD ").to_float(),
        )
        self.assertRaisesRegex(
            JSONSingletonException,
            "Target string does not match a float number",
            lambda: JSONStr("$USD4,312,555.520 USD").to_float(),
        )
        self.assertRaises(
            JSONSingletonException, lambda: JSONStr("--$4,312,555.520 USD").to_float()
        )
        self.assertEqual(
            JSONStr(" 2021-01-04").to_datetime(), datetime(2021, 1, 4, tzinfo=pytz.utc)
        )
        self.assertEqual(
            JSONStr(" 2021-01-04").to_datetime(return_string=True),
            datetime(2021, 1, 4, tzinfo=pytz.utc).isoformat(),
        )
        self.assertEqual(
            JSONStr(" 2021-01-04 09:00:00.001+01:00").to_datetime(),
            datetime.strptime(
                "2021-01-04T09:00:00.001+01:00", "%Y-%m-%dT%H:%M:%S.001%z"
            ),
        )
        self.assertEqual(
            JSONStr(" 2021-01-04 T 09:00:00-01:00").to_datetime(),
            datetime.fromisoformat("2021-01-04T09:00:00-01:00"),
        )
        self.assertEqual(
            JSONStr(" 2021/01/04 ").to_datetime(), datetime(2021, 1, 4, tzinfo=pytz.utc)
        )
        self.assertEqual(
            JSONStr("01-02-2021").to_datetime(), datetime(2021, 2, 1, tzinfo=pytz.utc)
        )
        self.assertEqual(
            JSONStr("01/02/2021 ").to_datetime(), datetime(2021, 2, 1, tzinfo=pytz.utc)
        )
        self.assertEqual(
            JSONStr("01/02/2021 T 09:00:30").to_datetime(),
            datetime(2021, 2, 1, 9, 0, 30, tzinfo=pytz.utc),
        )
        self.assertEqual(
            JSONStr("01/02/2021 T 09:00:30.0054").to_datetime(),
            datetime(2021, 2, 1, 9, 0, 30, tzinfo=pytz.utc),
        )
        self.assertEqual(
            JSONStr("01/02/2021 T09.00.30.0054Z").to_datetime(),
            datetime(2021, 2, 1, 9, 0, 30, tzinfo=pytz.utc),
        )
        self.assertEqual(
            JSONStr("01/02/2021 T09.00.30.0054Z").to_datetime(tzone_aware=False),
            datetime(2021, 2, 1, 9, 0, 30),
        )
        self.assertEqual(
            JSONStr(" 01/02/2021T 09.00.30.0054Z ").to_datetime(),
            datetime(2021, 2, 1, 9, 0, 30, tzinfo=pytz.utc),
        )
        self.assertIsNone(JSONStr("fake_datetime").to_datetime(fail_silently=True))
        self.assertIsNone(
            JSONStr("fake_datetime").to_datetime(return_string=True, fail_silently=True)
        )
        self.assertRaisesRegex(
            JSONSingletonException,
            "Can't parse target datetime",
            lambda: JSONStr("fake/datetime").to_datetime(),
        )
        self.assertRaisesRegex(
            JSONSingletonException,
            "Can't parse target datetime",
            lambda: JSONStr("01/02/2021T09.00.30.0054Z+05:00").to_datetime(),
        )
        self.assertRaisesRegex(
            JSONSingletonException,
            "Error on introduced datetime",
            lambda: JSONStr("32/02/2022").to_datetime(),
        )
        self.assertEqual(JSONStr(" tRue ").to_bool(), True)
        self.assertEqual(JSONStr(" fAlsE ").to_bool(), False)
        self.assertRaises(JSONSingletonException, lambda: JSONStr(" fAlsE. ").to_bool())

    def test_str_comparison_methods(self):
        self.assertGreater(JSONStr(" -$ 2,132.01US"), -5000)
        self.assertLess(JSONStr(" -5€ "), -4)
        self.assertGreater(JSONStr(" -5€ "), -6)
        self.assertGreaterEqual(JSONStr("-$2USD"), -2)
        self.assertGreaterEqual(JSONStr("-2EUR"), -3)
        self.assertEqual(
            JSONStr(" 2021-12-30 T 09:00:03+00:00 "),
            datetime(2021, 12, 30, 9, 0, 3, tzinfo=pytz.utc),
        )
        self.assertGreater(
            JSONStr(" 01/02/2021 08:00:00"), datetime(2021, 2, 1, 7, 0, 0)
        )
        self.assertLess(JSONStr(" 01/02/2021 08:00:00"), datetime(2021, 2, 1, 9, 0, 0))
        self.assertLess(datetime(2021, 2, 1, 7, 0, 0), JSONStr(" 01/02/2021 08:00:00"))
        self.assertGreater(
            datetime(2021, 2, 1, 9, 0, 0), JSONStr(" 01/02/2021 08:00:00")
        )
        self.assertIn(JSONStr("1.3"), [1, 2, 1.3])
        self.assertIn(1.3, JSONList(["1.3", 2]))
        self.assertIn("$1.3USD", JSONList([1.3, 1.4]))
        self.assertIn(datetime(2021, 1, 1), JSONList(["2021/01/01", 1]))

        self.assertNotEqual(JSONStr(1), True)

        self.assertFalse(JSONStr("3.5") > {"A": 1})
        self.assertFalse(JSONStr("3.5") >= {"A": 1})
        self.assertFalse(JSONStr("3.5") < {"A": 1})
        self.assertFalse(JSONStr("3.5") <= {"A": 1})

        self.assertFalse(JSONStr("3.5") > [1, 2])
        self.assertFalse(JSONStr("3.5") >= [1, 2])
        self.assertFalse(JSONStr("3.5") < [1, 2])
        self.assertFalse(JSONStr("3.5") <= [1, 2])

        self.assertFalse(JSONStr("3.5") > True)
        self.assertFalse(JSONStr("3.5") >= True)
        self.assertFalse(JSONStr("3.5") < True)
        self.assertFalse(JSONStr("3.5") <= True)

        self.assertFalse(JSONStr(1) > False)
        self.assertFalse(JSONStr(0) >= False)
        self.assertFalse(JSONStr(0) < False)
        self.assertFalse(JSONStr(0) <= False)

    def test_float_comparison_methods(self):
        self.assertEqual(JSONFloat(3.8), "$3.8USD")
        self.assertEqual(JSONFloat(3), "$3USD")
        self.assertEqual(JSONFloat(3.0), 3)
        self.assertGreater(JSONFloat(5.3), " €  5,.2EUR ")
        self.assertLess(JSONFloat(5.3), " €  5,.4EUR ")

    def test_bool_comparison_methods(self):
        self.assertEqual(JSONBool(True), True)
        self.assertEqual(JSONBool(False), False)
        self.assertFalse(JSONBool(True) < 3)
        self.assertIn(None, JSONList([None, 1]))
        self.assertTrue(JSONBool(True) != False)
        self.assertTrue(JSONBool(True) == True)
        self.assertFalse(JSONBool(True) != True)
        self.assertFalse(JSONBool(True) == False)
        self.assertTrue(JSONBool(False) != True)
        self.assertTrue(JSONBool(False) == False)
        self.assertFalse(JSONBool(False) != False)
        self.assertFalse(JSONBool(False) == True)
        self.assertTrue(bool(JSONBool(True)) != False)
        self.assertTrue(bool(JSONBool(True)) == True)
        self.assertFalse(bool(JSONBool(True)) != True)
        self.assertFalse(bool(JSONBool(True)) == False)
        self.assertTrue(bool(JSONBool(False)) != True)
        self.assertTrue(bool(JSONBool(False)) == False)
        self.assertFalse(bool(JSONBool(False)) != False)
        self.assertFalse(bool(JSONBool(False)) == True)

    def test_dict_comparison_methods(self):
        self.assertEqual(JSONDict(a=1, b=2), dict(b=2, a=1))

        self.assertFalse(JSONDict(a=1) > 1)
        self.assertFalse(JSONDict(a=1) > "str")
        self.assertFalse(JSONDict(a=1) > [1, 2])
        self.assertFalse(JSONDict(a=1) > (1,))
        self.assertFalse(JSONDict(a=1) > type)

    def test_parse_datetime_function(self):
        self.assertEqual(
            parse_datetime(date(2021, 1, 1), tzone_aware=True, only_date=False),
            datetime(2021, 1, 1, tzinfo=pytz.utc),
        )
        self.assertEqual(
            parse_datetime(
                date(2021, 1, 1), tzone_aware=True, only_date=False, return_string=True
            ),
            datetime(2021, 1, 1, tzinfo=pytz.utc).isoformat(),
        )
        self.assertEqual(
            parse_datetime(date(2021, 1, 1), tzone_aware=True, only_date=True),
            datetime(2021, 1, 1, tzinfo=pytz.utc),
        )
        self.assertEqual(
            parse_datetime(
                date(2021, 1, 1), tzone_aware=True, only_date=True, return_string=True
            ),
            datetime(2021, 1, 1, tzinfo=pytz.utc).isoformat(),
        )
        self.assertEqual(
            parse_datetime(date(2021, 1, 1), tzone_aware=False, only_date=True),
            datetime(2021, 1, 1),
        )
        self.assertEqual(
            parse_datetime(
                date(2021, 1, 1), tzone_aware=False, only_date=True, return_string=True
            ),
            datetime(2021, 1, 1).isoformat(),
        )
        self.assertEqual(
            parse_datetime(date(2021, 1, 1), tzone_aware=False, only_date=False),
            datetime(2021, 1, 1),
        )
        self.assertEqual(
            parse_datetime(datetime(2021, 1, 1, 9), tzone_aware=True, only_date=False),
            datetime(2021, 1, 1, 9, tzinfo=pytz.utc),
        )
        self.assertEqual(
            parse_datetime(datetime(2021, 1, 1, 9), tzone_aware=True, only_date=True),
            datetime(2021, 1, 1, tzinfo=pytz.utc),
        )

        self.assertEqual(
            parse_datetime("2020-07-14T12:31:45Z"),
            datetime(2020, 7, 14, 12, 31, 45, tzinfo=pytz.utc),
        )

        self.assertEqual(
            parse_datetime("Sep 9, 2021"), datetime(2021, 9, 9, tzinfo=pytz.utc)
        )
        self.assertEqual(
            parse_datetime("dec,  1 2021, 09:30"),
            datetime(2021, 12, 1, 9, 30, tzinfo=pytz.utc),
        )

        self.assertEqual(
            parse_datetime("january,  1 2021, 9:30:05"),
            datetime(2021, 1, 1, 9, 30, 5, tzinfo=pytz.utc),
        )

        self.assertEqual(
            parse_datetime("feb,  12, 2021, 9:30:05.123+02:00", return_string=True),
           "2021-02-12T09:30:05+02:00",
        )

        self.assertIsNone(parse_datetime(object, fail_silently=True))
        self.assertIsNone(
            parse_datetime(object, fail_silently=True, return_string=True)
        )
