# SPDX-FileCopyrightText: 2017-present SPDX Contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
WSGI config for project src.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
