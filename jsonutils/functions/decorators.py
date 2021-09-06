from functools import wraps

import jsonutils.config as config


def catch_exceptions(func):
    """
    When applied on a function, prevent it from throwing exceptions, if argument 'fail_silently' is set to True (False by default)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.get("fail_silently"):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Exception in function {func.__name__}. Error message: {e}")
                return
        else:
            return func(*args, **kwargs)

    return wrapper
