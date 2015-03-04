"""ccg_django_utils.conf -- Django settings util functions.

This module contains helper functions for working with environment
variable configuration of a Django app.

The goal is to use simple key-value settings so that the Django app
can be deployed in multiple scenarios with minimum fussing around
settings files. This simplification also helps makes the dev settings
more like production settings.

When deploying your application, you need to put the settings into the
web application's environment. Typically you would call
setup_prod_env() or setup_config_env() from both the WSGI handler and
the management script. These functions load settings from a simple
config file.

The Django settings module then gets configuration from the
environment. The ``EnvConfig`` class provides a methods to do this.


References:
 * http://12factor.net/config
 * http://12factor.net/dev-prod-parity
 * https://devcenter.heroku.com/articles/getting-started-with-django#django-settings
 * https://github.com/twoscoops/django-twoscoops-project/blob/2910cb96/project_name/project_name/settings/production.py

"""

import os
import sys
from six.moves.configparser import ConfigParser
from six import StringIO

__all__ = ["EnvConfig", "setup_prod_env", "setup_config_env"]

def setup_prod_env(project_name, config_file=None, package_name=None):
    """
    Sets environment variables for the web app according to conventions.
    """
    package_name = package_name or project_name

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '%s.prodsettings' % package_name)
    os.environ.setdefault('PYTHON_EGG_CACHE', '/tmp/.python-eggs')

    # ccg.utils.webhelpers expects SCRIPT_NAME to be a path such as /project-name
    # This is a fallback value if the variable isn't set through wsgi.
    os.environ.setdefault("SCRIPT_NAME", "/" + project_name)

    os.environ["PROJECT_NAME"] = project_name
    os.environ["PRODUCTION"] = "1"

    # set up the environment with settings loaded from a config file.
    config_file = config_file or "/etc/%s/%s.conf" % (project_name, project_name)
    setup_config_env(config_file)

def setup_config_env(config_file):
    """
    Loads settings from a key-value config file into environment
    variables.
    """
    for key, val in load_config(config_file):
        os.environ[key.upper()] = val

def load_config(filename):
    section = "root"

    try:
        config_text = "[%s]\n%s" % (section, open(filename).read())
    except IOError as e:
        sys.stderr.write("load_config: %s\n" % e)
        config_text = "[%s]\n" % section

    config = ConfigParser()
    config.readfp(StringIO(config_text))

    return config.items(section)

# global stash of environment variables which we have taken out of the
# environment, but which we may still need to be able to access later
envconfig_stash = {}

class EnvConfig(object):
    def get(self, setting, default=None, delete=True):
        """
        Get the environment setting, return a default value, or raise
        an exception.
        Values used by this function will likely come from a conf file in /etc.

        If 'delete' is True (the default), the setting is deleted from the
        environment to avoid data leaks.
        """

        # simple conversion of values to numbers or bool
        if isinstance(default, bool):
            conv = lambda v: v.lower()[0:1] in ("1", "y", "t")
        elif isinstance(default, (int, float)):
            conv = type(default)
        else:
            conv = lambda x: x

        return self._get_setting(setting, default, conv, delete)

    def getlist(self, setting, default=None, delete=True):
        return self._get_setting(setting, default, lambda x: x.split(), delete)

    def _get_setting(self, setting, default, conv, delete):
        def _get_raw():
            if setting in envconfig_stash:
                return envconfig_stash[setting]
            raw = self[setting]
            if delete:
                envconfig_stash[setting] = raw
                del self[setting]
            return raw
        try:
            return conv(_get_raw())
        except KeyError:
            if default is None:
                from django.core.exceptions import ImproperlyConfigured
                error_msg = "Set the %s env variable" % setting
                raise ImproperlyConfigured(error_msg)
            else:
                return default

    def __getitem__(self, setting):
        # make settings case-insensitive
        setting = setting.upper()
        return os.environ[setting]

    def __hasitem__(self, setting):
        return setting.upper() in os.environ

    def __delitem__(self, setting):
        setting = setting.upper()
        if setting in os.environ:
            del os.environ[setting]

    def get_db_engine(self, setting, default):
        """
        Gets the environment setting for database engine and maps it to a
        Django database backend class.
        Possible values are: pgsql, mysql, sqlite3.
        """
        engines = {
            'pgsql': 'django.db.backends.postgresql_psycopg2',
            'mysql': 'django.db.backends.mysql',
            'sqlite3': 'django.db.backends.sqlite3',
        }
        return engines.get(self.get(setting, ""), engines[default])
