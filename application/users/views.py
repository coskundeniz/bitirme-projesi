# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, url_for, redirect, g, flash
from flask.ext.login import login_user, logout_user, login_required

from application.app import app, db, login_manager, config_data, workflow_specs
from application.users.models import User, Transaction
from application.users.forms import LoginForm, RegistrationForm
from application.constants import ROLE_STUDENT, ROLE_ADMIN, ROLE_INSTRUCTOR
from application.workflow.models import WorkflowState, UserWorkflow
from application.pdf_forms.models import Pdf
from application.utils import save_workflow_instance, get_workflow_instance
from application.utils import get_last_workflow_id

from SpiffWorkflow.storage.DictionarySerializer import DictionarySerializer
from SpiffWorkflow import Workflow, Task
from datetime import datetime
from uuid import uuid4
import os


mod = Blueprint('users', __name__)


@login_manager.user_loader
def load_user(userid):
    # user ids in Flask-Login is unicode strings, so
    # convert it to int before sending to Flask-SQLAlchemy
    return User.query.get(int(userid))

@mod.route('/login', methods=['GET', 'POST'])
def login():

    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('.user_page', username=g.user.username))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first_or_404()

        if user.password == form.password.data:
            login_user(user)
            return redirect(url_for('.user_page', username=user.username))

    return render_template('login.html', form=form)

@mod.route('/register', methods=['GET', 'POST'])
def register():

    form = RegistrationForm()
    if form.validate_on_submit():
        if form.password.data.startswith("a#"):
            role = ROLE_ADMIN
        elif form.password.data.startswith("i#"):
            role = ROLE_INSTRUCTOR
        else:
            role = ROLE_STUDENT

        # if a user with this username already exists, return error message
        if not User.query.filter_by(username=form.username.data).first():
            user = User(username=form.username.data,
                        password=form.password.data,
                        role=role)
            user.add()
            return redirect(url_for('index'))

        else:
            flash("A user with same username already exists!")

    return render_template('register.html', form=form)

@mod.route('/<username>')
@login_required
def user_page(username):

    user = User.query.filter_by(username=username).first_or_404()
    content_data = {}

    if user.role == ROLE_ADMIN:
        return render_template('admin.html')

    elif user.role == ROLE_INSTRUCTOR:

        index = 0
        # get id of workflows that user has
        wf_ids = [item.workflow_id for item in UserWorkflow.query.filter_by(user_id=user.id).all()]
        # get all workflows with ids found above
        all_workflows = [WorkflowState.query.get(wf_id) for wf_id in wf_ids]

        if all_workflows:
            for db_wf in all_workflows:
                workflow = get_workflow_instance(db_wf)

                if not workflow.is_completed():

                    # get the last transaction for this workflow
                    transaction = Transaction.query.filter_by(workflow_id=db_wf.workflow_id).all()[-1]

                    # get output pdf
                    output_pdf = Pdf.query.filter_by(transaction_id=transaction.transaction_id).first()

                    # fill content_data dictionary
                    content_data[index] = {}
                    content_data[index]["ready_task"] = workflow.get_tasks(Task.READY)[0]
                    content_data[index]["pdf"] = output_pdf
                    if workflow.data.get("student", None):
                        content_data[index]["student"] = workflow.data.get("student")

                    index += 1

                else:
                    content_data[index] = {}

            return render_template('instructor.html', content_data=content_data)

        else:
            content_data[index] = {}
            return render_template('instructor.html', content_data=content_data)

    else:
        index = 0
        # get id of workflows that user has
        wf_ids = [item.workflow_id for item in UserWorkflow.query.filter_by(user_id=user.id).all()]
        # get all workflows with ids found above
        all_workflows = [WorkflowState.query.get(wf_id) for wf_id in wf_ids]

        if all_workflows:
            for db_wf in all_workflows:
                workflow = get_workflow_instance(db_wf)

                if not workflow.is_completed():
                    # fill content_data dictionary
                    content_data[index] = {}
                    content_data[index]["config_data"] = config_data
                    content_data[index]["ready_task"] = workflow.get_tasks(Task.READY)[0]
                    content_data[index]["completed_tasks"] = workflow.get_tasks(Task.COMPLETED)[::-1]

                    index += 1

                else:
                    content_data[index] = {}
                    content_data[index]["config_data"] = config_data

            return render_template('user.html', content_data=content_data)

        else:
            content_data[index] = {}
            content_data[index]["config_data"] = config_data
            return render_template('user.html', content_data=content_data)

