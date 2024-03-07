from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import re
from app.models import User

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=25)])
    email_address = StringField('Email', validators=[DataRequired(), Email()])
    password1 = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already registered. Please choose a different one.')

    def validate_email_address(self, email_address):
        user = User.query.filter_by(email_address=email_address.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

    def validate_password1(self, password1):
        password = password1.data

        if len(password) < 6:
            raise ValidationError('Password must be at least 6 characters long.')

        if not (re.search(r'[A-Z]', password) and
                re.search(r'[a-z]', password) and
                re.search(r'[0-9]', password) and
                re.search(r'[!@#$%^&*()\-_=+{};:,<.>]', password)):
            raise ValidationError('Password must contain at least one uppercase letter, one lowercase letter, one number, and one symbol.')

    def validate_password2(self, password2):
        if self.password1.data != password2.data:
            raise ValidationError('Passwords do not match.')

class LoginForm(FlaskForm):
    username = StringField(label='User Name:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Sign in')

class ForgotPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password1 = PasswordField('New Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password1')])
    submit = SubmitField('Reset Password')

    def validate_username(self, username_field):
        username = username_field.data
        user = User.query.filter_by(username=username).first()
        if not user:
            raise ValidationError('User does not exist.')

    def validate_email(self, email_field):
        email = email_field.data
        username = self.username.data
        user = User.query.filter_by(username=username, email_address=email).first()
        if not user:
            raise ValidationError('User with provided email does not exist.')
    
    def validate_passwords(self, password1_field, password2_field):
        password1 = password1_field.data
        password2 = password2_field.data

        if len(password1) < 6 or len(password2) < 6:
            raise ValidationError('Passwords must be at least 6 characters long.')

        if not (re.search(r'[A-Z]', password1) and
                re.search(r'[a-z]', password1) and
                re.search(r'[0-9]', password1) and
                re.search(r'[!@#$%^&*()\-_=+{};:,<.>]', password1)):
            raise ValidationError('Password must contain at least one uppercase letter, one lowercase letter, one number, and one symbol.')

        if password1 != password2:
            raise ValidationError('Passwords do not match.')

class CreatePostForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()])
    body = StringField(label='Body', validators=[DataRequired()])
    tags = StringField('Tags (optional)')
    submit = SubmitField(label='Create a post!')

class EditPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    body = TextAreaField('Body', validators=[DataRequired()])
    tags = StringField('Tags (optional)')
    submit = SubmitField('Edit a post!')

class DeletePostForm(FlaskForm):
    submit = SubmitField(label='Delete a post!')