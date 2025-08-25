"""
Flask application factory
"""

import os
import logging
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_environment_variables():
    """Load environment variables from .env files."""
    base_dir = Path(__file__).parent.parent
    
    # Try production env first, then fallback to .env
    env_files = ['.env.production', '.env']
    
    for env_file in env_files:
        env_path = base_dir / env_file
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
            logger.info(f"Environment loaded from {env_file}")
            return env_file
    
    logger.warning("No .env file found")
    return None

# Load environment variables at module level
load_environment_variables()


def create_app():
    """Create and configure the Flask application."""
    # Configure Flask to look for templates in the parent directory
    import os
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///kanardiacloud.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Email configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT') or 587)
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # API configuration
    app.config['EXTERNAL_API_KEY'] = os.environ.get('EXTERNAL_API_KEY')
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        # Import here to avoid circular imports
        from src.models import User
        return User.query.get(int(user_id))
    
    # Make CSRF token available to all templates
    @app.template_global()
    def csrf_token():
        from flask_wtf.csrf import generate_csrf
        return generate_csrf()
    
    # Import models to ensure they are registered with SQLAlchemy
    from src import models
    
    # Register blueprints
    from src.routes.auth import auth_bp
    from src.routes.main import main_bp
    from src.routes.dashboard import dashboard_bp
    from src.routes.api import api_bp
    from src.routes.admin import admin_bp
    from src.routes.notam_routes import notam_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(notam_bp, url_prefix='/notams')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Initialize background tasks
    from src.services.scheduler import task_scheduler
    task_scheduler.init_app(app)
    
    return app
