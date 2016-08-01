from . import main
from .forms import EditProfileForm
from flask import render_template, url_for, redirect, abort, flash
from flask_login import login_required, current_user
from ..models import User
from .. import db



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