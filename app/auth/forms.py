from flask_wtf import Form
from ..models import User
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import Email, DataRequired, Length, Email, Regexp, \
	EqualTo, ValidationError



# 登录表单
class LoginForm(Form):
	user = StringField('Email/Username', validators=[DataRequired(), Length(1, 64)])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('remember me')
	submit = SubmitField('Login')

# 注册表单
class RegisterForm(Form):
	email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
	username = StringField('Username', validators=[DataRequired(), Length(1, 64),
		Regexp('^[a-zA-Z][a-zA-Z0-9_.]*$', message='Only underscore, dot letters '
			'and numbers are allowed and start with a letter')])
	password = PasswordField('Password', validators=[DataRequired(), Length(1, 18),
		EqualTo('confirm', 'password does not match')])
	confirm = PasswordField('Confirm Password', validators=[DataRequired()])
	submit = SubmitField('Register')

	# 自定义验证器
	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first() is not None:
			raise ValidationError('email has already register.')

	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first() is not None:
			raise ValidationError('username has already register.')

# 更改邮箱表单
class ChangeEmailForm(Form):
	email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 64)])
	submit = SubmitField('Submit')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('email has already been registered.')

# 更改密码表单
class ChangePasswordForm(Form):
	old_password = PasswordField('Old password', validators=[DataRequired()])
	new_password = PasswordField('New password', validators=[DataRequired(), 
		Length(1, 20)])
	confirm = PasswordField('Confirm new password', validators=[DataRequired(),
		Length(1, 20), EqualTo('new_password', 'password must match')])
	submit = SubmitField('Submit')

# 发送重置密码表单
class SendResetPasswordForm(Form):
	email = StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Submit')

# 重置密码表单
class ConfirmResetPasswordForm(Form):
	password = PasswordField('Password', validators=[DataRequired(), Length(1, 20)])
	confirm = PasswordField('Confirm Password', validators=[DataRequired(), 
		Length(1, 20), EqualTo('password', 'password must match')])
	submit = SubmitField('Submit')
