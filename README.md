# Türk Mevzuat Çıkarıcı

Flask tabanlı bir web uygulaması ile Türkçe hukuki belgeleri (Word ve PDF) ayrıştırarak yapılandırılmış JSON formatına dönüştürür.

## Özellikler

- **Dosya Desteği**: Word (.doc, .docx) ve PDF formatlarını destekler
- **Türkçe Hukuki Metin Ayrıştırma**: Mevzuat başlığı, maddeler ve fıkraları otomatik ayırır
- **Düzenleme Arayüzü**: Çıkarılan metinleri düzenleyebilir, madde/fıkra ekleyip silebilirsiniz
- **JSON Dışa Aktarma**: Sonuçları JSON formatında indirebilirsiniz
- **Otomatik Kaydetme**: Değişiklikler otomatik olarak kaydedilir

## Kurulum

### 1. Gereksinimler

- Python 3.11 veya üzeri
- pip (Python paket yöneticisi)

### 2. Proje Dosyalarını İndirin

```bash
git clone [repository-url]
cd turkish-legal-document-parser
```

### 3. Sanal Ortam Oluşturun (Önerilen)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 4. Bağımlılıkları Yükleyin

```bash
pip install -r requirements_local.txt
```

### 5. Gerekli Klasörleri Oluşturun

```bash
mkdir -p static/uploads
```

## Çalıştırma

### Geliştirme Ortamı

```bash
python main.py
```

Uygulama `http://localhost:5000` adresinde çalışacaktır.

### Üretim Ortamı

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## Kullanım

1. **Dosya Yükleme**: Ana sayfada Word veya PDF dosyanızı seçin
2. **Ayrıştırma**: Dosya otomatik olarak ayrıştırılır ve sonuçlar görüntülenir
3. **Düzenleme**: "Düzenle" butonuna tıklayarak metinleri düzenleyebilirsiniz
4. **Kaydetme**: Değişiklikler otomatik kaydedilir veya "Kaydet" butonunu kullanabilirsiniz
5. **İndirme**: JSON formatında sonuçları indirebilirsiniz

## Desteklenen Dosya Formatları

- **Word**: .doc, .docx
- **PDF**: .pdf (metin tabanlı)

## Proje Yapısı

```
├── app.py              # Ana Flask uygulaması
├── main.py            # Uygulama başlatıcı
├── document_parser.py  # Belge ayrıştırma motoru
├── templates/         # HTML şablonları
│   ├── index.html     # Ana sayfa
│   ├── result.html    # Sonuç sayfası
│   └── edit.html      # Düzenleme sayfası
├── static/           # Statik dosyalar
│   └── uploads/      # Yüklenen dosyalar
└── requirements_local.txt  # Python bağımlılıkları
```

## Teknolojiler

- **Backend**: Flask, Python
- **Belge İşleme**: python-docx, pdfplumber
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Stil**: Replit Bootstrap Dark Theme

## Özelleştirme

### Yeni Belge Türleri Eklemek

`document_parser.py` dosyasındaki `DocumentParser` sınıfını düzenleyerek yeni belge türleri ekleyebilirsiniz.

### Ayrıştırma Kurallarını Değiştirmek

Türkçe hukuki metin ayrıştırma kuralları `document_parser.py` dosyasında tanımlanmıştır. Bu kuralları ihtiyacınıza göre özelleştirebilirsiniz.

## Sorun Giderme

### Yaygın Hatalar

1. **Dosya Yükleme Hatası**: `static/uploads` klasörünün var olduğundan emin olun
2. **PDF Ayrıştırma Hatası**: PDF dosyasının metin tabanlı olduğundan emin olun
3. **Türkçe Karakter Sorunu**: Dosyalarınızın UTF-8 kodlamasında olduğundan emin olun

### Loglar

Uygulama debug modunda çalışır ve hata mesajları konsola yazdırılır.

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'i push edin (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

## Destek

Herhangi bir sorun yaşarsanız veya öneriniz varsa lütfen issue oluşturun.