# -*- coding: utf-8 -*-

from flask.ext.login import UserMixin

from application.constants import ROLE_STUDENT
from application.app import db


class User(UserMixin, db.Model):

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(40))
    role = db.Column(db.SmallInteger)

    def __init__(self, username=None, password=None, role=ROLE_STUDENT):
        self.username = username
        self.password = password
        self.role     = role

    def get_user(self, username=None):
        return self.query.filter_by(username=username).first()

    def add(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return '<User %r>' % self.username


class Transaction(db.Model):

    __tablename__ = "transaction"

    transaction_id = db.Column(db.String(40), primary_key=True)
    datetime = db.Column(db.DateTime)
    workflow_id = db.Column(db.String(40), db.ForeignKey('workflow.workflow_id'))
    pdfs = db.relationship('Pdf', backref='transaction', lazy='dynamic')

    def __init__(self, transaction_id=None, datetime=None, workflow_id=None):
        self.transaction_id = transaction_id
        self.datetime       = datetime
        self.workflow_id    = workflow_id

    def add(self):
        db.session.add(self)
        db.session.commit()
