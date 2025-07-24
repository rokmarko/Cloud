"""
Forms for authentication and user management
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from src.models import User


class LoginForm(FlaskForm):
    """Login form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """Registration form."""
    nickname = StringField('Nickname', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        """Check if email is already registered."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email address.')


class RequestPasswordResetForm(FlaskForm):
    """Password reset request form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')
    
    def validate_email(self, email):
        """Check if email exists."""
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('No account found with that email address.')


class ResetPasswordForm(FlaskForm):
    """Password reset form."""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')


class DeviceForm(FlaskForm):
    """Device form."""
    name = StringField('Device Name', validators=[DataRequired(), Length(max=100)])
    device_type = SelectField('Device Type', choices=[
        ('aircraft', 'Aircraft'),
        ('radio', 'Radio'),
        ('gps', 'GPS'),
        ('transponder', 'Transponder'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    model = StringField('Model', validators=[Length(max=100)])
    serial_number = StringField('Serial Number', validators=[Length(max=100)])
    registration = StringField('Registration', validators=[Length(max=20)])
    submit = SubmitField('Save Device')


class ChecklistForm(FlaskForm):
    """Checklist form."""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    category = SelectField('Category', choices=[
        ('preflight', 'Preflight'),
        ('takeoff', 'Takeoff'),
        ('landing', 'Landing'),
        ('emergency', 'Emergency'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    items = TextAreaField('Checklist Items (one per line)', validators=[DataRequired()])
    submit = SubmitField('Save Checklist')


class LogbookEntryForm(FlaskForm):
    """Logbook entry form."""
    date = DateField('Date', validators=[DataRequired()])
    aircraft_type = StringField('Aircraft Type', validators=[DataRequired(), Length(max=50)])
    aircraft_registration = StringField('Aircraft Registration', validators=[DataRequired(), Length(max=20)])
    departure_airport = StringField('Departure Airport', validators=[DataRequired(), Length(max=10)])
    arrival_airport = StringField('Arrival Airport', validators=[DataRequired(), Length(max=10)])
    flight_time = FloatField('Total Flight Time (hours)', validators=[DataRequired()])
    pilot_in_command_time = FloatField('PIC Time (hours)', validators=[Optional()])
    dual_time = FloatField('Dual Time (hours)', validators=[Optional()])
    instrument_time = FloatField('Instrument Time (hours)', validators=[Optional()])
    night_time = FloatField('Night Time (hours)', validators=[Optional()])
    cross_country_time = FloatField('Cross Country Time (hours)', validators=[Optional()])
    landings_day = IntegerField('Day Landings', validators=[Optional()])
    landings_night = IntegerField('Night Landings', validators=[Optional()])
    remarks = TextAreaField('Remarks')
    submit = SubmitField('Save Entry')
