# -*- coding: utf-8 -*-

from application.app import app, db
from application.workflow.models import ProjectSpec, WorkflowState
from application.users.models import User, Transaction
from application.pdf_forms.models import Pdf
from application.constants import ROLE_INSTRUCTOR, ROLE_ADMIN

from SpiffWorkflow import Workflow
from SpiffWorkflow.storage.DictionarySerializer import DictionarySerializer
from datetime import datetime
from uuid import uuid4


class DBTasks(object):

    def drop_create(self):
        db.drop_all()
        db.create_all()

    def add_user(self):

        # add a student
        self.student = User("coskun", "deniz")
        self.student.add()

        # add an instructor
        self.instructor = User("instructor", "i#ins", role=ROLE_INSTRUCTOR)
        self.instructor.add()

        # add an admin
        self.admin = User("admin", "a#admin", role=ROLE_ADMIN)
        self.admin.add()

    def add_workflow(self):

        workflow = Workflow(ProjectSpec())
        serializer = DictionarySerializer()
        serialized_wf = workflow.serialize(serializer)
        self.workflow_id = str(uuid4())

        # 1 -> user_id
        # 2 -> instructor_id
        db_wf = WorkflowState(self.workflow_id, serialized_wf, 1, 2)
        db_wf.add()

    def add_transaction(self):

        self.transaction_id = str(uuid4())
        date_time = datetime.now()
        wf_id = self.workflow_id

        db_transaction = Transaction(self.transaction_id, date_time, wf_id)
        db_transaction.add()

    def add_pdf(self):

        pdf_id = str(uuid4())
        file_name = "bitirme_istek_formu.pdf"
        transaction_id = self.transaction_id

        db_pdf = Pdf(pdf_id, file_name, app.config['UPLOAD_FOLDER'], transaction_id)
        db_pdf.add()

    def try_add(self):

        self.add_user()
        self.add_workflow()
        self.add_transaction()
        self.add_pdf()

    def dump_db(self):
        """ dump all content of database """

        # dump users
        print " ..::: Printing Users :::.. "

        users = User.query.all()
        for user in users:
            print "id:       %d" % user.id
            print "username: %s" % user.username
            print "password: %s" % user.password
            print "role:     %d\n" % user.role

        print " ..::: Printing Workflows :::.. "

        workflows = WorkflowState.query.all()
        for workflow in workflows:
            print "id: %s" % workflow.workflow_id
            print "instance: ",
            print workflow.workflow_instance
            print "user id:       %d" % workflow.user_id
            print "instructor id: %d\n" % workflow.instructor_id

        print " ..::: Printing Transactions :::.. "

        transactions = Transaction.query.all()
        for transaction in transactions:
            print "transaction id: %s" % transaction.transaction_id
            print "date: %s" % str(transaction.datetime)
            print "workflow id: %s\n" % transaction.workflow_id

        print " ..::: Printing Pdfs :::.. "

        pdfs = Pdf.query.all()
        for pdf in pdfs:
            print "pdf id: %s" % pdf.pdf_id
            print "filename: %s" % pdf.name
            print "filepath: %s" % pdf.path
            print "transaction id: %s\n" % pdf.transaction_id

        print " ..::: Trying Relation Variables :::.. "
        wf = WorkflowState.query.first()
        print wf.user_id_rel

        for item in wf.transactions.all():
            print item

        transaction = Transaction.query.first()
        for item in transaction.pdfs.all():
            print item


if __name__ == '__main__':

    dbtasks = DBTasks()
    dbtasks.drop_create()
    dbtasks.add_user()
