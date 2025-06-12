"""
Legal Parser Routes - Blueprint Version
Mevcut app.py dosyasının blueprint formatına dönüştürülmüş hali
"""

import os
import json
import uuid
from flask import request, render_template, redirect, url_for, flash, send_file, jsonify, current_app
from werkzeug.utils import secure_filename
from . import legal_parser
from .document_parser import DocumentParser

# Konfigürasyon
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def get_upload_folder():
    """Upload klasörünü dinamik olarak al"""
    return current_app.config.get('LEGAL_PARSER_UPLOAD_FOLDER', 
                                 os.path.join(current_app.instance_path, 'legal_parser_uploads'))

def ensure_upload_folder():
    """Upload klasörünün var olduğundan emin ol"""
    upload_folder = get_upload_folder()
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder

def tojson_utf8(obj, indent=None):
    """Convert object to JSON with proper UTF-8 encoding for display."""
    return json.dumps(obj, ensure_ascii=False, indent=indent)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@legal_parser.route('/')
def index():
    """Ana sayfa"""
    return render_template('legal_parser/index.html')

@legal_parser.route('/upload', methods=['POST'])
def upload_file():
    """Dosya yükleme ve işleme"""
    try:
        if 'file' not in request.files:
            flash('Dosya seçilmedi', 'error')
            return redirect(url_for('legal_parser.index'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Dosya seçilmedi', 'error')
            return redirect(url_for('legal_parser.index'))
        
        if not allowed_file(file.filename):
            flash('Desteklenmeyen dosya türü. Sadece PDF, DOC ve DOCX dosyaları yükleyebilirsiniz.', 'error')
            return redirect(url_for('legal_parser.index'))
        
        # Dosya boyutu kontrolü
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            flash('Dosya boyutu çok büyük. Maksimum 16MB dosya yükleyebilirsiniz.', 'error')
            return redirect(url_for('legal_parser.index'))
        
        upload_folder = ensure_upload_folder()
        
        # Güvenli dosya adı oluştur
        if not file.filename:
            flash('Geçersiz dosya adı', 'error')
            return redirect(url_for('legal_parser.index'))
        
        filename = secure_filename(str(file.filename))
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"{unique_id}_{filename}"
        filepath = os.path.join(upload_folder, safe_filename)
        
        # Dosyayı kaydet
        file.save(filepath)
        
        # Belgeyi ayrıştır
        parser = DocumentParser()
        result = parser.parse_document(filepath)
        
        if result:
            # JSON dosyası oluştur
            json_filename = f"{safe_filename}.json"
            json_filepath = os.path.join(upload_folder, json_filename)
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            flash('Dosya başarıyla işlendi!', 'success')
            return render_template('legal_parser/result.html', 
                                 result=result, 
                                 json_filename=json_filename, 
                                 tojson_utf8=tojson_utf8)
        else:
            os.remove(filepath)
            flash('Dosya işlenirken hata oluştu. Dosyanın geçerli bir mevzuat belgesi olduğundan emin olun.', 'error')
            return redirect(url_for('legal_parser.index'))
            
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        flash('Dosya yüklenirken hata oluştu.', 'error')
        return redirect(url_for('legal_parser.index'))

@legal_parser.route('/edit/<json_filename>')
def edit_document(json_filename):
    """Belge düzenleme sayfası"""
    try:
        upload_folder = get_upload_folder()
        filepath = os.path.join(upload_folder, json_filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                result = json.load(f)
            return render_template('legal_parser/edit.html', 
                                 result=result, 
                                 json_filename=json_filename,
                                 tojson_utf8=tojson_utf8)
        else:
            flash('Dosya bulunamadı', 'error')
            return redirect(url_for('legal_parser.index'))
    except Exception as e:
        current_app.logger.error(f"Edit page error: {str(e)}")
        flash('Dosya açılırken hata oluştu', 'error')
        return redirect(url_for('legal_parser.index'))

@legal_parser.route('/save/<json_filename>', methods=['POST'])
def save_document(json_filename):
    """Düzenlenmiş belgeyi kaydet"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Geçersiz veri'})
        
        upload_folder = get_upload_folder()
        filepath = os.path.join(upload_folder, json_filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': 'Değişiklikler kaydedildi'})
    except Exception as e:
        current_app.logger.error(f"Save error: {str(e)}")
        return jsonify({'success': False, 'message': 'Kaydetme hatası oluştu'})

@legal_parser.route('/download/<filename>')
def download_file(filename):
    """JSON dosyası indirme"""
    try:
        upload_folder = get_upload_folder()
        return send_file(
            os.path.join(upload_folder, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        current_app.logger.error(f"Download error: {str(e)}")
        flash('Dosya indirilirken hata oluştu', 'error')
        return redirect(url_for('legal_parser.index'))

@legal_parser.route('/health')
def health_check():
    """Servis sağlık kontrolü"""
    try:
        upload_folder = get_upload_folder()
        
        # Upload klasörü kontrolü
        if not os.path.exists(upload_folder):
            return jsonify({
                'status': 'unhealthy',
                'reason': 'Upload directory missing',
                'service': 'legal-parser'
            }), 503
        
        # Parser kontrolü
        parser = DocumentParser()
        
        return jsonify({
            'status': 'healthy',
            'service': 'legal-parser',
            'upload_folder': upload_folder,
            'timestamp': json.dumps(None, default=str)
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'reason': str(e),
            'service': 'legal-parser'
        }), 503

# Hata işleyicileri
@legal_parser.errorhandler(413)
def too_large(e):
    """Dosya boyutu çok büyük hatası"""
    flash('Dosya boyutu çok büyük. Maksimum 16MB dosya yükleyebilirsiniz.', 'error')
    return redirect(url_for('legal_parser.index'))