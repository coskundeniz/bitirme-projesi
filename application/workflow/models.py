# -*- coding: utf-8 -*-

from application.app import db


class WorkflowState(db.Model):

    __tablename__ = "workflow"

    workflow_id       = db.Column(db.String(40), primary_key=True)
    workflow_name     = db.Column(db.String(40))
    workflow_instance = db.Column(db.PickleType)
    user_id           = db.Column(db.Integer, db.ForeignKey('user.id'))
    instructor_id     = db.Column(db.Integer, db.ForeignKey('user.id'))

    user_id_rel = db.relationship('User', foreign_keys=[user_id])
    instructor_id_rel = db.relationship('User', foreign_keys=[instructor_id])
    transactions = db.relationship('Transaction', backref='workflow', lazy='dynamic')

    def __init__(self, workflow_id=None, workflow_name=None, workflow_instance=None,
                       user_id=None, instructor_id=None):
        self.workflow_id       = workflow_id
        self.workflow_name     = workflow_name
        self.workflow_instance = workflow_instance
        self.user_id           = user_id
        self.instructor_id     = instructor_id

    def add(self):
        db.session.add(self)
        db.session.commit()

