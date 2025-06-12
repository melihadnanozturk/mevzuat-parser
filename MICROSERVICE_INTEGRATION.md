# Mikroservis Entegrasyonu Kılavuzu

Bu kılavuz, Türk Mevzuat Çıkarıcı projesini mevcut Python mikroservis projenize nasıl entegre edeceğinizi açıklar.

## Entegrasyon Seçenekleri

### 1. Blueprint Olarak Entegrasyon (Önerilen)

Flask Blueprint kullanarak mevcut Flask uygulamanıza entegre edin.

#### Adımlar:

1. **Dosyaları Kopyalayın**
```
your-microservice/
├── app/
│   ├── legal_parser/           # Yeni modül
│   │   ├── __init__.py
│   │   ├── routes.py           # app.py içeriği
│   │   ├── document_parser.py  # Ayrıştırma motoru
│   │   ├── templates/          # HTML şablonları
│   │   └── static/             # CSS/JS dosyaları
│   └── main.py
```

2. **Blueprint Oluşturun**

`app/legal_parser/__init__.py`:
```python
from flask import Blueprint

legal_parser = Blueprint('legal_parser', __name__, 
                        template_folder='templates',
                        static_folder='static',
                        url_prefix='/legal-parser')

from . import routes
```

3. **Routes Dosyasını Düzenleyin**

`app/legal_parser/routes.py`:
```python
import os
import json
from flask import request, render_template, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from . import legal_parser
from .document_parser import DocumentParser

# Konfigürasyon
UPLOAD_FOLDER = 'app/legal_parser/static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Tüm route'ları @legal_parser.route olarak değiştirin
@legal_parser.route('/')
def index():
    return render_template('legal_parser/index.html')

@legal_parser.route('/upload', methods=['POST'])
def upload_file():
    # Mevcut upload_file fonksiyonu
    pass

# Diğer route'lar...
```

4. **Ana Uygulamaya Kaydedin**

`app/__init__.py` veya `app/main.py`:
```python
from flask import Flask
from app.legal_parser import legal_parser

def create_app():
    app = Flask(__name__)
    
    # Mevcut konfigürasyonlar...
    
    # Legal parser blueprint'ini kaydet
    app.register_blueprint(legal_parser)
    
    return app
```

### 2. Ayrı Servis Olarak Entegrasyon

Mikroservis mimarisinde ayrı bir servis olarak çalıştırın.

#### Docker ile Entegrasyon:

1. **Dockerfile Oluşturun**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements_local.txt .
RUN pip install -r requirements_local.txt

COPY . .

RUN mkdir -p static/uploads

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

2. **Docker Compose ile Entegre Edin**
```yaml
version: '3.8'
services:
  main-service:
    build: ./main-service
    ports:
      - "3000:3000"
    
  legal-parser:
    build: ./legal-parser
    ports:
      - "5000:5000"
    volumes:
      - ./uploads:/app/static/uploads
    environment:
      - SESSION_SECRET=your-secret-key
```

### 3. API Modülü Olarak Entegrasyon

Sadece API endpoint'leri olarak entegre edin.

#### API Wrapper Oluşturun:

`app/legal_parser/api.py`:
```python
from flask import Blueprint, request, jsonify
from .document_parser import DocumentParser
import os
import json

api = Blueprint('legal_parser_api', __name__, url_prefix='/api/legal-parser')

@api.route('/parse', methods=['POST'])
def parse_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Dosyayı geçici olarak kaydet
        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)
        
        # Ayrıştır
        parser = DocumentParser()
        result = parser.parse_document(temp_path)
        
        # Geçici dosyayı sil
        os.remove(temp_path)
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Parsing failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})
```

## Konfigürasyon Değişiklikleri

### 1. Environment Variables

Mevcut mikroservis konfigürasyonunuza ekleyin:

```python
# config.py
import os

class Config:
    # Mevcut konfigürasyonlar...
    
    # Legal Parser konfigürasyonları
    LEGAL_PARSER_UPLOAD_FOLDER = os.environ.get('LEGAL_PARSER_UPLOAD_FOLDER', 'uploads/legal')
    LEGAL_PARSER_MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    LEGAL_PARSER_ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
```

