from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, ValidationError, Length
import re
from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import List, Optional
from app.models import User


# DTO FORMS

class RegisterDTO(BaseModel):
    username: str
    email_address: EmailStr
    password1: str
    password2: str


class LoginDTO(BaseModel):
    username: str
    password: str


class ForgotPasswordDTO(BaseModel):
    username: str
    email: EmailStr
    password1: str
    password2: str


class CreatePostDTO(BaseModel):
    title: str
    body: str
    tags: str


class EditPostDTO(BaseModel):
    title: str
    body: str
    tags: str


class AgeCheckDTO(BaseModel):
    date_of_birth: date


class ProfileDTO(BaseModel):
    name: str = None
    username: str
    gender: str = None
    pronouns: str = None
    bio: str = None



# FLASKFORMS

def password_strength(form, field):
    password = field.data

    if len(password) < 6:
        raise ValidationError('Password must be at least 6 characters long.')

    if not (re.search(r'[A-Z]', password) and
            re.search(r'[a-z]', password) and
            re.search(r'[0-9]', password) and
            re.search(r'[!@#$%^&*()\-_=+{};:,<.>]', password)):
        raise ValidationError('Password must contain at least one uppercase letter, one lowercase letter, one number, and one symbol.')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=25)])
    email_address = StringField('Email', validators=[DataRequired(), Email()])
    password1 = PasswordField('Password', validators=[DataRequired(), password_strength])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already registered. Please choose a different one.')

    def validate_email_address(self, email_address):
        user = User.query.filter_by(email_address=email_address.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

    def validate_password2(self, password2):
        if self.password1.data != password2.data:
            raise ValidationError('Passwords do not match.')


class LoginForm(FlaskForm):
    username = StringField(label='Username:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Sign in')


class ForgotPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password1 = PasswordField('New Password', validators=[DataRequired(), password_strength])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
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

    def validate_password2(self, password2_field):
        if self.password1.data != password2_field.data:
            raise ValidationError('Passwords do not match.')


class CreatePostForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()])
    body = TextAreaField(label='Body', validators=[DataRequired()])
    tags = StringField('Tags (optional)')
    submit = SubmitField(label='Create a post!')


class EditPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    body = TextAreaField('Body', validators=[DataRequired()])
    tags = StringField('Tags (optional)')
    submit = SubmitField('Edit a post!')


class AgeCheckForm(FlaskForm):
    date_of_birth = DateField(label='Date of Birth', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Verify')

    def validate_date_of_birth(form, date_of_birth):
        today = datetime.now().date()
        if date_of_birth.data >= today:
            raise ValidationError('Date of birth must be in the past.')

    def validate_age(form, age):
        try:
            int(age.data)
        except ValueError:
            raise ValidationError('Age must be a valid number.')


class ProfileForm(FlaskForm):
    name = StringField(label='Name:')
    username = StringField(label='Username:', validators=[DataRequired()])
    gender = StringField(label='Gender:')
    pronouns = StringField(label='Pronouns:')
    bio = TextAreaField(label='Bio:')
    submit = SubmitField(label='Update')