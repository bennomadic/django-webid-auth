import os
import sys

from os.path import abspath, dirname, join
from site import addsitedir

import django.core.handlers.wsgi
from django.conf import settings

sys.stdout = sys.stderr

sys.path.insert(0, abspath(join(dirname(__file__), "../../../")))
sys.path.insert(0, abspath(join(dirname(__file__), "../../")))


print sys.path

os.environ["DJANGO_SETTINGS_MODULE"] = "example_webid_auth.settings"

_application = django.core.handlers.wsgi.WSGIHandler()

def application(environ, start_response):
    if environ.get("HTTP_X_FORWARDED_PROTOCOL") == "https" or environ.get("HTTP_X_FORWARDED_SSL") == "on":
        environ["wsgi.url_scheme"] = "https"
#       environ['wsgi.url_scheme'] = environ.get('HTTP_X_URL_SCHEME', 'http')
    return _application(environ, start_response)

