#!/bin/bash

echo "Starting Turkish Legal Document Parser..."
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements_local.txt

# Create uploads directory
if [ ! -d "static/uploads" ]; then
    mkdir -p static/uploads
fi

# Set environment variable for session secret
export SESSION_SECRET="your-secret-key-change-this-in-production"

# Start the application
echo "Starting application..."
echo "Application will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
python main.py