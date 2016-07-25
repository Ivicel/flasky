from . import auth
from .forms import LoginForm, RegisterForm
from .. import login_manager
from ..models import User
from flask_login import login_user, logout_user, login_required, current_user
from flask import render_template, redirect, url_for, flash, request


@login_manager.user_loader
def load_user(id):
	return User.query.get(int(id))

@auth.route('/login', methods=['GET', 'POST'])
def login():
	if not current_user.is_anonymous:
		return url_for('main.index')
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.user.data).first()
		if user is None or user.check_password(form.password.data) is not True:
			flash('username or password error.')
			return redirect(url_for('.login'))
		login_user(user, remember=form.remember_me.data)
		flash('You have been logged in now.')
		return redirect(request.args.get('next') or url_for('main.index'))
	return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
	flash('You have been logged out.')
	logout_user()
	return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm()
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None:
			flash('email has been registered. please login')
			return redirect(url_for('.register'))
		user = User(username=form.username.data, email=form.email.data,
			password=form.password.data)
		token = user.generate_token()
		send_mail(user.email, 'Confirm Your Account', 'auth/email/new_user',
			token=token, user=user)
		flash('Register successfully.')
		flash('A email has been sent to you, please check your emali '
			'box to confirm your email address.')
		return redirect(url_for('.login'))
	return render_template('auth/register.html', form=form)