# This module contains utilities to parse query arguments
# TODO parse image links as text
import ast
import re
from datetime import date, datetime
from json import JSONDecoder

import jsonutils.base as base
import pytz
import requests
from jsonutils.config.locals import decimal_separator, thousands_separator
from jsonutils.exceptions import JSONQueryException, JSONSingletonException
from jsonutils.functions.decorators import catch_exceptions, return_str_or_datetime
from jsonutils.query import All, AllChoices, ExtractYear, I, QuerySet, ValuesList
from jsonutils.utils.retry import retry_function


def _parse_query(node, include_parent_, **q):
    """
    We must determine whether the child passed as input argument matches the conditions given by the query q.
    If required actions don't match the child type, it won't throw any exception, just returns False for such an object, and
    it won't be appended to the queryset.
    Query q must be structured as follows:
        <key>__<modificator>__<query>
    """

    # grab a list of node actions, without the action suffix
    node_actions = [
        i.replace("_action", "") for i in dir(base.JSONNode) if i.endswith("action")
    ]

    class UniqueList(list):
        """A list but appending only unique values"""

        def append(self, object):
            return super().append(object) if object not in self else None

    def make_actions(obj, target_actions, query_value):
        MODIFICATOR_CHECK = True
        actions_count = len(target_actions)
        for idx, action in enumerate(target_actions):
            if MODIFICATOR_CHECK:
                # ---- MODIFICATORS ----
                # modify obj before apply actions
                if action == "parent":
                    obj = obj.parent
                    if obj is None:
                        return False
                    if idx == actions_count - 1:
                        action = "exact"  # if parent is last action, take exact as the default one
                    else:
                        continue  # continue to next action or modificator
                elif action == "parents":  # multiparents modificator
                    parents = obj.parent_list
                    if not parents:
                        return False
                    if "parents" in target_actions[idx + 1 :]:
                        raise JSONQueryException(
                            "Lookup parents can only be included once"
                        )

                    results = (
                        make_actions(i, target_actions[idx + 1 :], query_value)
                        for i in parents
                    )
                    if any(results):
                        return True  # no more actions, continue with next query
                    else:
                        return False
                elif match := re.fullmatch(r"c_(\w+)", action):  # child modificator
                    try:
                        obj = obj.__getitem__(match.group(1))
                    except Exception:
                        return False
                    if idx == actions_count - 1:
                        action = "exact"  # if child is last action, take exact as the default one
                    else:
                        continue  # continue to next action or modificator
                elif action.isdigit():
                    if not isinstance(obj, list):
                        return False
                    try:
                        obj = obj[int(action)]
                    except IndexError:
                        return False
                    if idx == actions_count - 1:
                        action = "exact"  # if digit is last action, take exact as the default one
                    else:
                        continue  # continue to next action or modificator
                elif action == "year":  # TODO add test for year
                    if len(target_actions[idx + 1 :]) > 1:
                        raise JSONQueryException(
                            f"After year lookup, cannot set more actions"
                        )
                    obj = ExtractYear(obj)
                    if idx == actions_count - 1:
                        action = "exact"  # if year is last action, take exact as the default one
                    else:
                        MODIFICATOR_CHECK = False
                        continue  # continue to next action without cheking more modificators
            # ---- MATCH ----
            # all comparisons have child object to the left, and the underlying algorithm is contained in the magic methods of the JSON objects
            # no errors will be thrown, if types are not compatible, just returns False
            # node actions can't interfer with modificators
            if action in node_actions:  # call corresponding node method
                result = getattr(obj, action + "_action")(query_value)
                if not result:
                    return False
            else:
                raise JSONQueryException(f"Bad query: {action}")
        return True

    target_keys = UniqueList()

    for query_key, query_value in q.items():
        if not isinstance(
            query_value,
            (
                type,
                float,
                int,
                str,
                type(None),
                bool,
                dict,
                list,
                tuple,
                date,
                datetime,
                AllChoices,
            ),
        ):
            raise JSONQueryException(
                f"Target value of query has invalid type: {type(query_value)}. Valid types are: float, int, str, None, bool, dict, list, tuple, date, datetime, allchoices"
            )
        splitted_query = [i for i in query_key.split("__") if i]

        if not splitted_query:
            raise JSONQueryException("Bad query. Missing target key")

        target_key = splitted_query[0]
        target_actions = splitted_query[1:] or ["exact"]

        target_keys.append(target_key)

        if len(target_keys) > 1:  # MULTIQUERY MODE
            # in a multiquery mode, we take the outer dict which contains the first target key
            # so we prepend __parent__c_<target_key> in the target_actions list
            target_actions = ["parent", f"c_{target_key}"] + target_actions
            target_key = target_keys[0]

        # first of all, if target key of query argument does not match child's key, we won't append it to querylist
        if target_key != node._key:
            return False, None

        obj = node

        result = make_actions(obj, target_actions, query_value)
        if result is False:
            return False, None
    return (True, node.parent if include_parent_ else node)


