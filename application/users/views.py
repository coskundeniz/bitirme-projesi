# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, url_for, redirect, g, flash
from flask.ext.login import login_user, logout_user, login_required

from application.app import db, login_manager, config_data
from application.users.models import User, Transaction
from application.users.forms import LoginForm, RegistrationForm
from application.constants import ROLE_STUDENT, ROLE_ADMIN, ROLE_INSTRUCTOR
from application.workflow.models import WorkflowState
from application.pdf_forms.models import Pdf
from application.utils import get_from_config, create_spec_from_xml
from application.utils import save_workflow_instance, get_workflow_instance

from SpiffWorkflow.storage.DictionarySerializer import DictionarySerializer
from SpiffWorkflow import Workflow, Task


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
def user_page(username=None):

    user = User.query.filter_by(username=username).first_or_404()

    if user.role == ROLE_ADMIN:
        return render_template('admin.html')

    elif user.role == ROLE_INSTRUCTOR:
        db_wf_for_instructor = WorkflowState.query.filter_by(instructor_id=user.id).first()

        if db_wf_for_instructor:
            workflow = get_workflow_instance(get_from_config(db_wf_for_instructor.workflow_name,
                                                            "spec_file"), db_wf_for_instructor)

            # get related transaction
            transaction = Transaction.query.filter_by(workflow_id=db_wf_for_instructor.workflow_id).first()

            # get output pdf
            output_pdf = Pdf.query.filter_by(transaction_id=transaction.transaction_id).first()

            return render_template('instructor.html',
                                    workflow=workflow,
                                    form=output_pdf,
                                    ready=Task.READY)
        else:
            return render_template('instructor.html', workflow=None)

    else:
        db_wf = WorkflowState.query.filter_by(user_id=user.id).first()

        if db_wf:
            workflow = get_workflow_instance(get_from_config(db_wf.workflow_name, "spec_file"), db_wf)

            return render_template('user.html',
                                    config_data=config_data,
                                    workflow=workflow,
                                    ready=Task.READY,
                                    completed=Task.COMPLETED)
        else:
            return render_template('user.html',
                                    config_data=config_data,
                                    workflow=None)

@mod.route('/start/<spec_file>')
@login_required
def start_workflow(spec_file):
    """ start workflow for graduation project """

    # create workflow instance
    workflow = Workflow(create_spec_from_xml(spec_file))

    # complete start task
    start_task = workflow.get_tasks(state=Task.READY)[0]
    workflow.complete_task_from_id(start_task.id)

    # save username in workflow
    workflow.data["student"] = g.user.username

    # save workflow instance to database
    save_workflow_instance(workflow, g.user.id)

    return render_template('user.html',
                            config_data=config_data,
                            workflow=workflow,
                            ready=Task.READY,
                            completed=Task.COMPLETED)

@mod.route('/<username>/approve')
@login_required
def approve(username):

    user = User.query.filter_by(username=username).first()
    db_wf = WorkflowState.query.filter_by(user_id=user.id).first()
    workflow = get_workflow_instance(get_from_config(db_wf.workflow_name, "spec_file"), db_wf)

    # update pre-assign variable
    workflow.get_tasks(state=Task.READY)[0].task_spec.post_assign[0].right = "True"

    # complete *_excl_choice task
    workflow.complete_next()

    # complete approve_* task
    workflow.complete_next()

    # update workflow on database
    serialized_wf = workflow.serialize(serializer=DictionarySerializer())
    db_wf.workflow_instance = serialized_wf
    db.session.commit()

    transaction = Transaction.query.filter_by(workflow_id=db_wf.workflow_id).first()
    pdf = Pdf.query.filter_by(transaction_id=transaction.transaction_id).first()

    return render_template('instructor.html',
                            workflow=workflow,
                            form=pdf,
                            ready=Task.READY)

@mod.route('/reject')
@login_required
def reject():
    return redirect(url_for('index'))

@mod.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
