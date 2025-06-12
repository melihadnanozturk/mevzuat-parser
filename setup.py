#!/usr/bin/env python3
"""
Setup script for Turkish Legal Document Parser
"""

import os
import subprocess
import sys

def create_directories():
    """Create necessary directories"""
    directories = [
        'static/uploads',
        'templates'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def install_requirements():
    """Install Python requirements"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_local.txt'])
        print("Successfully installed all requirements")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)

def main():
    print("Setting up Turkish Legal Document Parser...")
    print("=" * 50)
    
    # Create directories
    print("\n1. Creating directories...")
    create_directories()
    
    # Install requirements
    print("\n2. Installing Python packages...")
    install_requirements()
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("\nTo run the application:")
    print("  python main.py")
    print("\nThe application will be available at:")
    print("  http://localhost:5000")

if __name__ == '__main__':
    main()