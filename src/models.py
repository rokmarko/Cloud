"""
Database models for KanardiaCloud
"""

from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from src.app import db


class User(UserMixin, db.Model):
    """User model for authentication and user management."""
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    devices = db.relationship('Device', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    checklists = db.relationship('Checklist', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    logbook_entries = db.relationship('LogbookEntry', backref='pilot', lazy='dynamic', cascade='all, delete-orphan')
    initial_logbook_time = db.relationship('InitialLogbookTime', backref='pilot', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password: str) -> None:
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches hash."""
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self) -> str:
        """Generate email verification token."""
        from flask import current_app
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps({'user_id': self.id}, salt='email-verification')
    
    def generate_reset_token(self) -> str:
        """Generate password reset token."""
        from flask import current_app
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps({'user_id': self.id}, salt='password-reset')
    
    @staticmethod
    def verify_token(token: str, salt: str, max_age: int = 3600) -> 'User':
        """Verify token and return user."""
        from flask import current_app
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token, salt=salt, max_age=max_age)
            user_id = data['user_id']
            return User.query.get(user_id)
        except:
            return None
    
    @property
    def full_name(self) -> str:
        """Get user's nickname."""
        return self.nickname
    
    def __repr__(self):
        return f'<User {self.email}>'


class Device(db.Model):
    """Device model for aircraft/equipment management."""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)  # aircraft, radio, gps, etc.
    model = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    registration = db.Column(db.String(20))  # For aircraft
    external_device_id = db.Column(db.String(100))  # ThingsBoard device ID for sync
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Device {self.name}>'


class Checklist(db.Model):
    """Checklist model for flight procedures."""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # preflight, takeoff, landing, emergency
    items = db.Column(db.Text, nullable=False)  # JSON string of checklist items
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Checklist {self.title}>'


class ApproachChart(db.Model):
    """Approach chart model for navigation charts."""
    
    id = db.Column(db.Integer, primary_key=True)
    airport_code = db.Column(db.String(10), nullable=False)
    airport_name = db.Column(db.String(200), nullable=False)
    chart_type = db.Column(db.String(50), nullable=False)  # ILS, VOR, GPS, etc.
    runway = db.Column(db.String(10))
    chart_url = db.Column(db.String(500))  # URL to chart file
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ApproachChart {self.airport_code} {self.chart_type}>'


class LogbookEntry(db.Model):
    """Logbook entry model for flight logging."""
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    aircraft_type = db.Column(db.String(50), nullable=False)
    aircraft_registration = db.Column(db.String(20), nullable=False)
    departure_airport = db.Column(db.String(10), nullable=False)
    arrival_airport = db.Column(db.String(10), nullable=False)
    flight_time = db.Column(db.Float, nullable=False)  # Hours
    pilot_in_command_time = db.Column(db.Float, default=0.0)
    dual_time = db.Column(db.Float, default=0.0)
    instrument_time = db.Column(db.Float, default=0.0)
    night_time = db.Column(db.Float, default=0.0)
    cross_country_time = db.Column(db.Float, default=0.0)
    landings_day = db.Column(db.Integer, default=0)
    landings_night = db.Column(db.Integer, default=0)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<LogbookEntry {self.date} {self.aircraft_registration}>'


class InitialLogbookTime(db.Model):
    """Initial logbook time model for setting starting hours."""
    
    id = db.Column(db.Integer, primary_key=True)
    effective_date = db.Column(db.Date, nullable=False)
    total_time = db.Column(db.Float, default=0.0)
    pilot_in_command_time = db.Column(db.Float, default=0.0)
    dual_time = db.Column(db.Float, default=0.0)
    instrument_time = db.Column(db.Float, default=0.0)
    night_time = db.Column(db.Float, default=0.0)
    cross_country_time = db.Column(db.Float, default=0.0)
    total_landings = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<InitialLogbookTime {self.user_id} {self.effective_date}>'
