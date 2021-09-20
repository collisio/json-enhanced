from jsonutils.base import JSONObject
from jsonutils.functions.parsers import (
    parse_bool,
    parse_datetime,
    parse_float,
    parse_http_url,
    parse_json,
    parse_timestamp,
)
from jsonutils.query import All, I, Q

_JSON_TYPES = (
    dict,
    list,
    str,
    float,
    int,
    bool,
    type(None),
)

from .release import __version__
