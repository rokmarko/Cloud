#!/usr/bin/env python3
"""
KanardiaCloud - Main Flask application
"""

from src.app import create_app

def main():
    """Main entry point for the KanardiaCloud application."""
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
