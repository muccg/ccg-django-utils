# CCG Django Utils

[![Build Status](https://travis-ci.org/muccg/django-useraudit.svg)](https://travis-ci.org/muccg/ccg-django-utils) [![PyPI](https://badge.fury.io/py/ccg-django-utils.svg)](https://pypi.python.org/pypi/ccg-django-utils)

Miscellaneous utility code used by the [Centre for Comparative
Genomics] [1] in our Django applications.

It's all contained in the ``ccg_django_utils`` module.

## Environment Settings for Django

Use simple environment variables to control django settings. For
example:

```python
# settings.py
from ccg_django_utils.conf import EnvConfig
env = EnvConfig()

DATABASES = {
    'default': {
        'ENGINE': env.get_db_engine("dbtype", "pgsql"),
        'NAME': env.get("dbname", "myapp"),
        'USER': env.get("dbuser", "myapp"),
        'PASSWORD': env.get("dbpass", "myapp"),
        'HOST': env.get("dbserver", ""),
        'PORT': env.get("dbport", ""),
    }
}
```

## Log Handler

A file logging handler which automatically creates the necessary
parent directories. For example:

```python
LOGGING['handlers']['file'] = {
    'level': 'INFO',
    'class': 'ccg_django_utils.loghandlers.ParentPathFileHandler',
    'filename': os.path.join(CCG_LOG_DIRECTORY, 'myapp.log'),
    'when': 'midnight',
    'formatter': 'verbose'
}
```

## Misc

A `HttpResponse` subclass with status of 401.

```python
from ccg_django_utils.http import HttpResponseUnauthorized
```

## Webhelpers

Functions for generating URLs with a base path prepended. This should
be deprecated soon.

```python
from ccg_django_utils.webhelpers import url
```

[1]: http://ccg.murdoch.edu.au/
