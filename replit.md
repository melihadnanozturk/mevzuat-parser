# Turkish Legal Document Parser

## Overview

This is a Flask-based web application designed to parse Turkish legal documents (Word and PDF formats) and convert them into structured JSON format. The application provides an intuitive web interface for uploading documents, automatically extracts legal articles and paragraphs, and offers editing capabilities for the parsed content.

## System Architecture

### Backend Architecture
- **Framework**: Flask 3.1.1 with Python 3.11
- **Web Server**: Gunicorn for production deployment
- **Document Processing**: 
  - `python-docx` for Word document processing (.doc, .docx)
  - `pdfplumber` for PDF document processing
- **File Handling**: Werkzeug utilities for secure file uploads
- **Template Engine**: Jinja2 (Flask's default)

### Frontend Architecture
- **UI Framework**: Bootstrap with dark theme (Agent Dark Theme)
- **Icons**: Bootstrap Icons
- **Responsive Design**: Mobile-first approach with Bootstrap grid system
- **JavaScript**: Vanilla JavaScript for dynamic interactions

### Document Processing Engine
The core parsing logic is implemented in `DocumentParser` class with specialized regex patterns for Turkish legal text:
- Article detection patterns for various Turkish legal formats
- Paragraph numbering recognition (both parenthetical and numbered formats)
- Subject header filtering to exclude non-content sections
- Multi-format support (Word and PDF)

## Key Components

### 1. Main Application (`app.py`)
- Primary Flask application setup
- Route definitions for upload, processing, editing, and download
- File upload validation and security measures
- Session management and flash messaging

### 2. Document Parser (`document_parser.py`)
- Text extraction from Word and PDF documents
- Turkish legal document structure recognition
- Article and paragraph parsing with regex patterns
- Metadata extraction and content structuring

### 3. Web Interface Templates
- **`index.html`**: File upload interface with drag-drop support
- **`result.html`**: Display parsed document with preview and download options
- **`edit.html`**: Interactive editing interface for modifying parsed content

### 4. Blueprint Conversion System
- Microservice integration capabilities through Flask Blueprints
- API-only version for headless integration
- Modular architecture for easy integration into existing projects

## Data Flow

1. **Document Upload**: User uploads Word/PDF file through web interface
2. **File Validation**: System validates file type, size, and security
3. **Text Extraction**: Document parser extracts raw text based on file format
4. **Content Parsing**: Turkish legal text patterns are applied to structure content
5. **JSON Generation**: Structured data is converted to JSON format with UTF-8 encoding
6. **Storage**: Processed JSON is saved with unique identifier
7. **User Interface**: Results displayed with editing and download options
8. **Edit Capability**: Interactive editing with real-time updates and auto-save

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **python-docx**: Microsoft Word document processing
- **pdfplumber**: PDF text extraction and processing
- **psycopg2-binary**: PostgreSQL adapter (prepared for database integration)
- **Werkzeug**: WSGI utilities and security features
- **Gunicorn**: WSGI HTTP Server for production deployment

### Frontend Dependencies (CDN)
- **Bootstrap**: CSS framework with dark theme
- **Bootstrap Icons**: Icon library for UI elements

### System Dependencies
- **OpenSSL**: Cryptographic library
- **PostgreSQL**: Database system (configured but not actively used)

## Deployment Strategy

### Development Environment
- Local development with Python virtual environment
- Automated setup scripts for Windows (`run_local.bat`) and Unix (`run_local.sh`)
- Environment variable configuration for session secrets

### Production Deployment
- **Platform**: Replit autoscale deployment
- **Process Manager**: Gunicorn with auto-reload capabilities
- **Port Configuration**: Internal port 5000, external port 80
- **File Storage**: Local filesystem with `static/uploads` directory
- **Session Management**: Environment-based secret key configuration

### Container Configuration
- Nix package management for dependencies
- Python 3.11 module with required system packages
- Workflow automation for parallel task execution

## Changelog

Changelog:
- June 25, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.