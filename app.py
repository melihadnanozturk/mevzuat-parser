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

# Custom filter for UTF-8 JSON display
@app.template_filter('tojson_utf8')
def tojson_utf8(obj, indent=None):
    """Convert object to JSON with proper UTF-8 encoding for display."""
    return json.dumps(obj, ensure_ascii=False, indent=indent, separators=(',', ': '))

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
        
        if file and file.filename and allowed_file(file.filename):
            # Generate unique filename to avoid conflicts
            filename = secure_filename(file.filename or "unknown")
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save the uploaded file
            file.save(filepath)
            
            try:
                # Get file extension
                file_extension = filepath.lower().split('.')[-1]
                
                # Parse the document
                parser = DocumentParser()
                result = parser.parse_document(filepath)
                
                if result is None:
                    flash('Dosya işlenirken hata oluştu. Dosya formatını kontrol edin.', 'error')
                    return redirect(url_for('index'))
                
                # Generate JSON file for download
                json_filename = f"mevzuat_{uuid.uuid4().hex}.json"
                json_filepath = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
                
                # Store original file info with result
                result['_metadata'] = {
                    'original_filename': filename,
                    'original_file_path': unique_filename,
                    'file_type': file_extension
                }
                
                with open(json_filepath, 'w', encoding='utf-8') as json_file:
                    json.dump(result, json_file, ensure_ascii=False, indent=2)
                
                # Keep the original file for PDF viewing (don't delete it)
                
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

@app.route('/edit/<json_filename>')
def edit_document(json_filename):
    """Edit document page with inline editing capabilities."""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                result = json.load(f)
            return render_template('edit.html', result=result, json_filename=json_filename)
        else:
            flash('Dosya bulunamadı', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Edit page error: {str(e)}")
        flash('Dosya açılırken hata oluştu', 'error')
        return redirect(url_for('index'))

@app.route('/save/<json_filename>', methods=['POST'])
def save_document(json_filename):
    """Save edited document data."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Geçersiz veri'})
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': 'Değişiklikler kaydedildi'})
    except Exception as e:
        app.logger.error(f"Save error: {str(e)}")
        return jsonify({'success': False, 'message': 'Kaydetme hatası oluştu'})

@app.route('/result/<json_filename>')
def view_result(json_filename):
    """Display the current JSON data as a result page."""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                result = json.load(f)
            return render_template('result.html', result=result, json_filename=json_filename, tojson_utf8=tojson_utf8)
        else:
            flash('Dosya bulunamadı', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Result view error: {str(e)}")
        flash('Dosya açılırken hata oluştu', 'error')
        return redirect(url_for('index'))

@app.route('/view-pdf/<json_filename>')
def view_pdf(json_filename):
    """Serve the original PDF file for viewing."""
    try:
        json_filepath = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        if os.path.exists(json_filepath):
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if '_metadata' in data and data['_metadata']['file_type'] == 'pdf':
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], data['_metadata']['original_file_path'])
                if os.path.exists(pdf_path):
                    return send_file(pdf_path, mimetype='application/pdf')
        
        return "PDF dosyası bulunamadı", 404
    except Exception as e:
        app.logger.error(f"PDF view error: {str(e)}")
        return "PDF görüntüleme hatası", 500

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