def _parse_query_key(node, pattern, include_parent_, **q):
    """ """
    # --- first checks ----
    if not node._key:
        return False, None

    if pattern == "*":
        pattern = ".*"
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    elif isinstance(pattern, I):
        pattern = pattern.data
    elif isinstance(pattern, re.Pattern):
        pass
    else:
        raise TypeError(f"Argument pattern must be an string or regex pattern")

    if not q:
        q = {"exact": All}

    # --------------------

    # grab a list of node actions, without the action suffix
    node_actions = [
        i.replace("_action", "") for i in dir(base.JSONNode) if i.endswith("action")
    ]

    def make_actions(obj, target_actions, query_value):
        MODIFICATOR_CHECK = True
        actions_count = len(target_actions)
        for idx, action in enumerate(target_actions):
            if MODIFICATOR_CHECK:
                # ---- MODIFICATORS ----
                # modify obj before apply actions
                if action == "parent":
                    obj = obj.parent
                    if obj is None:
                        return False
                    if idx == actions_count - 1:
                        action = "exact"  # if parent is last action, take exact as the default one
                    else:
                        continue  # continue to next action or modificator
                elif action == "parents":  # multiparents modificator
                    parents = obj.parent_list
                    if not parents:
                        return False
                    if "parents" in target_actions[idx + 1 :]:
                        raise JSONQueryException(
                            "Lookup parents can only be included once"
                        )

                    results = (
                        make_actions(i, target_actions[idx + 1 :], query_value)
                        for i in parents
                    )
                    if any(results):
                        return True  # no more actions, continue with next query
                    else:
                        return False
                elif match := re.fullmatch(r"c_(\w+)", action):  # child modificator
                    try:
                        obj = obj.__getitem__(match.group(1))
                    except Exception:
                        return False
                    if idx == actions_count - 1:
                        action = "exact"  # if child is last action, take exact as the default one
                    else:
                        continue  # continue to next action or modificator
                elif action.isdigit():
                    if not isinstance(obj, list):
                        return False
                    try:
                        obj = obj[int(action)]
                    except IndexError:
                        return False
                    if idx == actions_count - 1:
                        action = "exact"  # if digit is last action, take exact as the default one
                    else:
                        continue  # continue to next action or modificator
                elif action == "year":  # TODO add test for year
                    if len(target_actions[idx + 1 :]) > 1:
                        raise JSONQueryException(
                            f"After year lookup, cannot set more actions"
                        )
                    obj = ExtractYear(obj)
                    if idx == actions_count - 1:
                        action = "exact"  # if year is last action, take exact as the default one
                    else:
                        MODIFICATOR_CHECK = False
                        continue  # continue to next action without cheking more modificators
            # ---- MATCH ----
            # all comparisons have child object to the left, and the underlying algorithm is contained in the magic methods of the JSON objects
            # no errors will be thrown, if types are not compatible, just returns False
            # node actions can't interfer with modificators
            if action in node_actions:  # call corresponding node method
                result = getattr(obj, action + "_action")(query_value)
                if not result:
                    return False
            else:
                raise JSONQueryException(f"Bad query: {action}")
        return True

    for query_key, query_value in q.items():
        if not isinstance(
            query_value,
            (
                type,
                float,
                int,
                str,
                type(None),
                bool,
                dict,
                list,
                tuple,
                date,
                datetime,
                AllChoices,
            ),
        ):
            raise JSONQueryException(
                f"Target value of query has invalid type: {type(query_value)}. Valid types are: float, int, str, None, bool, dict, list, tuple, date, datetime, allchoices"
            )
        target_actions = [i for i in query_key.split("__") if i]

        if not target_actions:
            raise JSONQueryException("Bad query. Missing actions")

        # first of all, if target key of query argument does not match child's key, we won't append it to querylist
        if not pattern.fullmatch(node._key):
            return False, None

        obj = node

        result = make_actions(obj, target_actions, query_value)
        if result is False:
            return False, None

    return (True, node.parent if include_parent_ else node)


