"""
WSGI config for caesar project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os, sys

import locale
print('locale.getdefaultlocale()', locale.getdefaultlocale(), file=sys.stderr)
print('locale.getpreferredencoding()', locale.getpreferredencoding(), file=sys.stderr)



from django.core.wsgi import get_wsgi_application

path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# turn on warnings when upgrading Django, to look for deprecated features
# when you uncomment the part below, the warnings will appear in /var/log/apache2/error.log
# import warnings
# warnings.simplefilter('always')
# warnings.warn('this is a test warning')

application = get_wsgi_application()
