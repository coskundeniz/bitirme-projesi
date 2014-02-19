# -*- coding: utf-8 -*-

import os

DEBUG = True
SECRET_KEY = '\x0f v\xa5!\xb8*\x14\xfeY[\xaf\x83\xd4}vv*\xfb\x85'

abs_path = os.path.abspath('app.db')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + abs_path

# config for forms
CSRF_ENABLED = True
CSRF_SESSION_KEY = '\x0f v\xa5!\xb8*\x14\xfeY[\xaf\x83\xd4}vv*\xfb\x85'

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads/")
