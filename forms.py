from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class DictionaryForm(FlaskForm):
    name = StringField('অভিধানের নাম', validators=[DataRequired(), Length(max=200)])
    author = StringField('লেখক', validators=[Length(max=200)])
    publisher = StringField('প্রকাশক', validators=[Length(max=200)])
    edition = StringField('সংস্করণ', validators=[Length(max=100)])
    submit = SubmitField('সংরক্ষণ করুন')

class WordForm(FlaskForm):
    word = StringField('শব্দ', validators=[DataRequired(), Length(max=100)])
    definition = TextAreaField('অর্থ', validators=[DataRequired()])
    pos = StringField('পদ')
    note = TextAreaField('টীকা')
    dictionary_id = SelectField('ডিকশনারি', coerce=int, validators=[])
    submit = SubmitField('সংরক্ষণ করুন')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('ইমেইল', validators=[DataRequired()])
    submit = SubmitField('রিসেট লিঙ্ক পাঠান')

class PasswordResetForm(FlaskForm):
    password = PasswordField('নতুন পাসওয়ার্ড', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('নিশ্চিত করুন', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('পাসওয়ার্ড রিসেট করুন') 