@catch_exceptions
def parse_float(
    s,
    only_check=False,
    decimal_sep=decimal_separator,
    thousands_sep=thousands_separator,
    fail_silently=False,
):

    if decimal_sep == thousands_sep:
        raise JSONSingletonException("Decimal and Thousands separators cannot be equal")
    if isinstance(s, bool):
        raise JSONSingletonException("s argument cannot be boolean type")
    try:
        result = float(s)
    except Exception:
        if only_check:
            return False
    else:
        if only_check:
            return True
        else:
            return result
    match = re.fullmatch(
        fr"\s*(?:[\$€]*\s*([+-])?\s*|([+-])?\s*[\$€]*\s*)([0-9{thousands_sep}]+)({decimal_sep}[0-9]+)?\s*[\$€]*\w{{,10}}\s*",
        s,
    )
    if not match:
        if only_check:
            return False
        raise JSONSingletonException(
            f"Target string does not match a float number: {s}"
        )
    groups = match.groups()
    sign = groups[0] or groups[1] or ""
    number_left = groups[2].replace(thousands_sep, "")  # left of decimal sep
    number_right = groups[3] or ""  # right of decimal sep
    number_right = number_right.replace(decimal_sep, ".")

    return float("".join((sign, number_left, number_right)))


@catch_exceptions
@return_str_or_datetime
def parse_datetime(
    s,
    only_check=False,
    tzone_aware=True,
    only_date=False,
    fail_silently=False,
    return_string=False,
):
    """
    If only_check is True, then this algorithm will just check if string s matchs a datetime format (no errors).
    Algorithm is tzone aware by default. If no tzone is found on string, UTC will be considered.
    """
    if not all(
        isinstance(arg, bool)
        for arg in (only_check, tzone_aware, only_date, fail_silently, return_string)
    ):
        raise TypeError("Invalid type arguments. All keyword arguments must be boolean")

    if isinstance(s, (date, datetime)):
        if only_check:
            return True

        unified_datetime = datetime.fromisoformat(
            s.isoformat()
        )  # convert to datetime object

        if tzone_aware:
            if unified_datetime.tzinfo:
                return (
                    unified_datetime
                    if not only_date
                    else datetime(
                        unified_datetime.year,
                        unified_datetime.month,
                        unified_datetime.day,
                        tzinfo=unified_datetime.tzinfo,
                    )
                )
            else:  # if not tzinfo is shown, put utc as default
                return (
                    unified_datetime.replace(tzinfo=pytz.utc)
                    if not only_date
                    else datetime(
                        unified_datetime.year,
                        unified_datetime.month,
                        unified_datetime.day,
                        tzinfo=pytz.utc,
                    )
                )
        else:
            return (
                unified_datetime.replace(tzinfo=None)
                if not only_date
                else datetime(
                    unified_datetime.year, unified_datetime.month, unified_datetime.day
                )
            )

    def fill(x):
        if x is None:
            return 0
        else:
            try:
                return int(x)
            except ValueError:
                if isinstance(x, str):
                    lower_month = x.lower()
                    if "jan" in lower_month:
                        return 1
                    elif "feb" in lower_month:
                        return 2
                    elif "mar" in lower_month:
                        return 3
                    elif "apr" in lower_month:
                        return 4
                    elif "may" in lower_month:
                        return 5
                    elif "jun" in lower_month:
                        return 6
                    elif "jul" in lower_month:
                        return 7
                    elif "aug" in lower_month:
                        return 8
                    elif "sep" in lower_month:
                        return 9
                    elif "oct" in lower_month:
                        return 10
                    elif "nov" in lower_month:
                        return 11
                    elif "dec" in lower_month:
                        return 12
                    else:
                        return
                else:
                    return

    patterns = (
        r"\s*(?P<year>\d{4})[/\-.](?P<month>\d{1,2})[/\-.](?P<day>\d{1,2})\s*(?:T?\s*(?P<hour>\d{2})[:.](?P<min>\d{2})[:.](?P<sec>\d{2})(?:[Zz]|\.\d{3,}[Zz]?|(?:\.\d{3,})?(?P<off_sign>[+-])(?P<off_hh>\d{2}):(?P<off_mm>\d{2}))?\s*)?",
        r"\s*(?P<day>\d{1,2})[/\-.](?P<month>\d{1,2})[/\-.](?P<year>\d{4})\s*(?:T?\s*(?P<hour>\d{2})[:.](?P<min>\d{2})[:.](?P<sec>\d{2})(?:[Zz]|\.\d{3,}[Zz]?|(?:\.\d{3,})?(?P<off_sign>[+-])(?P<off_hh>\d{2}):(?P<off_mm>\d{2}))?\s*)?",
        r"\s*(?P<month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?\s*,?\s*(?P<day>\d{1,2})\s*,?\s*(?P<year>\d{4})\s*,?\s*(?:T?\s*(?P<hour>\d{1,2})[:.](?P<min>\d{2})(?:[:](?P<sec>\d{2}))?(?:[Zz]|\.\d{3,}[Zz]?|(?:\.\d{3,})?(?P<off_sign>[+-])(?P<off_hh>\d{2}):(?P<off_mm>\d{2}))?\s*)?",
    )

    for pattern in patterns:
        if match := re.fullmatch(pattern, s, re.I):
            if only_check:
                return True

            groups = match.groupdict()
            group_numbers = {k: fill(v) for k, v in groups.items()}

            year = group_numbers.get("year")
            month = group_numbers.get("month")
            day = group_numbers.get("day")
            hour = group_numbers.get("hour")
            min = group_numbers.get("min")
            sec = group_numbers.get("sec")

            off_sign = groups.get("off_sign") or "+"
            off_hh = groups.get("off_hh") or "00"
            off_mm = groups.get("off_mm") or "00"

            tzone = datetime.strptime(f"{off_sign}{off_hh}:{off_mm}", "%z").tzinfo

            try:
                if only_date:
                    return (
                        datetime(year, month, day, tzinfo=tzone)
                        if tzone_aware
                        else datetime(year, month, day)
                    )
                else:
                    return (
                        datetime(year, month, day, hour, min, sec, tzinfo=tzone)
                        if tzone_aware
                        else datetime(year, month, day, hour, min, sec)
                    )
            except Exception as e:
                if only_check:
                    return True
                raise JSONSingletonException(
                    f"Error on introduced datetime. {e}"
                ) from None

    if only_check:
        return False
    raise JSONSingletonException(f"Can't parse target datetime: {s}")


