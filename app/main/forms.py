from ..models import Role, User
from flask_wtf import Form
from flask_login import current_user
from wtforms.validators import Length, DataRequired, Email, Regexp, ValidationError
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, SelectField, \
	TextAreaField



class EditProfileForm(Form):
	name = StringField('Real name', validators=[Length(0, 64)])
	location = StringField('Location', validators=[Length(0, 64)])
	about_me = TextAreaField('About me')
	submit = SubmitField('Submit')

class AdminEditProfile(Form):
	email = StringField('Email', validators=[DataRequired(), Length(5, 64), Email()])
	username = StringField('Username', validators=[DataRequired(), Length(2, 64),
		Regexp('^[A-Za-z][A-Za-z0-9_.]*$', message='username must begin with letters, '
			'and only contain letters, numbers, dots and underscore')])
	confirmed = BooleanField('Confirmed')
	role = SelectField('Role', coerce=int)
	name = StringField('Real name', validators=[Length(0, 64)])
	location = StringField('Location', validators=[Length(0, 64)])
	about_me = TextAreaField('About me')
	submit = SubmitField('Submit')

	def __init__(self, user, *args, **kwargs):
		super(AdminEditProfile, self).__init__(*args, **kwargs)
		self.user = user
		roles = Role.query.order_by(Role.name).all()
		self.role.choices = [(role.id, role.name) for role in roles]

	def validate_email(self, field):
		if field.data != self.user.email and \
			User.query.filter_by(email=field.data).first():
			raise ValidationError('email has already registered.')

	def validate_username(self, field):
		if field.data != self.user.username and \
			User.query.filter_by(username=field.data).first():
			raise ValidationError('username has already registered.')