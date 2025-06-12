"""
Mevcut Mikroservis Projenize Legal Parser Blueprint'ini Entegre Etme Örneği
"""

from flask import Flask
from blueprint_conversion import legal_parser
import os

def create_app_with_legal_parser():
    """
    Mevcut Flask uygulamanızın __init__.py veya app.py dosyasına 
    ekleyebileceğiniz kod örneği
    """
    
    app = Flask(__name__)
    
    # Mevcut konfigürasyonlarınız...
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Legal Parser için gerekli konfigürasyonlar
    app.config['LEGAL_PARSER_UPLOAD_FOLDER'] = os.path.join(
        app.instance_path, 'legal_parser_uploads'
    )
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # Mevcut blueprint'leriniz...
    # app.register_blueprint(auth_bp)
    # app.register_blueprint(api_bp)
    
    # Legal Parser Blueprint'ini kaydetme
    app.register_blueprint(legal_parser)
    
    # Instance klasörünü oluştur
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    return app

# Örnek kullanım:
if __name__ == '__main__':
    app = create_app_with_legal_parser()
    app.run(debug=True, port=5000)