@catch_exceptions
def parse_timestamp(s, **kwargs):
    result = int(parse_datetime(s, **kwargs).timestamp() * 1000)
    return result


@catch_exceptions
def parse_bool(s, fail_silently=False):
    from jsonutils.base import JSONBool

    if isinstance(s, bool):
        return s
    elif isinstance(s, JSONBool):
        return s._data

    pipe = s.strip().lower().capitalize()
    if pipe in ("True", "False"):
        return ast.literal_eval(pipe)
    else:
        raise JSONSingletonException(f"Can't parse target bool: {s}")


def parse_json(s, **kwargs):
    """Parse all jsons from a text string or URL"""

    if not isinstance(s, str):
        raise TypeError(f"Argument s must be a string, not {type(s)}")
    output = QuerySet(list_of_root_nodes=True)

    if url_validator(s):
        req = retry_function(requests.get, s, **kwargs)
        s = req.text

    def extract_json_objects(text, decoder=JSONDecoder()):
        """Find JSON objects in text, and yield the decoded JSON data

        Does not attempt to look for JSON arrays, text, or other JSON types outside
        of a parent JSON object.

        """
        pos = 0
        while True:
            match = (text.find("{", pos) + 1) or (text.find("[", pos) + 1)
            if not match:
                break
            try:
                result, index = decoder.raw_decode(text[match - 1 :])
                yield result
                pos = match + index
            except ValueError:
                pos = match + 1

    for item in extract_json_objects(s):
        if item:
            data = base.JSONObject(item)
            output.append(data)

    return output


@catch_exceptions
def parse_http_url(url, fail_silently=False):

    if not isinstance(url, str):
        raise TypeError(f"Argument url must be an str instance, not {type(url)}")

    match = url_validator(url, return_match=True, optative_protocol=True)

    if match:
        protocol = match.groupdict().get("protocol")

        if not protocol:
            return "http://" + url
        elif protocol not in ("http", "https"):
            raise Exception(f"Url's protocol is not http: {protocol}")
        else:  # a protocol already exists
            return url

    else:
        raise Exception(f"Can't parse a valid url: {url}")


