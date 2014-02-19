# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import TextField, PasswordField
from wtforms.validators import Required, EqualTo


class LoginForm(Form):

    username = TextField('username', validators=[Required()])
    password = PasswordField('password', validators=[Required()])


class RegistrationForm(Form):

    username = TextField('username', validators=[Required()])
    password = PasswordField('password', validators=[Required()])
    confirm_password = PasswordField('confirm password', validators=[Required(),
                            EqualTo('password', message='Passwords must match')])
