#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, g
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, current_user


app = Flask(__name__)
app.config.from_object('config')

# set database and login manager instances
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "users.login"

# assign config data in wf_config.xml to read file once
from application.utils import get_config_data
config_data = get_config_data()

from application.utils import get_all_specs
workflow_specs = get_all_specs()

# register blueprints on app
from users.views import mod as user_bp
app.register_blueprint(user_bp, url_prefix='/user')

from pdf_forms.views import mod as form_bp
app.register_blueprint(form_bp, url_prefix='/form')


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.before_request
def before_request():
    g.user = current_user

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404
