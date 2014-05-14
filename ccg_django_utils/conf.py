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
import ConfigParser
import StringIO

__all__ = ["EnvConfig", "setup_prod_env", "setup_config_env"]

def setup_prod_env(project_name, config_file=None):
    """
    Sets environment variables for the web app according to conventions.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '%s.prodsettings' % project_name)
    os.environ.setdefault('PYTHON_EGG_CACHE', '/tmp/.python-eggs')

    # ccg.utils.webhelpers expects SCRIPT_NAME to be a path such as /project-name
    # This is a fallback value if the variable isn't set through wsgi.
    os.environ.setdefault("SCRIPT_NAME", "/" + project_name)

    os.environ["PROJECT_NAME"] = project_name

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
    except IOError:
        config_text = "[%s]\n" % section

    config = ConfigParser.ConfigParser()
    config.readfp(StringIO.StringIO(config_text))

    return config.items(section)

class EnvConfig(object):

    def get(self, setting, default=None):
        """
        Get the environment setting, return a default value, or raise
        an exception.
        Values used by this function will likely come from a conf file in /etc.
        """
        # fixme: use type of default to choose output type
        setting = setting.upper()
        try:
            return os.environ[setting]
        except KeyError:
            if default is None:
                from django.core.exceptions import ImproperlyConfigured
                error_msg = "Set the %s env variable" % setting
                raise ImproperlyConfigured(error_msg)
            else:
                return default

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
