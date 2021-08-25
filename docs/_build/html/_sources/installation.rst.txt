Installation & Quickstart
=========================

Pip installation
----------------

This package can be installed via pip, by simply typing:

``pip install json-enhanced``

Docker's set up
---------------

Additionally, if you have Docker installed on your Linux system, we provide a bash script, called ``build.sh``,
which comes preloaded with the entire ecosystem of the library; the main modules and objects, and a predefined ``test`` variable with some json data.
You can access an Ipython terminal by entering the following command:

``bash build.sh``

Also, if you want to load a local resource from your host system into the container, you can point to it with an additional argument on the script's call:

``bash build.sh <resource_path>``

Quickstart
----------

To start, we import the module into our workspace:

``import jsonutils as js``

There are different ways to load a JSON object in our interpreter:

* By directly entering the corresponding Python object in the constructor

.. code-block:: python

    json_object = js.JSONObject(
        {
            "data": [
                {
                    "name": "Daniel",
                    "age": 30,
                    "hobbies": ["music", "reading", "football"]
                },
                {
                    "name": "Gloria",
                    "age": 25,
                    "hobbies": ["tennis", "music", "programming"]
                }
            ]
        }
    )

* By calling the method ``open`` of ``JSONObject`` class. This method detects whether the argument entered
  corresponds to a local path or a remote web page.

  .. code-block:: python

    json_object = js.JSONObject.open("<path_of_json_file>") # to open a local json file

    json_object = js.JSONObject.open("<url_of_json_file>") # to open a remote url json file

  if requesting a remote url, it must include http or https protocol in order to be validated.

Once the json data has been loaded as a ``JSONNode`` instance, we will be able to perform some useful things,
such as browsing the nested object by attribute access with autocompletion features:

.. code-block:: python

    >> json_object.data._0.hobbies._1
        'reading'

    >> json_object.data._1.name
        'Gloria'

Or changing node elements as we want:

.. code-block:: python

    >> json_object.data._0.hobbies._1 = "SLEEPING"

    >> json_object
        {
            "data": [
                {
                    "name": "Daniel",
                    "age": 30,
                    "hobbies": ["music", "SLEEPING", "football"]
                },
                {
                    "name": "Gloria",
                    "age": 25,
                    "hobbies": ["tennis", "music", "programming"]
                }
            ]
        }

But probably the most important feature is the ability to make queries, following a syntax
similar to the one offered by Django's ORM. Let's see some examples:

.. code-block:: python

    >> json_object.query(hobbies__contains="football")
        <QuerySet [['music', 'SLEEPING', 'football']]>

    >> json_object.query(age__lt=30, include_parent_=True).first() # retrieving the first query result including parent object (the inner dict)
        {'name': 'Gloria', 'age': 25, 'hobbies': ['tennis', 'music', 'programming']}

    >> json_object.query(name__regex=r"(?:Daniel|Gloria)")
        <QuerySet ['Daniel', 'Gloria']>

    >> json_object.query(hobbies__contains="music").count() # counting the number of nodes with 'music' as hobbie
        2

    >> json_object.query(hobbies=js.All).update(None) # updating all hobbies nodes to null values

    >> json_object
        {
            "data": [
                {
                    "name": "Daniel",
                    "age": 30,
                    "hobbies": None
                },
                {
                    "name": "Gloria",
                    "age": 25,
                    "hobbies": None
                }
            ]
        }