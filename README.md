# KanardiaCloud

A comprehensive Python Flask application for aviation management with user authentication, device tracking, checklists, and logbook functionality.

## Features

### Authentication System
- **User Registration** with email verification
- **Secure Login** with session management
- **Password Reset** functionality via email
- **Email Verification** for new accounts

### Dashboard & Navigation
- **Responsive Bootstrap UI** with sidebar navigation
- **Dashboard Overview** with statistics and recent activity
- **User-friendly Interface** optimized for aviation professionals

### Core Features
- **🛩️ Devices**: Manage aircraft and aviation equipment
- **✅ Checklists**: Create and organize flight checklists by category
- **🗺️ Approach Charts**: Access navigation charts (coming soon)
- **📖 Logbook**: Digital flight logging with detailed entries

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: Bootstrap 5, Jinja2 templates
- **Database**: SQLite (development), PostgreSQL ready
- **Email**: Flask-Mail for verification and password reset
- **Forms**: WTForms with CSRF protection

## Installation

1. **Clone and setup the project**:
   ```bash
   cd /path/to/project
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

5. **Access the application**:
   - Open http://localhost:5000 in your browser
   - Register a new account or login

## Configuration

Edit the `.env` file with your settings:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database
DATABASE_URL=sqlite:///kanardiacloud.db

# Email (for verification and password reset)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

## Project Structure

```
KanardiaCloud/
├── src/
│   ├── __init__.py
│   ├── app.py              # Flask application factory
│   ├── models.py           # Database models
│   ├── forms/              # WTForms for user input
│   └── routes/             # Application routes
│       ├── auth.py         # Authentication routes
│       ├── dashboard.py    # Dashboard and features
│       └── main.py         # Main/landing routes
├── templates/              # Jinja2 templates
│   ├── base.html          # Base template with Bootstrap
│   ├── auth/              # Authentication templates
│   ├── dashboard/         # Dashboard templates
│   └── main/              # Landing page templates
├── venv/                  # Virtual environment
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Usage

### Getting Started
1. **Register**: Create a new account with email verification
2. **Login**: Access your dashboard after email verification
3. **Navigate**: Use the sidebar to access different features

### Managing Devices
- Add aircraft, radios, GPS units, and other equipment
- Track serial numbers, models, and registrations
- Edit or remove devices as needed

### Creating Checklists
- Build custom checklists for different flight phases
- Organize by categories (preflight, takeoff, landing, emergency)
- View and use checklists during operations

### Logbook Entries
- Record detailed flight information
- Track different types of flight time (PIC, dual, instrument, etc.)
- Maintain comprehensive flight records

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Database Operations
The application automatically creates database tables on first run. For production deployments, consider using Flask-Migrate for database migrations.

## Security Features

- **CSRF Protection** on all forms
- **Password Hashing** using Werkzeug
- **Session Management** with Flask-Login
- **Email Verification** for account activation
- **Secure Password Reset** with time-limited tokens

## Contributing

1. Follow PEP 8 style guidelines
2. Write tests for new functionality
3. Update documentation as needed
4. Use type hints where appropriate

## License

This project is open source. Add your license information here.

## Support

For issues and questions, please create an issue in the project repository.
