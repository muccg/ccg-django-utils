import os
import sys
import unittest
import tempfile
from io import StringIO

from ccg_django_utils.conf import *

class SetupProdEnvTests(unittest.TestCase):
    def setup_test_file(self):
        conf = tempfile.NamedTemporaryFile(delete=False, mode="w")
        conf.write("""
qwerty=asdf
asdf = 42
foo = bar baz
# this is a comment
some setting = zxc
testing=TRUE
bored=1
fun=no
dbname=pgsql
""")
        conf.flush()
        self.addCleanup(os.remove, conf.name)
        return conf.name

    def setUp(self):
        self.conf = self.setup_test_file()
        setup_prod_env("testproj", self.conf)
        self.env = EnvConfig()

    def test_set_env(self):
        self.assertEqual(os.environ["QWERTY"], "asdf")
        self.assertEqual(os.environ["ASDF"], "42")
    def test_value_space(self):
        self.assertEqual(os.environ["FOO"], "bar baz")
    def test_key_space(self):
        self.assertEqual(os.environ["SOME SETTING"], "zxc")
    def test_django_settings(self):
        self.assertEqual(os.environ["DJANGO_SETTINGS_MODULE"], "testproj.prodsettings")

    def test_get_env(self):
        self.assertEqual(self.env.get("qwerty"), "asdf")
    def test_get_int(self):
        self.assertEqual(self.env.get("asdf"), "42")
        self.assertEqual(self.env.get("asdf", 0), 42)
    def test_get_bool(self):
        self.assertTrue(self.env.get("testing", False))
        self.assertTrue(self.env.get("bored", False))
        self.assertFalse(self.env.get("fun", True))
    def test_get_list(self):
        self.assertEqual(self.env.getlist("foo"), ["bar", "baz"])
    def test_get_no_exist(self):
        from django.core.exceptions import ImproperlyConfigured
        self.assertRaises(ImproperlyConfigured, self.env.get, "coffee")
        self.assertRaises(ImproperlyConfigured, self.env.getlist, "coffee")
    def test_get_default(self):
        self.assertEqual(self.env.get("coffee", "espresso"), "espresso")
    def test_get_list_default(self):
        self.assertEqual(self.env.getlist("coffee", ["espresso", "macchiato"]), ["espresso", "macchiato"])
    def test_get_db_engine(self):
        self.assertEqual(self.env.get_db_engine("dbname", "sqlite3"), "django.db.backends.postgresql_psycopg2")
    def test_get_db_engine_default(self):
        self.assertEqual(self.env.get_db_engine("sqdb", "sqlite3"), "django.db.backends.sqlite3")

    def test_missing_conf_file(self):
        old, sys.stderr = sys.stderr, StringIO()
        setup_config_env("/tmp/lahlah")
        sys.stderr.seek(0)
        messages = sys.stderr.read()
        sys.stderr = old
        self.assertTrue(messages.startswith("load_config"))

if __name__ == '__main__':
    unittest.main()