@mod.route('/start/<workflow_name>')
@login_required
def start_workflow(workflow_name):
    """ start workflow for graduation project """

    # create workflow instance
    workflow = Workflow(workflow_specs[workflow_name])

    # complete start task
    start_task = workflow.get_tasks(state=Task.READY)[0]
    workflow.complete_task_from_id(start_task.id)

    # save username in workflow
    workflow.data["student"] = g.user.username

    # save workflow instance to database
    save_workflow_instance(workflow, g.user.id)

    return redirect(url_for('.user_page', username=g.user.username))

@mod.route('/<username>/approve')
@login_required
def approve(username):

    user = User.query.filter_by(username=username).first()
    wf_id = get_last_workflow_id(user.id)
    db_wf = WorkflowState.query.get(wf_id)
    workflow = get_workflow_instance(db_wf)

    # if first workflow is running, complete xor task
    if workflow.spec.name == "Bitirme":
        workflow.complete_next()

    # complete *_multi_instance tasks if not completed
    for task in workflow.get_tasks(state=Task.READY):
        if task.get_name().endswith("multi_instance"):
            workflow.complete_task_from_id(task.id)

    # get ready approve tasks
    ready_approve_tasks = [task for task in workflow.get_tasks(state=Task.READY)
                                 if task.get_name().startswith("approve")]
    if ready_approve_tasks:
        # store an information on workflow to not to show multiple approve
        # tasks to instructor once it was approved or rejected
        workflow.data[g.user.username] = ready_approve_tasks[0].get_name()
        # complete an approve task
        workflow.complete_task_from_id(ready_approve_tasks[0].id)

    # complete approve join task
    if workflow.get_tasks(state=Task.READY)[0].get_name().endswith("join"):
        workflow.complete_next()

        # cancel remaining reject tasks
        reject_tasks = [task for task in workflow.get_tasks(state=Task.READY)
                              if task.get_name().startswith("reject")]
        for task in reject_tasks:
            task.cancel()

        # get last pdf sent
        transaction = Transaction.query.filter_by(workflow_id=db_wf.workflow_id).all()[-1]
        pdf = Pdf.query.filter_by(transaction_id=transaction.transaction_id).first()

        # create transaction and add
        transaction_id = str(uuid4())
        new_transaction = Transaction(transaction_id, datetime.now(), db_wf.workflow_id)
        new_transaction.add()

        # create pdf object for database and add
        new_pdf = Pdf(str(uuid4()), pdf.name, app.config['UPLOAD_FOLDER'], transaction_id)
        new_pdf.add()

    # if last task reached, complete workflow
    if workflow.get_tasks(state=Task.READY)[0].get_name() == "End":
        workflow.complete_next()

    # update workflow on database
    serialized_wf = workflow.serialize(serializer=DictionarySerializer())
    db_wf.workflow_instance = serialized_wf
    db.session.commit()

    if workflow.spec.name == "Bitirme":
        #get last pdf sent
        transaction = Transaction.query.filter_by(workflow_id=db_wf.workflow_id).all()[-1]
        pdf = Pdf.query.filter_by(transaction_id=transaction.transaction_id).first()

        # create transaction and add
        transaction_id = str(uuid4())
        new_transaction = Transaction(transaction_id, datetime.now(), db_wf.workflow_id)
        new_transaction.add()

        # create pdf object for database and add
        new_pdf = Pdf(str(uuid4()), pdf.name, app.config['UPLOAD_FOLDER'], transaction_id)
        new_pdf.add()

    return redirect(url_for('.user_page', username=g.user.username))

