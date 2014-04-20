# -*- coding: utf-8 -*-

from application.app import db


class WorkflowState(db.Model):

    __tablename__ = "workflow"

    workflow_id       = db.Column(db.String(40), primary_key=True)
    workflow_name     = db.Column(db.String(40))
    workflow_instance = db.Column(db.PickleType)

    transactions = db.relationship('Transaction', backref='workflow', lazy='dynamic')

    def __init__(self, workflow_id=None, workflow_name=None, workflow_instance=None):

        self.workflow_id       = workflow_id
        self.workflow_name     = workflow_name
        self.workflow_instance = workflow_instance

    def add(self):
        db.session.add(self)
        db.session.commit()


class UserWorkflow(db.Model):

    __tablename__ = "userworkflow"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'))
    workflow_id = db.Column(db.String(40), db.ForeignKey('workflow.workflow_id'))

    def __init__(self, user_id=None, workflow_id=None):
        self.user_id     = user_id
        self.workflow_id = workflow_id

    def add(self):
        db.session.add(self)
        db.session.commit()
