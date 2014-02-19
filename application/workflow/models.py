# -*- coding: utf-8 -*-

from SpiffWorkflow.specs import *


class ProjectSpec(WorkflowSpec):

    def __init__(self, name="Bitirme"):
        super(ProjectSpec, self).__init__(name)

        self.create_wf_spec()

    def create_wf_spec(self):

        # create first task and connect to start task
        send_request_form = Simple(self, 'send_request_form')
        self.start.connect(send_request_form)

        form_approval = Simple(self, 'approve_form_task')
        send_request_form.connect(form_approval)

        # add last task
        last = Simple(self, 'last_task')
        form_approval.connect(last)


from application.app import db
class WorkflowState(db.Model):

    __tablename__ = "workflow"

    workflow_id       = db.Column(db.String(40), primary_key=True)
    workflow_instance = db.Column(db.PickleType)
    user_id           = db.Column(db.Integer, db.ForeignKey('user.id'))
    instructor_id     = db.Column(db.Integer, db.ForeignKey('user.id'))

    user_id_rel = db.relationship('User', foreign_keys=[user_id])
    instructor_id_rel = db.relationship('User', foreign_keys=[instructor_id])
    transactions = db.relationship('Transaction', backref='workflow', lazy='dynamic')

    def __init__(self, workflow_id=None, workflow_instance=None,
                       user_id=None, instructor_id=None):
        self.workflow_id = workflow_id
        self.workflow_instance = workflow_instance
        self.user_id = user_id
        self.instructor_id = instructor_id

    def add(self):
        db.session.add(self)
        db.session.commit()


