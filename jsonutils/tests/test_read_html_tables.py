import unittest
from jsonutils.base import JSONObject
import jsonutils as js


class JsonTest(unittest.TestCase):
    def test_read_html_with_headers(self):
        table = """\
<table id="id-table">
  <tr>
    <th>Company</th>
    <th>Contact</th>
    <th>Country</th>
  </tr>
  <tr>
    <td>Alfreds Futterkiste</td>
    <td>Maria Anders</td>
    <td>Germany</td>
  </tr>
  <tr>
    <td>Centro comercial Moctezuma</td>
    <td>Francisco Chang</td>
    <td>Mexico</td>
  </tr>
</table>\
"""

        self.assertEqual(
            JSONObject.read_html_table(table, attrs={"id": "id-table"}),
            JSONObject(
                [
                    {
                        "Company": "Alfreds Futterkiste",
                        "Contact": "Maria Anders",
                        "Country": "Germany",
                    },
                    {
                        "Company": "Centro comercial Moctezuma",
                        "Contact": "Francisco Chang",
                        "Country": "Mexico",
                    },
                ]
            ),
        )

    def test_html_without_headers(self):
        table = """\
<table id="id-table">
  <tr>
    <td>Alfreds Futterkiste</td>
    <td>Maria Anders</td>
    <td>Germany</td>
  </tr>
  <tr>
    <td>Centro comercial Moctezuma</td>
    <td>Francisco Chang</td>
    <td>Mexico</td>
  </tr>
</table>\
"""
        self.assertEqual(
            JSONObject.read_html_table(table, attrs={"id": "id-table"}),
            JSONObject(
                [
                    {
                        "0": "Alfreds Futterkiste",
                        "1": "Maria Anders",
                        "2": "Germany",
                    },
                    {
                        "0": "Centro comercial Moctezuma",
                        "1": "Francisco Chang",
                        "2": "Mexico",
                    },
                ]
            ),
        )

    def test_read_links(self):
        table = """\
<table id="id-table">
  <tr>
    <td>Alfreds Futterkiste</td>
    <td><a href="/es/endpoint">Maria Anders</a></td>
    <td>Germany</td>
  </tr>
  <tr>
    <td>Centro comercial Moctezuma</td>
    <td>Francisco Chang</td>
    <td>Mexico</td>
  </tr>
</table>\
"""
        self.assertEqual(
            JSONObject.read_html_table(table, parse_links=True),
            JSONObject(
                [
                    {
                        "0": "Alfreds Futterkiste",
                        "1": "/es/endpoint",
                        "2": "Germany",
                    },
                    {
                        "0": "Centro comercial Moctezuma",
                        "1": "Francisco Chang",
                        "2": "Mexico",
                    },
                ]
            ),
        )
        self.assertEqual(
            JSONObject.read_html_table(
                table, parse_links=True, link_prefix="/pre/prefix/"
            ),
            JSONObject(
                [
                    {
                        "0": "Alfreds Futterkiste",
                        "1": "/pre/prefix/es/endpoint",
                        "2": "Germany",
                    },
                    {
                        "0": "Centro comercial Moctezuma",
                        "1": "Francisco Chang",
                        "2": "Mexico",
                    },
                ]
            ),
        )
