"""
Main application routes
"""

from flask import Blueprint, render_template
from flask_login import current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        return render_template('main/index.html', title='Home')
    return render_template('main/landing.html', title='Welcome to KanardiaCloud')
