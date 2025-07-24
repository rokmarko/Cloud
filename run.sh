#!/bin/bash

# KanardiaCloud Startup Script
echo "Starting KanardiaCloud..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the Flask application
echo "Starting Flask server at http://localhost:5000"
python main.py
