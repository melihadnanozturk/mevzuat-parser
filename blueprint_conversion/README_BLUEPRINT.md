# Blueprint Entegrasyon Kılavuzu

Bu klasör, Legal Parser projesini mevcut mikroservis projenize entegre etmek için hazırlanmış dosyaları içerir.

## Dosya Açıklaması

### 1. Temel Blueprint Dosyaları
- `__init__.py` - Blueprint tanımlaması
- `routes.py` - Ana web arayüzü route'ları (Blueprint formatı)
- `document_parser.py` - Belge ayrıştırma motoru (değişiklik yok)

### 2. API Versiyonu
- `api_version.py` - Sadece API endpoint'leri (UI olmadan)

### 3. Entegrasyon Örnekleri
- `integration_example.py` - Mevcut Flask uygulamanıza entegrasyon örneği

## Hızlı Entegrasyon

### Adım 1: Dosyaları Kopyalayın
```bash
# Mevcut mikroservis projenizde
mkdir -p app/legal_parser
cp blueprint_conversion/* app/legal_parser/
```

### Adım 2: Template Dosyalarını Taşıyın
```bash
# Template klasörü yapısı
mkdir -p app/legal_parser/templates/legal_parser
cp templates/*.html app/legal_parser/templates/legal_parser/
```

### Adım 3: Ana Uygulamaya Ekleyin
```python
# app/__init__.py veya main.py dosyanızda
from app.legal_parser import legal_parser

def create_app():
    app = Flask(__name__)
    
    # Mevcut konfigürasyonlar...
    
    # Legal parser konfigürasyonu
    app.config['LEGAL_PARSER_UPLOAD_FOLDER'] = '/path/to/uploads'
    
    # Blueprint'i kaydet
    app.register_blueprint(legal_parser)
    
    return app
```

### Adım 4: Erişim
- Web arayüzü: `http://your-app/legal-parser/`
- API: `http://your-app/api/legal-parser/parse`

## Konfigürasyon Seçenekleri

```python
# Gerekli konfigürasyonlar
app.config['LEGAL_PARSER_UPLOAD_FOLDER'] = '/uploads/legal'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Opsiyonel konfigürasyonlar
app.config['LEGAL_PARSER_MAX_FILE_SIZE'] = 16 * 1024 * 1024
app.config['LEGAL_PARSER_ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}
```

## API Kullanımı

### Dosya Ayrıştırma
```bash
curl -X POST \
  http://your-app/api/legal-parser/parse \
  -F "file=@document.pdf"
```

### Metin Ayrıştırma
```bash
curl -X POST \
  http://your-app/api/legal-parser/parse-text \
  -H "Content-Type: application/json" \
  -d '{"text": "MADDE 1 - Bu yönetmelik...", "title": "Örnek Yönetmelik"}'
```

### Sağlık Kontrolü
```bash
curl http://your-app/api/legal-parser/health
```

## Güvenlik Notları

1. **Authentication**: Route'lara auth decorator ekleyin
2. **Rate Limiting**: API endpoint'lerini sınırlayın
3. **File Validation**: Dosya türü ve boyut kontrolü aktif
4. **Path Traversal**: Güvenli dosya adı kullanımı implemented

## Dependency'ler

```python
# requirements.txt'e eklenecekler
python-docx==1.1.2
pdfplumber==0.11.6
```

Bu entegrasyon mevcut mikroservis mimarinizi bozmadan legal parser özelliklerini ekler.