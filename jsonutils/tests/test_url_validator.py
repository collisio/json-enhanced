import unittest

from jsonutils.functions.parsers import parse_http_url, url_validator


class JsonTest(unittest.TestCase):
    def test_http(self):
        self.assertTrue(url_validator("http://www.google.es"))
        self.assertTrue(url_validator("http://google.es"))
        self.assertTrue(url_validator("http://google.com"))
        self.assertTrue(url_validator("http://198.165.1.32"))

        self.assertFalse(url_validator("http://www.google._com"))
        self.assertFalse(url_validator("http://www.goo."))

    def test_ftp(self):
        self.assertTrue(url_validator("ftp://ftp.com"))
        self.assertTrue(url_validator("ftp://192.168.1.32"))

    def test_nohttp(self):
        self.assertTrue(url_validator("www.google.es", optative_protocol=True))
        self.assertTrue(url_validator("google.es", optative_protocol=True))
        self.assertFalse(url_validator("192.168.1.32"))
        self.assertFalse(url_validator("www.google.es"))

    def test_parse_http_url(self):

        self.assertEqual(parse_http_url("www.example.com"), "http://www.example.com")
        self.assertEqual(parse_http_url("example.com"), "http://example.com")
        self.assertEqual(parse_http_url("http://example.com"), "http://example.com")
        self.assertEqual(parse_http_url("https://example.com"), "https://example.com")

        self.assertRaisesRegex(
            Exception,
            "Url's protocol is not http: ftp",
            lambda: parse_http_url("ftp://www.example.com"),
        )
        self.assertRaisesRegex(
            Exception,
            "Can't parse a valid url",
            lambda: parse_http_url(".example.com"),
        )

        self.assertIsNone(parse_http_url(".example.com", fail_silently=True))
