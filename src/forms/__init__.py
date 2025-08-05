"""
Forms for authentication and user management
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateField, FloatField, IntegerField, DateTimeLocalField
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
        ('gyro', 'Gyro'),
        ('helicopter', 'Helicopter'),
        ('trike', 'Trike')
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


class ChecklistCreateForm(FlaskForm):
    """Simplified checklist creation form - only title required."""
    title = StringField('Checklist Title', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Create Checklist')


class InstrumentLayoutForm(FlaskForm):
    """Instrument layout form."""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    category = SelectField('Category', choices=[
        ('primary', 'Primary Display'),
        ('secondary', 'Secondary Display'),
        ('backup', 'Backup Instruments'),
        ('custom', 'Custom Layout'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Layout')


class InstrumentLayoutCreateForm(FlaskForm):
    """Simplified instrument layout creation form - only title required."""
    title = StringField('Layout Title', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Create Layout')


class LogbookEntryForm(FlaskForm):
    """Logbook entry form."""
    takeoff_datetime = DateTimeLocalField('Takeoff Date/Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    landing_datetime = DateTimeLocalField('Landing Date/Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    aircraft_type = StringField('Aircraft Type', validators=[DataRequired(), Length(max=50)])
    aircraft_registration = StringField('Aircraft Registration', validators=[DataRequired(), Length(max=20)])
    departure_airport = StringField('Departure Airport', validators=[DataRequired(), Length(max=10)])
    arrival_airport = StringField('Arrival Airport', validators=[DataRequired(), Length(max=10)])
    flight_time = FloatField('Total Flight Time (hours)', validators=[Optional()],
                           description='Leave blank to auto-calculate from takeoff/landing times')
    pilot_in_command_time = FloatField('PIC Time (hours)', validators=[Optional()])
    dual_time = FloatField('Dual Time (hours)', validators=[Optional()])
    instrument_time = FloatField('Instrument Time (hours)', validators=[Optional()])
    night_time = FloatField('Night Time (hours)', validators=[Optional()])
    cross_country_time = FloatField('Cross Country Time (hours)', validators=[Optional()])
    landings_day = IntegerField('Day Landings', validators=[Optional()])
    landings_night = IntegerField('Night Landings', validators=[Optional()])
    remarks = TextAreaField('Remarks')
    submit = SubmitField('Save Entry')


class InitialLogbookTimeForm(FlaskForm):
    """Initial logbook time form."""
    effective_date = DateField('Effective Date', validators=[DataRequired()], 
                               description='Entries before this date will not be counted in totals')
    total_time = FloatField('Total Flight Time (hours)', validators=[DataRequired()], default=0.0)
    pilot_in_command_time = FloatField('Pilot in Command Time (hours)', validators=[Optional()], default=0.0)
    dual_time = FloatField('Dual Instruction Time (hours)', validators=[Optional()], default=0.0)
    instrument_time = FloatField('Instrument Time (hours)', validators=[Optional()], default=0.0)
    night_time = FloatField('Night Time (hours)', validators=[Optional()], default=0.0)
    cross_country_time = FloatField('Cross Country Time (hours)', validators=[Optional()], default=0.0)
    total_landings = IntegerField('Total Landings', validators=[Optional()], default=0)
    notes = TextAreaField('Notes', description='Optional notes about your previous flight experience')
    submit = SubmitField('Set Initial Times')


class PilotMappingForm(FlaskForm):
    """Form for creating pilot mappings."""
    pilot_name = StringField('Pilot Name', validators=[DataRequired(), Length(min=1, max=100)])
    user_id = SelectField('Map to User', coerce=int, validators=[DataRequired()])
    device_id = SelectField('Device', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create Mapping')
    
    def __init__(self, *args, **kwargs):
        super(PilotMappingForm, self).__init__(*args, **kwargs)
        # Populate choices in the view, not here
        self.user_id.choices = []
        self.device_id.choices = []
