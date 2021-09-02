
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/json-enhanced)
![PyPI](https://img.shields.io/pypi/v/json-enhanced)
# JSON Enhanced

JSON Enhanced implements fast and pythonic queries and mutations for JSON objects. 

# Installation

You can install json-enhanced with pip:

```
pip install json-enhanced
```
# Quickstart
```python
import jsonutils as js
from datetime import datetime

# We create a new JSONObject either directly or from a local file/URL:
json_data = js.JSONObject(
    {
        "data": [
            {
                "name": "Dan",
                "birthday": "1991-01-02 09:00:00",
                "publications": 15
            },
            {
                "name": "Mar",
                "birthday": "1991-03-02 12:30:00",
                "publications": 13
            },
            {
                "name": "Carl",
                "birthday": "1950-06-02 16:00:00",
                "publications": 36
            },
            {
                "name": "Vic",
                "birthday": "1986-07-02 16:00:00",
                "publications": None
            },
        ]
    }
)

# Now we can navegate through this object by attribute accesion:
json_data.data._1.name
# 'Mar'

# Or we can make queries. The syntax is very similar to Django's querysets:
result = json_data.query(birthday__lt=datetime(1985,1,1))

result
# <QuerySet ['1950-06-02 16:00:00']>

result.first().parent
# {'name': 'Carl', 'birthday': '1950-06-02 16:00:00', 'publications': 36}

# We can also retrieve the path of a node:
result.first().jsonpath
# data/2/
```

# Documentation

Detailed documentation is available at [json-enhanced.readthedocs.io](https://json-enhanced.readthedocs.io/en/latest).

# Contributing

Contributions are welcome! Please take a look at our contributors guide.

# Code of Conduct

Please read [CODE_OF_CONDUCT.md](https://github.com/Collisio/json-enhanced/CODE_OF_CONDUCT.md) for details on our code of conduct.

# License

This project is licensed under the *GPL-3.0 License*. For details, please read our [LICENSE FILE](https://github.com/Collisio/json-enhanced/LICENSE).
