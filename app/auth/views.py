from datetime import datetime
from . import auth
from ..models import User, Post
from ..email import send_mail
from .. import login_manager, db
from .forms import LoginForm, RegisterForm, ChangeEmailForm, ChangePasswordForm, \
	SendResetPasswordForm, ConfirmResetPasswordForm
from flask_login import login_user, logout_user, login_required, current_user
from flask import render_template, redirect, url_for, flash, request, abort


@login_manager.user_loader
def load_user(id):
	return User.query.get(int(id))

@auth.before_app_request
def is_confirmed():
	if current_user.is_authenticated:
		current_user.ping()
		if not current_user.confirmed and request.endpoint[5:] not in \
			['unconfirmed', 'logout', 'resend_email', 'confirm_email_address']:
			return redirect(url_for('auth.unconfirmed'))

# 登录
@auth.route('/login', methods=['GET', 'POST'])
def login():
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.user.data).first() \
			if '@' in form.user.data else \
			User.query.filter_by(username=form.user.data).first()
		if user is None or user.check_password(form.password.data) is not True:
			flash('username or password error.')
			return redirect(url_for('.login'))
		login_user(user, remember=form.remember_me.data)
		flash('You have been logged in now.')
		return redirect(request.args.get('next') or url_for('main.index'))
	return render_template('auth/login.html', form=form)

# 登出
@auth.route('/logout')
@login_required
def logout():
	current_user.last_seen = datetime.utcnow()
	db.session.add(current_user)
	db.session.commit()
	logout_user()
	flash('You have been logged out.')
	return redirect(url_for('main.index'))

# 注册
@auth.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm()
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	if form.validate_on_submit():
		user = User(username=form.username.data, email=form.email.data,
			password=form.password.data)
		token = user.generate_token()
		send_mail(user.email, 'Confirm Your Account', 'auth/email/new_user',
			token=token, user=user)
		db.session.add(user)
		db.session.commit()
		flash('Register successfully.')
		flash('A email has been sent to you, please check your emali '
			'box to confirm your email address.')
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html', form=form)

# 确认邮箱
@auth.route('/confirm/<token>')
@login_required
def confirm_email_address(token):
	if current_user.confirm_token(token):
		flash('You have confirmed your email address successfully.')
		return redirect(url_for('main.index'))
	flash('The link has expirated or invalid.')
	return redirect(url_for('auth.unconfirmed'))

# 未确认邮箱页面
@auth.route('/unconfirmed')
@login_required
def unconfirmed():
	if not current_user.confirmed:
		return render_template('auth/unconfirmed.html')
	return redirect(url_for('main.index'))

# 重新发新确认邮件
@auth.route('/resend-email')
@login_required
def resend_email():
	if not current_user.confirmed:
		token = current_user.generate_token()
		send_mail(current_user.email, 'Confirm Your Account', 'auth/email/new_user',
			token=token, user=current_user)
		flash('An email has been sent to your, please confirm your email.')
		return redirect(url_for('auth.unconfirmed'))
	return redirect(url_for('main.index'))

# 更改邮箱
@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
	form = ChangeEmailForm()
	if form.validate_on_submit():
		token = current_user.generate_token(new_email=form.email.data)
		send_mail(form.email.data, 'Confirm Your Account',
			'auth/email/send_change_email', token=token, user=current_user)
		flash('An email has been sent to your, please confirm your email.')
		return redirect(url_for('auth.change_email'))
	return render_template('auth/change_email.html', form=form)

@auth.route('/change-email/<token>')
@login_required
def confirm_change_email(token):
	if current_user.confirm_token(token, change_email=True):
		flash('You have change your email successfully.')
	else:
		flash('The link has been expirated or invalid.')
	return render_template('auth/change_email.html')

# 更改密码
@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
	form = ChangePasswordForm()
	if form.validate_on_submit():
		if current_user.check_password(form.old_password.data):
			current_user.password = form.new_password.data
			db.session.add(current_user)
			db.session.commit()
			flash('Your password has been update')
		else:
			flash('input password error')
		return redirect(url_for('auth.change_password'))
	return render_template('auth/change_email.html', form=form)

# 重置密码
@auth.route('/reset-your-password', methods=['GET', 'POST'])
def reset_password():
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = SendResetPasswordForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is None:
			flash("The email has been not registered.")
			return redirect(url_for('auth.reset_password'))
		token = user.generate_token(reset_password=True)
		send_mail(form.email.data, 'Reset Your Password', 
			'auth/email/send_reset_password', user=user, token=token)
		flash('An email has been sent to you, '
			'please check your inbox to reset your password.')
		return redirect(url_for('auth.reset_password'))
	return render_template('auth/change_email.html', form=form)
	

@auth.route('/reset-your-password/<token>', methods=['GET', 'POST'])
def confirm_reset_password(token):
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = ConfirmResetPasswordForm()
	if form.validate_on_submit():
		if User.confirm_reset_password(token, form.password.data):
			flash('Your password has been change, please log in.')
			return redirect(url_for('auth.login'))
		flash('The link has been expirated or invalid.')
		return redirect(url_for('main.index'))
	return render_template('auth/change_email.html', form=form)