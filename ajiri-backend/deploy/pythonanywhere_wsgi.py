# TEMPLATE for the WSGI file on PythonAnywhere.
#
# On the Web tab, click the "WSGI configuration file" link (it is named something like
# /var/www/yourname_pythonanywhere_com_wsgi.py), delete everything in it, and paste
# this in. Replace YOURNAME with your PythonAnywhere username. The Django project is the
# ajiri-backend folder inside the cloned repository (~/ajiri, which is what
# `git clone .../ajiri.git` creates).
#
# No secrets belong in this file: SECRET_KEY and the rest are read from the
# git-ignored `.env` file in the project folder (loaded by config/settings.py).
import os
import sys

project_path = '/home/YOURNAME/ajiri/ajiri-backend'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
