"""
Legal Parser API Version - Mikroservis API Entegrasyonu için
Sadece API endpoint'leri sağlar, UI olmadan
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import json
import uuid
import tempfile
from .document_parser import DocumentParser

# API Blueprint
api = Blueprint('legal_parser_api', __name__, url_prefix='/api/legal-parser')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api.route('/parse', methods=['POST'])
def parse_document():
    """
    Belge ayrıştırma API endpoint'i
    
    Request:
        - file: Yüklenecek dosya (multipart/form-data)
    
    Response:
        - JSON formatında ayrıştırılmış belge içeriği
    """
    try:
        # Dosya kontrolü
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'message': 'Dosya yüklenmedi'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'message': 'Dosya seçilmedi'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type',
                'message': 'Desteklenmeyen dosya türü. Sadece PDF, DOC ve DOCX dosyaları kabul edilir.',
                'allowed_extensions': list(ALLOWED_EXTENSIONS)
            }), 400
        
        # Dosya boyutu kontrolü
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': 'File too large',
                'message': f'Dosya boyutu çok büyük. Maksimum {MAX_FILE_SIZE // (1024*1024)}MB dosya yükleyebilirsiniz.',
                'max_size_mb': MAX_FILE_SIZE // (1024*1024)
            }), 413
        
        # Geçici dosya oluştur
        if not file.filename:
            return jsonify({
                'success': False,
                'error': 'Invalid filename',
                'message': 'Geçersiz dosya adı'
            }), 400
        
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Belgeyi ayrıştır
            parser = DocumentParser()
            result = parser.parse_document(temp_path)
            
            if result:
                return jsonify({
                    'success': True,
                    'data': result,
                    'message': 'Belge başarıyla ayrıştırıldı',
                    'original_filename': file.filename
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Parsing failed',
                    'message': 'Belge ayrıştırılamadı. Dosyanın geçerli bir mevzuat belgesi olduğundan emin olun.'
                }), 422
                
        finally:
            # Geçici dosyayı sil
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
    except Exception as e:
        current_app.logger.error(f"API parse error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Sunucu hatası oluştu'
        }), 500

@api.route('/parse-text', methods=['POST'])
def parse_text():
    """
    Metin ayrıştırma API endpoint'i
    Dosya yüklemek yerine direkt metin gönderir
    
    Request:
        - text: Ayrıştırılacak metin (JSON)
        - title: Belge başlığı (opsiyonel)
    
    Response:
        - JSON formatında ayrıştırılmış belge içeriği
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'No text provided',
                'message': 'Ayrıştırılacak metin bulunamadı'
            }), 400
        
        text = data['text']
        if not text or not text.strip():
            return jsonify({
                'success': False,
                'error': 'Empty text',
                'message': 'Boş metin gönderilemez'
            }), 400
        
        # Ayrıştırıcı oluştur ve metni işle
        parser = DocumentParser()
        result = parser._parse_legal_content(text)
        
        # Başlık override edilmişse kullan
        if 'title' in data and data['title']:
            result['mevzuat_basligi'] = data['title']
        
        # Metadata ekle
        result['_metadata'] = {
            'original_filename': data.get('filename', 'text_input'),
            'file_type': 'text',
            'source': 'api_text_input'
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Metin başarıyla ayrıştırıldı'
        })
        
    except Exception as e:
        current_app.logger.error(f"API parse text error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Sunucu hatası oluştu'
        }), 500

@api.route('/validate', methods=['POST'])
def validate_document():
    """
    Belge validasyon endpoint'i
    Ayrıştırılmış JSON formatındaki belgeyi doğrular
    
    Request:
        - document: Validasyon yapılacak belge JSON'u
    
    Response:
        - Validasyon sonucu ve hatalar
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'message': 'Validasyon için veri bulunamadı'
            }), 400
        
        errors = []
        warnings = []
        
        # Temel yapı kontrolü
        if 'mevzuat_basligi' not in data:
            errors.append('Mevzuat başlığı eksik')
        elif not data['mevzuat_basligi'].strip():
            errors.append('Mevzuat başlığı boş olamaz')
        
        if 'maddeler' not in data:
            errors.append('Maddeler bölümü eksik')
        elif not isinstance(data['maddeler'], list):
            errors.append('Maddeler bir liste olmalıdır')
        elif len(data['maddeler']) == 0:
            warnings.append('Hiç madde bulunamadı')
        
        # Maddeler kontrolü
        if 'maddeler' in data and isinstance(data['maddeler'], list):
            for i, madde in enumerate(data['maddeler']):
                if not isinstance(madde, dict):
                    errors.append(f'Madde {i+1}: Geçersiz format')
                    continue
                
                if 'madde_numarasi' not in madde:
                    errors.append(f'Madde {i+1}: Madde numarası eksik')
                elif not madde['madde_numarasi'].strip():
                    errors.append(f'Madde {i+1}: Madde numarası boş olamaz')
                
                if 'fikralar' not in madde:
                    errors.append(f'Madde {i+1}: Fıkralar bölümü eksik')
                elif not isinstance(madde['fikralar'], list):
                    errors.append(f'Madde {i+1}: Fıkralar bir liste olmalıdır')
                elif len(madde['fikralar']) == 0:
                    warnings.append(f'Madde {i+1}: Hiç fıkra bulunamadı')
                else:
                    # Fıkra kontrolü
                    for j, fikra in enumerate(madde['fikralar']):
                        if not isinstance(fikra, str):
                            errors.append(f'Madde {i+1}, Fıkra {j+1}: Fıkra metin olmalıdır')
                        elif not fikra.strip():
                            errors.append(f'Madde {i+1}, Fıkra {j+1}: Fıkra boş olamaz')
        
        # Sonuç
        is_valid = len(errors) == 0
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'message': 'Validasyon tamamlandı',
            'statistics': {
                'total_articles': len(data.get('maddeler', [])),
                'total_paragraphs': sum(len(m.get('fikralar', [])) for m in data.get('maddeler', [])),
                'has_title': bool(data.get('mevzuat_basligi', '').strip())
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"API validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Validasyon sırasında hata oluştu'
        }), 500

@api.route('/health', methods=['GET'])
def health_check():
    """API sağlık kontrolü"""
    try:
        # Parser test
        parser = DocumentParser()
        
        return jsonify({
            'status': 'healthy',
            'service': 'legal-parser-api',
            'version': '1.0.0',
            'endpoints': [
                '/api/legal-parser/parse',
                '/api/legal-parser/parse-text',
                '/api/legal-parser/validate',
                '/api/legal-parser/health'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'service': 'legal-parser-api'
        }), 503

# Hata işleyiciler
@api.errorhandler(413)
def payload_too_large(e):
    """Dosya boyutu çok büyük"""
    return jsonify({
        'success': False,
        'error': 'Payload too large',
        'message': f'Dosya boyutu çok büyük. Maksimum {MAX_FILE_SIZE // (1024*1024)}MB dosya yükleyebilirsiniz.',
        'max_size_mb': MAX_FILE_SIZE // (1024*1024)
    }), 413

@api.errorhandler(400)
def bad_request(e):
    """Geçersiz istek"""
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'Geçersiz istek formatı'
    }), 400