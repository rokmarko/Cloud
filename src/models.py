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


class Pilot(db.Model):
    """Pilot model to map users to devices with pilot names."""
    
    id = db.Column(db.Integer, primary_key=True)
    pilot_name = db.Column(db.String(100), nullable=False)  # Name as it appears in logbook
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='pilot_mappings')
    device = db.relationship('Device', backref='pilots')
    
    # Unique constraint to prevent duplicate pilot names per device
    __table_args__ = (db.UniqueConstraint('pilot_name', 'device_id', name='_pilot_device_uc'),)
    
    def __repr__(self):
        return f'<Pilot {self.pilot_name} on {self.device.name if self.device else "Unknown Device"}>'
    
    def get_logbook_entry_count(self):
        """Get the number of logbook entries for this pilot on this device."""
        return LogbookEntry.query.filter_by(
            pilot_name=self.pilot_name,
            device_id=self.device_id
        ).count()


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
    flight_time = db.Column(db.Float, nullable=False)  # Total flight time in hours
    takeoff_time = db.Column(db.Time, nullable=True)  # Time of takeoff (optional)
    landing_time = db.Column(db.Time, nullable=True)  # Time of landing (optional)
    pilot_in_command_time = db.Column(db.Float, default=0.0)
    dual_time = db.Column(db.Float, default=0.0)
    instrument_time = db.Column(db.Float, default=0.0)
    night_time = db.Column(db.Float, default=0.0)
    cross_country_time = db.Column(db.Float, default=0.0)
    landings_day = db.Column(db.Integer, default=0)
    landings_night = db.Column(db.Integer, default=0)
    remarks = db.Column(db.Text)
    pilot_name = db.Column(db.String(100), nullable=True)  # Name of pilot as recorded in logbook
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=True)  # Optional link to device for synced entries
    
    # Relationships
    # Note: user relationship is handled by existing 'pilot' backref from User model
    device = db.relationship('Device', backref=db.backref('device_logbook_entries', lazy=True))
    user = db.relationship('User', overlaps="logbook_entries,pilot")
    
    def get_calculated_flight_time(self) -> float:
        """Calculate flight time in hours from takeoff and landing times."""
        if not self.takeoff_time or not self.landing_time:
            return self.flight_time or 0.0
        
        # Convert times to datetime objects for calculation
        from datetime import datetime, timedelta
        
        # Use today's date as base for time calculation
        base_date = self.date if self.date else datetime.now().date()
        takeoff_dt = datetime.combine(base_date, self.takeoff_time)
        landing_dt = datetime.combine(base_date, self.landing_time)
        
        # Handle flights that cross midnight
        if landing_dt < takeoff_dt:
            landing_dt += timedelta(days=1)
        
        # Calculate flight duration in hours
        flight_duration = landing_dt - takeoff_dt
        return round(flight_duration.total_seconds() / 3600, 2)
    
    def get_aircraft_info(self):
        """Get aircraft information from linked device or stored values."""
        if self.device:
            return {
                'registration': self.device.registration or self.aircraft_registration,
                'type': self.device.model or self.aircraft_type
            }
        return {
            'registration': self.aircraft_registration,
            'type': self.aircraft_type
        }
    
    def get_pilot_mapping(self):
        """Get pilot mapping if pilot_name and device are available."""
        if self.pilot_name and self.device_id:
            return Pilot.query.filter_by(
                pilot_name=self.pilot_name,
                device_id=self.device_id
            ).first()
        return None
    
    def get_actual_pilot_user(self):
        """Get the actual user who is the pilot for this entry."""
        pilot_mapping = self.get_pilot_mapping()
        if pilot_mapping:
            return pilot_mapping.user
        # Fall back to the user_id field (original owner/creator)
        return self.user
    
    @property
    def is_synced(self) -> bool:
        """Check if this entry was synced from a device."""
        return self.device_id is not None
        # is calculated from takeoff_time and landing_time.
        pass
    
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
