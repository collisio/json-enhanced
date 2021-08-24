import requests
import time

class default:
    pass


def retry_function(
    func, *args, max_tries=10, output_value=default, raise_exception=True, **kwargs
):
    """
    Try to evaluate selected function a certain number of tries
    """
    out = None
    e = None
    for _ in range(max_tries):
        try:
            out = func(*args, **kwargs)
        except Exception as exc:
            e = exc
            continue
        else:
            if func in (
                requests.post,
                requests.get,
                requests.put,
                requests.patch,
                requests.delete,
            ):
                if hasattr(out, "status_code"):
                    if out.status_code > 299:
                        time.sleep(0.5)
                        continue
                    else:
                        return out if output_value == default else output_value
            else:
                return out if output_value == default else output_value

    if raise_exception is True:
        try:
            msg = e or out.text
        except Exception:
            msg = e or out
        raise Exception(
            f"Selected function does not give any valid output after {max_tries} tries.\nError message: {msg}\n"
        )
    else:
        return out if output_value == default else output_value