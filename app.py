import os
import logging
import json
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from document_parser import DocumentParser
import tempfile
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'doc', 'docx', 'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with file upload form."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('Dosya seçilmedi', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('Dosya seçilmedi', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Generate unique filename to avoid conflicts
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save the uploaded file
            file.save(filepath)
            
            try:
                # Parse the document
                parser = DocumentParser()
                result = parser.parse_document(filepath)
                
                if result is None:
                    flash('Dosya işlenirken hata oluştu. Dosya formatını kontrol edin.', 'error')
                    return redirect(url_for('index'))
                
                # Generate JSON file for download
                json_filename = f"mevzuat_{uuid.uuid4().hex}.json"
                json_filepath = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
                
                with open(json_filepath, 'w', encoding='utf-8') as json_file:
                    json.dump(result, json_file, ensure_ascii=False, indent=2)
                
                # Clean up the original uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return render_template('result.html', 
                                     result=result, 
                                     json_filename=json_filename,
                                     original_filename=filename)
                
            except Exception as e:
                app.logger.error(f"Error parsing document: {str(e)}")
                flash(f'Dosya işlenirken hata oluştu: {str(e)}', 'error')
                
                # Clean up uploaded file on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return redirect(url_for('index'))
        
        else:
            flash('Geçersiz dosya formatı. Sadece .doc, .docx ve .pdf dosyaları kabul edilir.', 'error')
            return redirect(url_for('index'))
    
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        flash('Dosya yüklenirken hata oluştu.', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download the generated JSON file."""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=filename)
        else:
            flash('Dosya bulunamadı', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        flash('Dosya indirilirken hata oluştu', 'error')
        return redirect(url_for('index'))

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    flash('Dosya çok büyük. Maksimum dosya boyutu 16MB.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
