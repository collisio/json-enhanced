Comparison with other related libraries
=======================================

There are other libraries that implement similar functionality to that of json-enhanced,
but all of them use their own syntax for querying data, whereas json-enhanced uses a purely Python syntax,
based on Django's ORM.

Let's see a quick usage comparison between the different related packages.

jsonpath-ng
-----------

Perhaps the most used library to cover this type of needs.
Following the example concerning authors and books, published on its web site:

.. code-block:: python
    :caption: with jsonpath-ng

    data = {
        "store": {
            "book": [
                {
                    "category": "reference",
                    "author": "Nigel Rees",
                    "title": "Sayings of the Century",
                    "price": 8.95
                },
                {
                    "category": "fiction",
                    "author": "Evelyn Waugh",
                    "title": "Sword of Honour",
                    "price": 12.99
                },
                {
                    "category": "fiction",
                    "author": "Herman Melville",
                    "title": "Moby Dick",
                    "isbn": "0-553-21311-3",
                    "price": 8.99
                },
                {
                    "category": "fiction",
                    "author": "J. R. R. Tolkien",
                    "title": "The Lord of the Rings",
                    "isbn": "0-395-19395-8",
                    "price": 22.99
                }
            ],
            "bicycle": {
                "color": "red",
                "price": 19.95
            }
        }
    }

    from jsonpath_ng.ext import parse

    # retrieving the authors of all books in the store
    query_all_book_authors = parse("$.store.book[*].author")

    >> [match.value for match in query_all_book_authors.find(data)]
        ['Nigel Rees', 'Evelyn Waugh', 'Herman Melville', 'J. R. R. Tolkien']

    # getting the json path of the first author
    >> str(query_all_book_authors.find(data)[0].full_path)
        'store.book.[0].author'

    # filter all books with isbn number
    query_isbn_books = parse("$..book[?(@.isbn)]")

    >> [match.value for match in query_isbn_books.find(data)]
        [{'category': 'fiction',
        'author': 'Herman Melville',
        'title': 'Moby Dick',
        'isbn': '0-553-21311-3',
        'price': 8.99},
        {'category': 'fiction',
        'author': 'J. R. R. Tolkien',
        'title': 'The Lord of the Rings',
        'isbn': '0-395-19395-8',
        'price': 22.99}] 

.. code-block:: python
    :caption: with json-enhanced

    import jsonutils as js

    data = js.JSONObject(data) # load previous data as a JSONNode instance

    # retrieving the authors of all books in the store
    >> data.store.book.query(author=js.All) # just one statement
        <QuerySet ['Nigel Rees', 'Evelyn Waugh', 'Herman Melville', 'J. R. R. Tolkien']>

    # getting the json path of the first author
    >> data.store.book.query(author=js.All).first().jsonpath
        store/book/0/author/

    # or if we want a python path expression
    >> data.store.book.query(author=js.All).first().jsonpath.expr
        '["store"]["book"][0]["author"]'

    # filter all books with isbn number
    >> data.store.book.query(isbn__isnull=False, include_parent_=True)
        <QuerySet [{'category': 'fiction', 'author': 'Herman Melville', 'title': 'Moby Dick', 'isbn': '0-553-21311-3', 'price': 8.99}, {'category': 'fiction', 'author': 'J. R. R. Tolkien', 'title': 'The Lord of the Rings', 'isbn': '0-395-19395-8', 'price': 22.99}]>

objectpath
----------

This library is currently out of maintenance. Its syntax is very similar to that of jsonpath-ng.
Let's compare its functionality following the example of json above.

.. code-block:: python
    :caption: with objectpath

    from objectpath import Tree

    tree = Tree(data) # loading the data above

    # retrieving books with price greater than 12
    >> list(tree.execute("$.store.book[@.price > 12]"))
        [{'category': 'fiction',
        'author': 'Evelyn Waugh',
        'title': 'Sword of Honour',
        'price': 12.99},
        {'category': 'fiction',
        'author': 'J. R. R. Tolkien',
        'title': 'The Lord of the Rings',
        'isbn': '0-395-19395-8',
        'price': 22.99}]

.. code-block:: python
    :caption: with json-enhanced

    import jsonutils as js

    data = js.JSONObject(data)

    # retrieving books with price greater than 12
    >> data.store.book.query(price__gt=12) # without including parent nodes
        <QuerySet [12.99, 22.99]>

    # getting the last element's parent
    >> data.store.book.query(price__gt=12).last().parent
        {'category': 'fiction',
        'author': 'J. R. R. Tolkien',
        'title': 'The Lord of the Rings',
        'isbn': '0-395-19395-8',
        'price': 22.99}

pandas
------

The pandas library offers very user-friendly tools for querying structured data.
The main problem is that it can only properly read data that has a defined structure (which can be converted to a dataframe).
In the case we are concerned with, we could proceed as follows:


.. code-block:: python
    :caption: with pandas

    import pandas as pd

    df = pd.json_normalize(data, ["store", ["book"]])

    >> df
            category            author                   title  price           isbn
        0  reference        Nigel Rees  Sayings of the Century   8.95            NaN
        1    fiction      Evelyn Waugh         Sword of Honour  12.99            NaN
        2    fiction   Herman Melville               Moby Dick   8.99  0-553-21311-3
        3    fiction  J. R. R. Tolkien   The Lord of the Rings  22.99  0-395-19395-8

    # filter books with no isbn
    >> df.query("isbn.isna()")
            category        author                   title  price isbn
        0  reference    Nigel Rees  Sayings of the Century   8.95  NaN
        1    fiction  Evelyn Waugh         Sword of Honour  12.99  NaN

    # filter books whose title contains the string "the" and has a valid ISBN
    >> df.query("title.str.contains('the') & isbn.isna() == False")
        category            author                  title  price           isbn
        3  fiction  J. R. R. Tolkien  The Lord of the Rings  22.99  0-395-19395-8

.. code-block:: python
    :caption: with json-enhanced

    import jsonutils as js

    data = js.JSONObject(data) # load the data into JSONNode instance

    # filter books with no isbn
    >> data.store.book.annotate(isbn=None).query(isbn__isnull=True, include_parent_=True)
        <QuerySet [{'category': 'reference', 'author': 'Nigel Rees', 'title': 'Sayings of the Century', 'price': 8.95, 'isbn': None}, {'category': 'fiction', 'author': 'Evelyn Waugh', 'title': 'Sword of Honour', 'price': 12.99, 'isbn': None}]>