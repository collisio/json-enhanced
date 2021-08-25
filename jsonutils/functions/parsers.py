# This module contains utilities to parse query arguments
# TODO parse image links as text
import ast
import re
from datetime import date, datetime

import pytz
from jsonutils.config.locals import decimal_separator, thousands_separator
from jsonutils.exceptions import JSONQueryException, JSONSingletonException
from jsonutils.query import All, AllChoices


def _parse_query(child, include_parent_, **q):
    """
    We must determine whether the child passed as input argument matches the conditions given by the query q.
    If required actions don't match the child type, it won't throw any exception, just returns False for such an object, and
    it won't be appended to the queryset.
    Query q must be structured as follows:
        <key>__<modificator>__<query>
    """
    # TODO if a query contains two different keys, take into account the dict

    obj = child

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
        splitted = query_key.split("__")
        target_key = splitted[0]
        if not target_key:
            raise JSONQueryException("Bad query. Missing target key")
        # first of all, if target key of query argument does not match child's key, we won't append it to querylist
        if target_key != child._key:
            return False, None
        try:
            target_action = splitted[1]
        except IndexError:  # default action will be exact value match
            target_action = "exact"
        else:
            try:
                target_action_extra = splitted[2]
            except IndexError:
                target_action_extra = None
        target_value = query_value  # this is the query argument value
        # ---- MODIFICATORS ----
        # modify obj before apply actions
        if target_action == "parent":
            obj = child.parent
            target_action = target_action_extra if target_action_extra else "exact"
        elif target_action.isdigit():  # if a digit, take such an element
            if not isinstance(child, (tuple, list)):
                return False, None
            try:
                obj = child[int(target_action)]
            except Exception:  # if not a list
                return False, None
            else:
                target_action = target_action_extra if target_action_extra else "exact"
        # ---- MATCH ----
        # all comparisons have child object to the left, and the underlying algorithm is contained in the magic methods of the JSON objects
        # no errors will be thrown, if types are not compatible, just returns False
        # TODO complete with node actions
        if target_action == "exact":
            if obj.exact_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "gt":
            # child value must be greather than target value of query
            if obj.gt_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "gte":
            if obj.gte_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "lt":
            if obj.lt_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "lte":
            if obj.lte_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "contains":
            if obj.contains_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "icontains":
            if obj.icontains_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "in":
            if obj.in_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "regex":
            if obj.regex_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "fullregex":
            if obj.fullregex_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "isnull":
            if obj.isnull_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "length":
            if obj.length_action(target_value):
                pass
            else:
                return False, None
        elif target_action == "type":
            if obj.type_action(target_value):
                pass
            else:
                return False, None
        else:
            raise JSONQueryException(f"Bad query: {target_action}")

    return (True, child.parent if include_parent_ else child)


def parse_float(s, decimal_sep=decimal_separator, thousands_sep=thousands_separator):

    if decimal_sep == thousands_sep:
        raise JSONSingletonException("Decimal and Thousands separators cannot be equal")
    if isinstance(s, bool):
        raise JSONSingletonException("s argument cannot be boolean type")
    try:
        return float(s)
    except Exception:
        pass

    match = re.fullmatch(
        fr"\s*(?:[\$€]*\s*([+-])?\s*|([+-])?\s*[\$€]*\s*)([0-9{thousands_sep}]+)({decimal_sep}[0-9]+)?\s*[\$€]*\w{{,10}}\s*",
        s,
    )
    if not match:
        raise JSONSingletonException(
            f"Target string does not match a float number: {s}"
        )
    groups = match.groups()
    sign = groups[0] or groups[1] or ""
    number_left = groups[2].replace(thousands_sep, "")  # left of decimal sep
    number_right = groups[3] or ""  # right of decimal sep
    number_right = number_right.replace(decimal_sep, ".")

    return float("".join((sign, number_left, number_right)))


def parse_datetime(s, only_check=False, tzone_aware=True, only_date=False):
    """
    If only_check is True, then this algorithm will just check if string s matchs a datetime format (no errors).
    Algorithm is tzone aware by default. If no tzone is found on string, UTC will be considered.
    """
    if not all(isinstance(arg, bool) for arg in (only_check, tzone_aware, only_date)):
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
                return

    patterns = (
        r"\s*(?P<year>\d{4})[/\-.](?P<month>\d{1,2})[/\-.](?P<day>\d{1,2})\s*(?:T?\s*(?P<hour>\d{2})[:.](?P<min>\d{2})[:.](?P<sec>\d{2})(?:\.\d{3,}[Zz]?|(?:\.\d{3,})?(?P<off_sign>[+-])(?P<off_hh>\d{2}):(?P<off_mm>\d{2}))?\s*)?",
        r"\s*(?P<day>\d{1,2})[/\-.](?P<month>\d{1,2})[/\-.](?P<year>\d{4})\s*(?:T?\s*(?P<hour>\d{2})[:.](?P<min>\d{2})[:.](?P<sec>\d{2})(?:\.\d{3,}[Zz]?|(?:\.\d{3,})?(?P<off_sign>[+-])(?P<off_hh>\d{2}):(?P<off_mm>\d{2}))?\s*)?",
    )

    for pattern in patterns:
        if match := re.fullmatch(pattern, s):
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
                raise JSONSingletonException(
                    f"Error on introduced datetime. {e}"
                ) from None

    if only_check:
        return False
    raise JSONSingletonException(f"Can't parse target datetime: {s}")


def parse_bool(s):
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


def parse_json(s):
    # TODO parse jsons in a string
    pass


def url_validator(url, public=False):
    """
    :param value: URL address string to validate
    :param public: (default=False) Set True to only allow a public IP address
    """

    ip_middle_octet = r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5]))"
    ip_last_octet = r"(?:\.(?:0|[1-9]\d?|1\d\d|2[0-4]\d|25[0-5]))"

    regex = re.compile(  # noqa: W605
        r"^"
        # protocol identifier
        r"(?:(?:https?|ftp)://)"
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
    if not public:
        return bool(result)

    return bool(result) and not any(
        (result.groupdict().get(key) for key in ("private_ip", "private_host"))
    )