### 2. Database Entegrasyonu (Opsiyonel)

Ayrıştırılan belgeleri veritabanında saklamak için:

```python
# models.py
from app import db
from datetime import datetime

class ParsedDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    title = db.Column(db.Text)
    content_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Eğer user sistemi varsa
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'title': self.title,
            'content': self.content_json,
            'created_at': self.created_at.isoformat()
        }
```

### 3. Logging Entegrasyonu

Mevcut logging sisteminize entegre edin:

```python
# app/legal_parser/routes.py
import logging
from app import logger  # Mevcut logger'ınız

@legal_parser.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Ayrıştırma işlemi
        logger.info(f"Legal document parsing started for file: {filename}")
        result = parser.parse_document(filepath)
        logger.info(f"Legal document parsing completed for file: {filename}")
        
    except Exception as e:
        logger.error(f"Legal document parsing failed: {str(e)}")
        # Hata işleme
```

## Güvenlik Entegrasyonu

### 1. Authentication

Mevcut auth sisteminizle entegre edin:

```python
# app/legal_parser/routes.py
from functools import wraps
from flask import g
from app.auth import require_auth  # Mevcut auth decorator'ünüz

@legal_parser.route('/upload', methods=['POST'])
@require_auth
def upload_file():
    # Sadece authenticate edilmiş kullanıcılar erişebilir
    pass
```

### 2. Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@legal_parser.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_file():
    pass
```

## Monitoring ve Health Checks

### 1. Health Check Endpoint

```python
@legal_parser.route('/health')
def health_check():
    try:
        # Dosya sistemi kontrolü
        upload_dir = current_app.config['LEGAL_PARSER_UPLOAD_FOLDER']
        if not os.path.exists(upload_dir):
            return jsonify({'status': 'unhealthy', 'reason': 'Upload directory missing'}), 503
        
        # Parser kontrolü
        parser = DocumentParser()
        
        return jsonify({
            'status': 'healthy',
            'service': 'legal-parser',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'reason': str(e)}), 503
```

### 2. Metrics

```python
from prometheus_client import Counter, Histogram
import time

parse_requests = Counter('legal_parser_requests_total', 'Total parse requests')
parse_duration = Histogram('legal_parser_duration_seconds', 'Parse duration')

@legal_parser.route('/upload', methods=['POST'])
def upload_file():
    parse_requests.inc()
    start_time = time.time()
    
    try:
        # Ayrıştırma işlemi
        result = parser.parse_document(filepath)
        
    finally:
        parse_duration.observe(time.time() - start_time)
```

## Deployment Önerileri

### 1. Blueprint Entegrasyonu için
- Mevcut deployment pipeline'ınızı kullanabilirsiniz
- Sadece yeni template dosyalarının deployment'a dahil edildiğinden emin olun

### 2. Ayrı Servis için
- Kubernetes deployment:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legal-parser
spec:
  replicas: 2
  selector:
    matchLabels:
      app: legal-parser
  template:
    metadata:
      labels:
        app: legal-parser
    spec:
      containers:
      - name: legal-parser
        image: your-registry/legal-parser:latest
        ports:
        - containerPort: 5000
        env:
        - name: SESSION_SECRET
          valueFrom:
            secretKeyRef:
              name: legal-parser-secrets
              key: session-secret
```

## Test Entegrasyonu

Mevcut test suite'inize ekleyebileceğiniz test örnekleri:

```python
# tests/test_legal_parser.py
import pytest
from app import create_app
from app.legal_parser.document_parser import DocumentParser

@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        yield client

def test_legal_parser_health(client):
    response = client.get('/legal-parser/health')
    assert response.status_code == 200

def test_document_parsing():
    parser = DocumentParser()
    # Test implementation
```

Bu kılavuz, mevcut mikroservis projenizin mimarisine uygun olan entegrasyon yöntemini seçmenize yardımcı olacaktır.