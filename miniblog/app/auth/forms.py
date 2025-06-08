
from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from sqlalchemy import text
from app import db
import sqlalchemy as sa
from app.models import User




class LoginForm (FlaskForm):
    username = StringField(_l('使用者名稱'), validators=[DataRequired()])
    password = PasswordField(_l('密碼'), validators=[DataRequired()])
    remember_me = BooleanField(_l('記住我'))
    submit = SubmitField(_l('登入'))

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('請求重設密碼'))

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset') 

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        sql = text("SELECT 1 FROM user WHERE username = :username LIMIT 1")
        result = db.session.execute(sql, {'username': username.data}).first()
        if result is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        sql = text("SELECT 1 FROM user WHERE email = :email LIMIT 1")
        result = db.session.execute(sql, {'email': email.data}).first()
        if result is not None:
            raise ValidationError('Please use a different email address.')






