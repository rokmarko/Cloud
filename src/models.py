"""
Database models for KanardiaCloud
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any
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
    date_format = db.Column(db.String(20), default="%Y-%m-%d", nullable=False)  # User's preferred date format
    
    # Relationships
    devices = db.relationship('Device', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    checklists = db.relationship('Checklist', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    instrument_layouts = db.relationship('InstrumentLayout', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
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
    current_logger_page = db.Column(db.BigInteger, nullable=True)  # Current page of device logger
    is_active = db.Column(db.Boolean, default=True)
    
    # Telemetry fields
    last_telemetry_update = db.Column(db.DateTime, nullable=True)  # When telemetry was last updated
    fuel_quantity = db.Column(db.Float, nullable=True)  # Current fuel quantity
    status = db.Column(db.String(20), nullable=True)  # Raw status from telemetry
    status_description = db.Column(db.String(50), nullable=True)  # Human-readable status
    altitude = db.Column(db.Float, nullable=True)  # Current altitude
    latitude = db.Column(db.Float, nullable=True)  # Current latitude
    longitude = db.Column(db.Float, nullable=True)  # Current longitude
    speed = db.Column(db.Float, nullable=True)  # Current speed
    location_description = db.Column(db.String(200), nullable=True)  # Human-readable location
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def get_status_description(self, status_value: str) -> str:
        """
        Convert raw status value to human-readable description.
        
        Args:
            status_value: Raw status value from telemetry
            
        Returns:
            Human-readable status description
        """
        if not status_value:
            return 'Unknown'
        
        status_map = {
            '0': 'Parked',
            '1': 'Engine Running',
            '2': 'Airborne',
            'parked': 'Parked',
            'engine_running': 'Engine Running',
            'airborne': 'Airborne'
        }
        
        return status_map.get(str(status_value).lower(), f'Status {status_value}')
    
    def update_telemetry(self, telemetry_data: dict) -> None:
        """
        Update device telemetry data from ThingsBoard response.
        
        Args:
            telemetry_data: Dictionary with telemetry values
        """
        from datetime import datetime
        
        # Update telemetry fields if present in data
        if 'fuel' in telemetry_data:
            try:
                self.fuel_quantity = float(telemetry_data['fuel']) if telemetry_data['fuel'] is not None else None
            except (ValueError, TypeError):
                self.fuel_quantity = None
        
        if 'status' in telemetry_data:
            self.status = str(telemetry_data['status'])
            self.status_description = self.get_status_description(self.status)
        
        if 'altitude' in telemetry_data:
            try:
                self.altitude = float(telemetry_data['altitude']) if telemetry_data['altitude'] is not None else None
            except (ValueError, TypeError):
                self.altitude = None
        
        if 'latitude' in telemetry_data:
            try:
                self.latitude = float(telemetry_data['latitude']) if telemetry_data['latitude'] is not None else None
            except (ValueError, TypeError):
                self.latitude = None
        
        if 'longitude' in telemetry_data:
            try:
                self.longitude = float(telemetry_data['longitude']) if telemetry_data['longitude'] is not None else None
            except (ValueError, TypeError):
                self.longitude = None
        
        if 'speed' in telemetry_data:
            try:
                self.speed = float(telemetry_data['speed']) if telemetry_data['speed'] is not None else None
            except (ValueError, TypeError):
                self.speed = None
        
        # Update location description if we have coordinates
        if self.latitude is not None and self.longitude is not None:
            self.location_description = self._get_location_description(self.latitude, self.longitude)
        
        # Update timestamp - use telemetry timestamp if available, otherwise current time
        if '_timestamp' in telemetry_data:
            ts_value = telemetry_data['_timestamp']
            # Convert from milliseconds to seconds for datetime.fromtimestamp
            telemetry_timestamp = datetime.fromtimestamp(ts_value / 1000, tz=timezone.utc)
            self.last_telemetry_update = telemetry_timestamp
            
        self.updated_at = datetime.now(timezone.utc)
    
    def _get_location_description(self, lat: float, lon: float) -> str:
        """
        Get human-readable location description from coordinates using hybrid geocoding.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Location description from hybrid geocoding service
        """
        try:
            from .services.geocoding import reverse_geocode
            return reverse_geocode(lat, lon)
        except ImportError as e:
            # Fallback to basic coordinate display if geocoding service unavailable
            return f"{lat:.4f}°, {lon:.4f}°"
        except Exception as e:
            # Log error and provide fallback
            from flask import current_app
            if current_app:
                current_app.logger.warning(f"Geocoding failed for {lat}, {lon}: {e}")
            return f"{lat:.4f}°, {lon:.4f}°"
    
    def has_recent_telemetry(self, max_age_minutes: int = 30) -> bool:
        """
        Check if device has recent telemetry data.
        
        Args:
            max_age_minutes: Maximum age of telemetry in minutes
            
        Returns:
            True if telemetry is recent, False otherwise
        """
        if not self.last_telemetry_update:
            return False
        
        from datetime import datetime, timedelta
        threshold = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        
        # Handle timezone-naive datetime objects from old database records
        last_update = self.last_telemetry_update
        if last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=timezone.utc)
        
        return last_update > threshold
    
    def get_telemetry_age(self) -> str:
        """
        Get human-readable age of telemetry data.
        
        Returns:
            String describing how old the telemetry data is
        """
        if not self.last_telemetry_update:
            return "No data"
        
        from datetime import datetime, timedelta
        now = datetime.now(timezone.utc)
        
        # Handle timezone-naive datetime objects from old database records
        last_update = self.last_telemetry_update
        if last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=timezone.utc)
        
        age = now - last_update
        
        if age.total_seconds() < 60:
            return "Just now"
        elif age.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(age.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif age.total_seconds() < 86400:  # Less than 1 day
            hours = int(age.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif age.total_seconds() < 2592000:  # Less than 30 days
            days = int(age.total_seconds() / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            # For older data, show the actual date
            return self.last_telemetry_update.strftime("%Y-%m-%d %H:%M")
    
    def get_telemetry_timestamp(self) -> str:
        """
        Get formatted timestamp of last telemetry update.
        
        Returns:
            Formatted timestamp string
        """
        if not self.last_telemetry_update:
            return "Never"
        
        return self.last_telemetry_update.strftime("%Y-%m-%d %H:%M UTC")
    
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
    items = db.Column(db.Text, nullable=False)  # JSON string of checklist items
    json_content = db.Column(db.Text, nullable=False)  # Full JSON content of the checklist
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


class InstrumentLayout(db.Model):
    """Instrument layout model for cockpit instrument configurations."""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instrument_type = db.Column(db.String(50), nullable=False)  # digi, indu_57mm, indu_80mm, altimeter_80mm
    layout_data = db.Column(db.Text, nullable=False)  # JSON string of layout configuration
    xml_content = db.Column(db.Text, nullable=False)  # Full XML content of the layout
    thumbnail_filename = db.Column(db.String(255), nullable=True)  # PNG thumbnail filename (legacy)
    thumbnail_base64 = db.Column(db.Text, nullable=True)  # Base64 encoded PNG thumbnail data
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<InstrumentLayout {self.title}>'
    
    @property
    def thumbnail_data_uri(self):
        """Get thumbnail as data URI for HTML img src."""
        if self.thumbnail_base64:
            return f"data:image/png;base64,{self.thumbnail_base64}"
        return None


class LogbookEntry(db.Model):
    """Logbook entry model for flight logging."""
    
    id = db.Column(db.Integer, primary_key=True)
    takeoff_datetime = db.Column(db.DateTime, nullable=False)  # Takeoff date and time
    landing_datetime = db.Column(db.DateTime, nullable=False)  # Landing date and time
    aircraft_type = db.Column(db.String(50), nullable=False)
    aircraft_registration = db.Column(db.String(20), nullable=False)
    departure_airport = db.Column(db.String(10), nullable=False)
    arrival_airport = db.Column(db.String(10), nullable=False)
    flight_time = db.Column(db.Float, nullable=False)  # Total flight time in hours
    pilot_in_command_time = db.Column(db.Float, default=0.0)
    dual_time = db.Column(db.Float, default=0.0)
    instrument_time = db.Column(db.Float, default=0.0)
    night_time = db.Column(db.Float, default=0.0)
    cross_country_time = db.Column(db.Float, default=0.0)
    landings_day = db.Column(db.Integer, default=0)
    landings_night = db.Column(db.Integer, default=0)
    remarks = db.Column(db.Text)
    pilot_name = db.Column(db.String(100), nullable=True)  # Name of pilot as recorded in logbook
    flight_points_fetched = db.Column(db.Boolean, default=False)  # Track if flight points fetch was attempted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Allow None for unknown pilots
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=True)  # Optional link to device for synced entries
    
    # Relationships
    # Note: user relationship is handled by existing 'pilot' backref from User model
    device = db.relationship('Device', backref=db.backref('device_logbook_entries', lazy=True))
    user = db.relationship('User', overlaps="logbook_entries,pilot")
    
    def get_calculated_flight_time(self) -> float:
        """Calculate flight time in hours from takeoff and landing datetime."""
        if not self.takeoff_datetime or not self.landing_datetime:
            return self.flight_time or 0.0
        
        # Calculate flight duration in hours
        flight_duration = self.landing_datetime - self.takeoff_datetime
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
        
        # If there's a pilot name but no mapping, don't fall back to device owner
        # This keeps unknown pilots unlinked
        if self.pilot_name:
            return None
            
        # If no pilot name is specified, fall back to the entry's user_id
        return self.user
    
    @property
    def date(self) -> datetime.date:
        """Get flight date from takeoff datetime for backward compatibility."""
        return self.takeoff_datetime.date() if self.takeoff_datetime else None
    
    @property
    def takeoff_time(self) -> datetime.time:
        """Get takeoff time from takeoff datetime for backward compatibility."""
        return self.takeoff_datetime.time() if self.takeoff_datetime else None
    
    @property
    def landing_time(self) -> datetime.time:
        """Get landing time from landing datetime for backward compatibility."""
        return self.landing_datetime.time() if self.landing_datetime else None
    
    @property
    def is_synced(self) -> bool:
        """Check if this entry was synced from a device."""
        return self.device_id is not None
    
    def __repr__(self):
        return f'<LogbookEntry {self.date} {self.aircraft_registration}>'


class FlightPoint(db.Model):
    """Flight point model for storing GPS and flight data points."""
    
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)  # Latitude in decimal degrees
    longitude = db.Column(db.Float, nullable=False)  # Longitude in decimal degrees
    airspeed = db.Column(db.Float, nullable=True)  # Airspeed in knots or m/s
    static_pressure = db.Column(db.Float, nullable=True)  # Static pressure in Pa or other units
    sequence = db.Column(db.Integer, nullable=False)  # Order of point in flight (0-based)
    timestamp_offset = db.Column(db.Integer, nullable=False)  # Seconds from flight start
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    logbook_entry_id = db.Column(db.Integer, db.ForeignKey('logbook_entry.id'), nullable=False)
    
    # Relationships
    logbook_entry = db.relationship('LogbookEntry', backref=db.backref('flight_points', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<FlightPoint {self.logbook_entry_id}:{self.sequence} {self.latitude},{self.longitude}>'


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


class Event(db.Model):
    """Event model for device events synced from ThingsBoard."""
    
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, nullable=True)  # Optional event timestamp
    page_address = db.Column(db.BigInteger, nullable=False)  # Page address in device logger
    write_address = db.Column(db.BigInteger, nullable=True)  # Write address from device logger
    total_time = db.Column(db.Integer, nullable=False)  # Total time in milliseconds
    bitfield = db.Column(db.Integer, nullable=False, default=0)  # Event bitfield value
    message = db.Column(db.String(500), nullable=True)  # Optional message/description for the event
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    logbook_entry_id = db.Column(db.Integer, db.ForeignKey('logbook_entry.id'), nullable=True)  # Link to associated logbook entry
    
    # Relationships
    device = db.relationship('Device', backref=db.backref('events', lazy='dynamic', cascade='all, delete-orphan'))
    logbook_entry = db.relationship('LogbookEntry', backref=db.backref('linked_events', lazy='dynamic'))
    
    # Event bit definitions
    EVENT_BITS = {
        'AnyEngStart': 0,      # 1 - Any engine start condition detected
        'Takeoff': 1,          # 2 - Takeoff condition detected  
        'Landing': 2,          # 4 - Aircraft has landed
        'LastEngStop': 3,      # 8 - Last engine stop condition detected
        'Flying': 4,           # 16 - Aircraft is flying
        'EngRun1': 5,          # 32 - Engine 1 running
        'EngRun2': 6,          # 64 - Engine 2 running
        'Alarm': 7,            # 128 - Alarm condition
        'FlushAndLink': 31     # Flush and link operation
    }
    
    def has_event_bit(self, bit_name: str) -> bool:
        """Check if a specific event bit is set."""
        if bit_name not in self.EVENT_BITS:
            return False
        bit_position = self.EVENT_BITS[bit_name]
        return (self.bitfield & (1 << bit_position)) != 0
    
    def get_active_events(self):
        """Get list of active event names based on bitfield."""
        active_events = []
        for event_name, bit_position in self.EVENT_BITS.items():
            if (self.bitfield & (1 << bit_position)) != 0:
                active_events.append(event_name)
        return active_events
    
    def set_event_bit(self, bit_name: str, value: bool = True):
        """Set or clear a specific event bit."""
        if bit_name not in self.EVENT_BITS:
            return
        bit_position = self.EVENT_BITS[bit_name]
        if value:
            self.bitfield |= (1 << bit_position)
        else:
            self.bitfield &= ~(1 << bit_position)
    
    @classmethod
    def get_newest_event_for_device(cls, device_id: int):
        """Get the newest event for a device based on highest page_address."""
        return cls.query.filter_by(device_id=device_id).order_by(cls.page_address.desc()).first()
    
    def format_log_time(self):
        """Format total_time (milliseconds) as H:M:S string."""
        if not self.total_time:
            return "0:00:00"
        
        # Convert milliseconds to seconds
        total_seconds = int(self.total_time / 1000)
        
        # Calculate hours, minutes, seconds
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    
    def __repr__(self):
        active_events = self.get_active_events()
        events_str = ', '.join(active_events) if active_events else 'None'
        return f'<Event {self.id} Device:{self.device_id} Events:[{events_str}]>'


class Airfield(db.Model):
    """ICAO airfield model for geocoding services."""
    
    id = db.Column(db.Integer, primary_key=True)
    icao_code = db.Column(db.String(4), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    country = db.Column(db.String(50))
    region = db.Column(db.String(50))
    elevation_ft = db.Column(db.Integer)  # Elevation in feet
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional aviation-specific fields
    runway_info = db.Column(db.Text)  # JSON string with runway information
    frequencies = db.Column(db.Text)  # JSON string with radio frequencies
    
    def __repr__(self):
        return f'<Airfield {self.icao_code} - {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert airfield to dictionary format."""
        return {
            'id': self.id,
            'icao_code': self.icao_code,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'country': self.country,
            'region': self.region,
            'elevation_ft': self.elevation_ft,
            'is_active': self.is_active,
            'runway_info': self.runway_info,
            'frequencies': self.frequencies
        }
    
    @classmethod
    def find_nearest(cls, latitude: float, longitude: float, max_distance_km: float = 25.0, limit: int = 10):
        """
        Find nearest airfields using database query with distance calculation.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            max_distance_km: Maximum search distance in kilometers
            limit: Maximum number of results to return
            
        Returns:
            List of tuples (airfield, distance_km)
        """
        import math
        
        # Convert max distance to rough coordinate bounds for initial filtering
        # 1 degree latitude ≈ 111 km
        lat_delta = max_distance_km / 111.0
        lon_delta = max_distance_km / (111.0 * math.cos(math.radians(latitude)))
        
        # Query airfields within rough bounding box
        nearby_airfields = cls.query.filter(
            cls.is_active == True,
            cls.latitude >= latitude - lat_delta,
            cls.latitude <= latitude + lat_delta,
            cls.longitude >= longitude - lon_delta,
            cls.longitude <= longitude + lon_delta
        ).all()
        
        # Calculate precise distances and filter
        results = []
        for airfield in nearby_airfields:
            distance = cls._calculate_distance(
                latitude, longitude,
                airfield.latitude, airfield.longitude
            )
            if distance <= max_distance_km:
                results.append((airfield, distance))
        
        # Sort by distance and limit results
        results.sort(key=lambda x: x[1])
        return results[:limit]
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
