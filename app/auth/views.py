from flask_login import login_required, login_user, logout_user, current_user
from flask import render_template, url_for, redirect, flash, request, \
	render_template_string, abort
from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, \
	ChangeEmailForm, ResetPasswordForm, ConfirmNewPasswordForm
from .. import login_manager, db
from ..models import User
from ..email import send_mail


@auth.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			return redirect(request.args.get('next') or url_for('main.index'))
		flash('Invalid username or password.')
	return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out.')
	return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(email=form.email.data, username=form.username.data,
			password=form.password.data)
		db.session.add(user)
		db.session.commit()
		token = user.generate_confirmation_token()
		send_mail(user.email, 'Confirm Your Account', 'auth/email/confirm',
			user=user, token=token)
		flash('A confirmation email has been sent to you by email.')
		flash('Please confirm your account before you login.')
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
	if current_user.confirmed:
		return redirect(url_for('main.index'))
	if current_user.confirm(token):
		flash('You have confirmed your account.')
	else:
		flash('The confirmation link is invalid or has expired.')
	return redirect(url_for('main.index'))

@auth.route('/unconfirmed')
@login_required
def unconfirmed():
	print(current_user.confirmed)
	if current_user.is_anonymous or current_user.confirmed:
		return redirect(url_for('main.index'))
	return render_template('auth/unconfirmed.html')

@auth.route('/resend-email')
@login_required
def resend_email():
	if current_user.is_anonymous or current_user.confirmed:
		return redirect(url_for('main.index'))
	token = current_user.generate_confirmation_token()
	send_mail(current_user.email, 'Confirm Your Account', 'auth/email/confirm',
			user=current_user, token=token)
	flash('A confirmation email has been sent to you by email.')
	return redirect(url_for('.unconfirmed'))

@auth.route('/change-your-password', methods=['GET', 'POST'])
@login_required
def change_password():
	form = ChangePasswordForm()
	if form.validate_on_submit():
		if not current_user.verify_password(form.old_password.data):
			flash('old password is wrong.')
			return redirect(url_for('.change_password'))
		current_user.password = form.new_password.data
		db.session.add(current_user)
		db.session.commit()
		flash('Your password has been changed.')
	return render_template('auth/change-password.html', form=form)

@auth.route('/change-your-email', methods=['GET', 'POST'])
@login_required
def change_email():
	form = ChangeEmailForm()
	if form.validate_on_submit():
		token = current_user.generate_change_email_token(form.email.data)
		send_mail(form.email.data, 'Confirm your new email address', 
			'auth/email/change-email-confirm', user=current_user, token=token)
		flash('A confirmation email has been sent to you.')
	return render_template('auth/change-email.html', form=form)

@auth.route('/confirm-to-change-your-email/<token>', methods=['GET', 'POST'])
@login_required
def confirm_to_change_email(token):
	if current_user.confirm_new_email(token):
		flash('Your email has changed.')
		return redirect(url_for('main.user_profile', username=current_user.username))
	else:
		abort(404)

@auth.route('/reset-your-password', methods=['GET', 'POST'])
def reset_password():
	form = ResetPasswordForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None:
			token = user.generate_reset_password_token()
			send_mail(user.email, 'reset password', 
				'auth/email/reset-password-confirm', user=user, token=token)
			flash('A email has sent to you, '
				'please check your email box to reset password')
	return render_template('auth/reset-password.html', form=form)

@auth.route('/reset-your-password/<token>', methods=['GET', 'POST'])
def confirm_to_reset_password(token):
	form = ConfirmNewPasswordForm()
	user = User.confirm_reset_password(token)
	if user is None:
		abort(404)
	if form.validate_on_submit():
		user.password = form.password.data
		db.session.add(user)
		db.session.commit()
		flash('Your password has been reset to new passowrd')
		form = None
	return render_template('auth/reset-password.html', form=form)

@auth.before_app_request
def check_account_confirm():
	if current_user.is_authenticated :
		current_user.ping()
		if not current_user.confirmed and request.endpoint[:5] != 'auth.':
			return redirect(url_for('auth.unconfirmed'))

