from functools import wraps

import jsonutils.config as config


class dummy:
    pass


def catch_exceptions(func):
    """
    When applied on a function, prevent it from throwing exceptions, if argument 'fail_silently' is set to True (False by default)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.get("fail_silently") is True:
            try:
                return func(*args, **kwargs)
            except Exception:
                return
        else:
            return func(*args, **kwargs)

    return wrapper


def return_str_or_datetime(func):
    """
    This decorator will be applied to the parse_datetime function,
    so that it returns strings in isoformat format whenever the
    return_string argument is set to True.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.get("return_string") is True:
            return func(*args, **kwargs).isoformat()
        else:
            return func(*args, **kwargs)

    return wrapper


def return_value_on_exception(value, exception):
    """
    When applied on a function, it will return `value` if selected `exception` is raised
    and argument `fail_silently` is passed as True.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if kwargs.get("fail_silently") is True:
                try:
                    return func(*args, **kwargs)
                except exception:
                    if (
                        selected_return_value := kwargs.get("value_on_exception", dummy)
                    ) is not dummy:
                        return selected_return_value
                    return value
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


def global_config(fun=None, **config_kw):
    """
    Applies a certain global configuration to the function on which it acts.
    By default, if no arguments are entered, it will use native_types=True, query_exceptions=False.

    Example
    -------

    from jsonutils.functions.decorators import global_config
    from jsonutils import JSONObject

    data = JSONObject(
        [
            {
                "A": 1,
                "B": 2
            },
            {
                "A": 1,
                "B": 3
            },
        ]
    )

    @global_config
    def query_1(data):
        return data.get(A=1)

    >>> query_1(data)   # this will use native_types=True, query_exceptions=False
        1               # so, this is a python `int`, not a JSONInt

    @global_config(query_exceptions=True)
    def query_2(data):
        return data.get(A=1)

    >>> query_2(data)   # now this user query_exceptions=True, so it will throw a multiple values exception.
        JSONQueryMultipleValues: More than one value returned by query
    """

    if not config_kw:
        config_kw = dict(native_types=True, query_exceptions=False)

    def _set_config(dic):
        for k, v in dic.items():
            setattr(config, k, v)

    INITIAL_CONFIG = {k: getattr(config, k) for k in config_kw}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _set_config(config_kw)
            try:
                result = func(*args, **kwargs)
            finally:
                _set_config(INITIAL_CONFIG)
            return result

        return wrapper

    if fun is not None:
        return decorator(fun)

    return decorator


def return_native_types(func):
    """ """

    @wraps(func)
    def wrapper(self):
        res = func(self)
        if self._native_types:
            return res._data
        return res

    return wrapper
