from flask_wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp, ValidationError
from ..models import User, Role


class NameForm(Form):
	# email = StringField("Please input your email.", validators=[DataRequired(),
		# is_an_email_address()])
	# password = PasswordField("Input your password.", validators=[DataRequired(),
	# 	EqualTo('password_confirm', "The password looks like not the same.")])
	# password_confirm = PasswordField("Confirm your password.", validators=[
	# 	DataRequired()])
	username = StringField("Please input your name.", validators=[DataRequired()])
	submit = SubmitField("Submit")

class EditProfileForm(Form):
	name = StringField('Real name', validators=[Length(0, 64)])
	location = StringField('Location', validators=[Length(0, 64)])
	about_me = TextAreaField('About me')
	submit = SubmitField('Submit')

class EditProfileAdminForm(Form):
	email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 64)])
	username = StringField('Username', validators=[DataRequired(), Length(1, 64),
		Regexp('^[A-Za-z][A-Za-z0-9_.]*$', message='Username must only have letters, '
			'numbers, dots or underscore')])
	confirmed = BooleanField('Confirm')
	role = SelectField('Role', coerce=int)
	name = StringField('Real name', validators=[Length(0, 64)])
	location = StringField('Location', validators=[Length(0, 64)])
	about_me = TextAreaField('About me')
	submit = SubmitField('Submit')

	def __init__(self, user, *args, **kwargs):
		super(EditProfileAdminForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name)
			for role in Role.query.order_by(Role.name).all()]
		self.user = user

	def validate_email(self, field):
		if field.data != self.user.email and \
			User.query.filter_by(email=field.data).first():
			raise ValidationError('Email already registered.')

	def validate_username(self, field):
		if field.data != self.user.username and \
			User.query.filter_by(username=field.data).first():
			raise ValidationError('Username already in use.')