@mod.route('/<username>/reject')
@login_required
def reject(username):

    user = User.query.filter_by(username=username).first()
    wf_id = get_last_workflow_id(user.id)
    db_wf = WorkflowState.query.get(wf_id)
    workflow = get_workflow_instance(db_wf)

    # if first workflow is running, update *_approved variable and complete xor task
    if workflow.spec.name == "Bitirme":
        ready_task = workflow.get_tasks(state=Task.READY)[0]
        ready_task.set_data(**{ready_task.task_spec.pre_assign[0].left_attribute: "False"})
        workflow.complete_next()

    # complete *_multi_instance tasks if not completed
    for task in workflow.get_tasks(state=Task.READY):
        if task.get_name().endswith("multi_instance"):
            workflow.complete_task_from_id(task.id)

    # get ready reject tasks
    ready_reject_tasks = [task for task in workflow.get_tasks(state=Task.READY)
                                if task.get_name().startswith("reject")]
    if ready_reject_tasks:
        # store an information on workflow not to show multiple approve
        # tasks to instructor once it was approved or rejected
        workflow.data[g.user.username] = ready_reject_tasks[0].get_name()
        # complete a reject task
        workflow.complete_task_from_id(ready_reject_tasks[0].id)

    # complete reject join task
    for task in workflow.get_tasks(state=Task.READY):
        if task.get_name().endswith("join"):
            workflow.complete_task_from_id(task.id)

            # cancel remaining approve tasks
            approve_tasks = [ready_task for ready_task in workflow.get_tasks(state=Task.READY)
                                         if ready_task.get_name().startswith("approve")]
            for approve_task in approve_tasks:
                approve_task.cancel()

            # set *_rejected variable as True
            reject_xor = workflow.get_tasks(state=Task.READY)[0]
            reject_xor.set_data(**{reject_xor.task_spec.pre_assign[0].left_attribute: "True"})
            workflow.complete_task_from_id(reject_xor.id)

            # if reject_join completed, delete rejected pdf from database and local folder
            transaction = Transaction.query.filter_by(workflow_id=db_wf.workflow_id).all()[-1]
            pdf = Pdf.query.filter_by(transaction_id=transaction.transaction_id).first()

            # delete both pdf and fdf files
            os.remove("%s" % os.path.join(pdf.path, pdf.name))
            if os.path.exists(os.path.join(pdf.path, pdf.name.replace("pdf", "fdf"))):
                os.remove("%s" % os.path.join(pdf.path, pdf.name.replace("pdf", "fdf")))
            pdf.delete()

    # update workflow on database
    serialized_wf = workflow.serialize(serializer=DictionarySerializer())
    db_wf.workflow_instance = serialized_wf
    db.session.commit()

    if workflow.spec.name == "Bitirme":
        #if reject_join completed, delete rejected pdf from database and local folder
        transaction = Transaction.query.filter_by(workflow_id=db_wf.workflow_id).all()[-1]
        pdf = Pdf.query.filter_by(transaction_id=transaction.transaction_id).first()

        # delete both pdf and fdf files
        os.remove("%s" % os.path.join(pdf.path, pdf.name))
        if os.path.exists(os.path.join(pdf.path, pdf.name.replace("pdf", "fdf"))):
            os.remove("%s" % os.path.join(pdf.path, pdf.name.replace("pdf", "fdf")))
        pdf.delete()

    return redirect(url_for('.user_page', username=g.user.username))

@mod.route('/send_pdf/<filename>')
@login_required
def send_pdf(filename):

    user = User.query.filter_by(username=g.user.username).first()
    wf_id = get_last_workflow_id(user.id)
    db_wf = WorkflowState.query.get(wf_id)
    workflow = get_workflow_instance(db_wf)

    # complete send_* task
    workflow.complete_next()

    serialized_wf = workflow.serialize(serializer=DictionarySerializer())
    db_wf.workflow_instance = serialized_wf
    db.session.commit()

    # create transaction and add
    transaction_id = str(uuid4())
    transaction = Transaction(transaction_id, datetime.now(), db_wf.workflow_id)
    transaction.add()

    # create pdf object for database and add
    output_pdf = Pdf(str(uuid4()), filename, app.config['UPLOAD_FOLDER'], transaction_id)
    output_pdf.add()

    return redirect(url_for('.user_page', username=g.user.username))

@mod.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