def url_validator(url, public=False, return_match=False, optative_protocol=False):
    """
    :param value: URL address string to validate
    :param public: (default=False) Set True to only allow a public IP address
    :param return_match: (default=False) Set True to return match instead of bool
    """

    ip_middle_octet = r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5]))"
    ip_last_octet = r"(?:\.(?:0|[1-9]\d?|1\d\d|2[0-4]\d|25[0-5]))"

    prot = "?" if optative_protocol else ""

    regex = re.compile(  # noqa: W605
        r"^"
        # protocol identifier
        rf"(?:(?P<protocol>https?|ftp)://){prot}"
        # user:pass authentication
        r"(?:[-a-z\u00a1-\uffff0-9._~%!$&'()*+,;=:]+"
        r"(?::[-a-z0-9._~%!$&'()*+,;=:]*)?@)?"
        r"(?:"
        r"(?P<private_ip>"
        # IP address exclusion
        # private & local networks
        r"(?:(?:10|127)" + ip_middle_octet + r"{2}" + ip_last_octet + r")|"
        r"(?:(?:169\.254|192\.168)" + ip_middle_octet + ip_last_octet + r")|"
        r"(?:172\.(?:1[6-9]|2\d|3[0-1])" + ip_middle_octet + ip_last_octet + r"))"
        r"|"
        # private & local hosts
        r"(?P<private_host>" r"(?:localhost))" r"|"
        # IP address dotted notation octets
        # excludes loopback network 0.0.0.0
        # excludes reserved space >= 224.0.0.0
        # excludes network & broadcast addresses
        # (first & last IP address of each class)
        r"(?P<public_ip>"
        r"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
        r"" + ip_middle_octet + r"{2}"
        r"" + ip_last_octet + r")"
        r"|"
        # IPv6 RegEx from https://stackoverflow.com/a/17871737
        r"\[("
        # 1:2:3:4:5:6:7:8
        r"([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|"
        # 1::                              1:2:3:4:5:6:7::
        r"([0-9a-fA-F]{1,4}:){1,7}:|"
        # 1::8             1:2:3:4:5:6::8  1:2:3:4:5:6::8
        r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|"
        # 1::7:8           1:2:3:4:5::7:8  1:2:3:4:5::8
        r"([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|"
        # 1::6:7:8         1:2:3:4::6:7:8  1:2:3:4::8
        r"([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
        # 1::5:6:7:8       1:2:3::5:6:7:8  1:2:3::8
        r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|"
        # 1::4:5:6:7:8     1:2::4:5:6:7:8  1:2::8
        r"([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|"
        # 1::3:4:5:6:7:8   1::3:4:5:6:7:8  1::8
        r"[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|"
        # ::2:3:4:5:6:7:8  ::2:3:4:5:6:7:8 ::8       ::
        r":((:[0-9a-fA-F]{1,4}){1,7}|:)|"
        # fe80::7:8%eth0   fe80::7:8%1
        # (link-local IPv6 addresses with zone index)
        r"fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|"
        r"::(ffff(:0{1,4}){0,1}:){0,1}"
        r"((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}"
        # ::255.255.255.255   ::ffff:255.255.255.255  ::ffff:0:255.255.255.255
        # (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
        r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|"
        r"([0-9a-fA-F]{1,4}:){1,4}:"
        r"((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}"
        # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33
        # (IPv4-Embedded IPv6 Address)
        r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])" r")\]|"
        # host name
        r"(?:(?:(?:xn--)|[a-z\u00a1-\uffff\U00010000-\U0010ffff0-9]-?)*"
        r"[a-z\u00a1-\uffff\U00010000-\U0010ffff0-9]+)"
        # domain name
        r"(?:\.(?:(?:xn--)|[a-z\u00a1-\uffff\U00010000-\U0010ffff0-9]-?)*"
        r"[a-z\u00a1-\uffff\U00010000-\U0010ffff0-9]+)*"
        # TLD identifier
        r"(?:\.(?:(?:xn--[a-z\u00a1-\uffff\U00010000-\U0010ffff0-9]{2,})|"
        r"[a-z\u00a1-\uffff\U00010000-\U0010ffff]{2,}))"
        r")"
        # port number
        r"(?::\d{2,5})?"
        # resource path
        r"(?:/[-a-z\u00a1-\uffff\U00010000-\U0010ffff0-9._~%!$&'()*+,;=:@/]*)?"
        # query string
        r"(?:\?\S*)?"
        # fragment
        r"(?:#\S*)?" r"$",
        re.UNICODE | re.IGNORECASE,
    )

    pattern = re.compile(regex)

    result = pattern.match(url)

    if return_match:
        return result

    if not public:
        return bool(result)

    return bool(result) and not any(
        (result.groupdict().get(key) for key in ("private_ip", "private_host"))
    )
