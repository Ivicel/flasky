from flask_wtf import Form
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import Email, DataRequired, Length, Email, Regexp, EqualTo




class LoginForm(Form):
	user = StringField('Email/Username', validators=[DataRequired(), Length(1, 64)])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('remember me')
	submit = SubmitField('Login')

class RegisterForm(Form):
	email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
	username = StringField('Username', validators=[DataRequired(), Length(1, 64),
		Regexp('^[a-zA-Z][a-zA-Z0-9_.]*$', message='Only underscore, dot '
			'letters and numbers are allowed')])
	password = PasswordField('Password', validators=[DataRequired(), Length(1, 18),
		EqualTo('confirm', 'password does not match')])
	confirm = PasswordField('Confirm Password', validators=[DataRequired()])
	submit = SubmitField('Register')