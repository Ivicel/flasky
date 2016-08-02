from . import main
from .forms import EditProfileForm, AdminEditProfile
from flask import render_template, url_for, redirect, abort, flash
from flask_login import login_required, current_user
from flask_sqlalchemy import Pagination
from ..models import User, Role
from .. import db
from ..decorators import admin_required, permission_required



@main.route('/')
def index():
	return render_template('index.html')

@main.route('/user/<username>')
def profile(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	return render_template('profile.html', user=user)

@main.route('/user/<username>/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
	if current_user.username != username:
		return redirect(url_for('.edit_profile', username=current_user.username))
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		db.session.add(current_user)
		db.session.commit()
		flash('Your profile has been updated.')
		return redirect(url_for('.edit_profile'), username=username)
	form.name.data = current_user.name
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	return render_template('edit-profile.html', form=form)

@main.route('/edit-profile/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_profile(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	form = AdminEditProfile(user=user)
	if form.validate_on_submit():
		 user.email = form.email.data
		 user.username = form.username.data
		 user.confirmed = form.confirmed.data
		 user.role_id = form.role.data
		 user.name = form.name.data
		 user.location = form.location.data
		 user.about_me = form.about_me.data
		 db.session.add(user)
		 db.session.commit()
		 flash("user's profile has been updated.")
		 return redirect(url_for('main.admin_edit_profile', username=username))
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id or Role.query.filter_by(default_user=True).first().id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit-profile.html', form=form, user=user)

@main.route('/manage-accounts')
def manage_accounts():
	users = User.query.all()
	return render_template('manage-accounts.html', users=users)