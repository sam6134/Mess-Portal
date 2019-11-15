from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from mess.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password",validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Choose a unique username")

    def validate_email(self,email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError("Email is taken. Please enter a different email.")

class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username :
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email :
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')

class PostForm(FlaskForm):
    title = StringField('Please specify type(Bfst/Lunch/Dinner) and day:', validators=[DataRequired()])
    content = TextAreaField('Issues with Food', validators=[DataRequired()])
    date = DateField('Date(dd/mm/YYYY)', format='%Y-%m-%d')
    submit = SubmitField('Submit')

class MenuForm(FlaskForm):
    title = StringField('Please specify the day:', validators=[DataRequired()])
    content = TextAreaField('Food Menu (Bfst,Lunch,Dinner)', validators=[DataRequired()])
    submit = SubmitField('Submit')

class NewMenuForm(FlaskForm):
    title = StringField('Please specify the day:', validators=[DataRequired()])
    breakfast = TextAreaField('Food Menu (Breakfast)', validators=[DataRequired()])
    lunch = TextAreaField('Food Menu (Lunch)', validators=[DataRequired()])
    dinner = TextAreaField('Food Menu (Dinner)', validators=[DataRequired()])
    submit = SubmitField('Submit')
class FindDate(FlaskForm):
    start_date = DateField('Start Date(dd/mm/YYYY)', format='%Y-%m-%d')
    end_date = DateField(' End Date(dd/mm/YYYY)', format='%Y-%m-%d')
    submit = SubmitField('Submit')