from ..models import User
from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError,\
	Regexp

class LoginForm(Form):
	email = StringField('Email', validators=[DataRequired(), Length(1, 64),
		Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Keep me logged in')
	submit = SubmitField('Log In')


class RegistrationForm(Form):
	email = StringField('Email', validators=[Email(), DataRequired(), Length(1, 64)])
	username = StringField('Username', validators=[DataRequired(), Length(1, 64),
		Regexp('^[a-zA-Z][a-zA-Z0-9_.]*$', 0, 'Usernames must have only letters, '
			'numbers, dots or underscores')])
	password = PasswordField('Password', validators=[DataRequired(),
		EqualTo('confirm', 'Password didn\'t match')])
	confirm = PasswordField('Confirm password', validators=[DataRequired()])
	submit = SubmitField('Register')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('email already have registered.')

	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError('username already in user.')

class ChangePasswordForm(Form):
	old_password = PasswordField('Old Password', validators=[DataRequired()])
	new_password = PasswordField('New Password', validators=[DataRequired(),
		EqualTo('confirm', 'New password didn\'t match')])
	confirm = PasswordField('Confirm', validators=[DataRequired()])
	submit = SubmitField('Submit')

class ChangeEmailForm(Form):
	email = StringField('New email', validators=[DataRequired(), Email(), Length(1, 64)])
	submit = SubmitField('Submit')

class ResetPasswordForm(Form):
	email = StringField('Your email', validators=[DataRequired(), 
		Email(), Length(1, 64)])
	submit = SubmitField('Submit')

class ConfirmNewPasswordForm(Form):
	password = PasswordField('Password', validators=[DataRequired(), 
		EqualTo('confirm', 'Password didn\'t match')])
	confirm = PasswordField('Confirm', validators=[DataRequired()])
	submit = SubmitField('Submit')