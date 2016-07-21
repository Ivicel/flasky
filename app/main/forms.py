from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class NameForm(Form):
	# email = StringField("Please input your email.", validators=[DataRequired(),
		# is_an_email_address()])
	# password = PasswordField("Input your password.", validators=[DataRequired(),
	# 	EqualTo('password_confirm', "The password looks like not the same.")])
	# password_confirm = PasswordField("Confirm your password.", validators=[
	# 	DataRequired()])
	username = StringField("Please input your name.", validators=[DataRequired()])
	submit = SubmitField("Submit")