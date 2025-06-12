"""
Document Parser - Blueprint Version
Mevcut document_parser.py dosyasının kopyası (değişiklik yok)
"""

import re
import logging
from typing import Dict, List, Optional
from docx import Document
import pdfplumber

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DocumentParser:
    """Parser for Turkish legal documents in Word and PDF formats."""
    
    def __init__(self):
        self.subject_headers = {
            'dayanak', 'amaç', 'kapsam', 'tanımlar', 'tanım', 'ilkeler',
            'başvuru', 'değerlendirme', 'kabul', 'kayıt', 'öğretim',
            'sınav', 'mezuniyet', 'yürürlük', 'geçici', 'son hükümler',
            'ek madde', 'geçici madde'
        }
    
    def _is_subject_header(self, line: str) -> bool:
        """Check if a line is a subject header that should be excluded from paragraphs."""
        line_clean = line.strip().lower()
        line_clean = re.sub(r'[^\w\s]', '', line_clean)
        
        return any(header in line_clean for header in self.subject_headers)
    
    def parse_document(self, filepath: str) -> Optional[Dict]:
        """Parse a document and extract legal content."""
        try:
            if filepath.lower().endswith(('.doc', '.docx')):
                text = self._extract_text_from_word(filepath)
            elif filepath.lower().endswith('.pdf'):
                text = self._extract_text_from_pdf(filepath)
            else:
                logger.error(f"Unsupported file format: {filepath}")
                return None
            
            if not text:
                logger.error("No text extracted from document")
                return None
            
            result = self._parse_legal_content(text)
            result['_metadata'] = {
                'original_filename': filepath.split('/')[-1],
                'original_file_path': filepath,
                'file_type': 'pdf' if filepath.lower().endswith('.pdf') else 'word'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing document: {str(e)}")
            return None
    
    def _extract_text_from_word(self, filepath: str) -> str:
        """Extract text from Word document."""
        try:
            doc = Document(filepath)
            text = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text.strip())
            
            return '\n'.join(text)
            
        except Exception as e:
            logger.error(f"Error extracting text from Word document: {str(e)}")
            return ""
    
    def _extract_text_from_pdf(self, filepath: str) -> str:
        """Extract text from PDF document."""
        try:
            text = []
            
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            
            return '\n'.join(text)
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def _parse_legal_content(self, text: str) -> Dict:
        """Parse the extracted text to identify title, articles, and paragraphs."""
        text = self._clean_text(text)
        
        title = self._extract_title(text)
        articles = self._extract_articles(text)
        
        return {
            'mevzuat_basligi': title,
            'maddeler': articles
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive line breaks
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def _extract_title(self, text: str) -> str:
        """Extract document title using improved heuristics."""
        lines = text.split('\n')
        
        # Look for common Turkish regulation patterns in first few lines
        for i, line in enumerate(lines[:10]):
            line_clean = line.strip().upper()
            
            # Skip metadata and date information
            if any(skip_pattern in line_clean for skip_pattern in [
                'SAYILI', 'TARİHLİ', 'KARAR', 'SAYI:', 'TARİH:', 'GÜNDEM',
                'SENATONUN', 'YÖNETİM KURULU', 'KABUL EDİLMİŞTİR'
            ]):
                continue
            
            # Title indicators
            if any(title_pattern in line_clean for title_pattern in [
                'YÖNETMELİĞİ', 'ESASLARI', 'TALİMATI', 'YÖNERGESİ',
                'KANUNU', 'KARARI', 'GENELGESİ', 'TEBLİĞİ'
            ]) and len(line.strip()) > 10:
                return line.strip()
        
        # Fallback to first substantial line
        for line in lines[:5]:
            if len(line.strip()) > 20 and not re.match(r'^\d+\.?\s', line.strip()):
                return line.strip()
        
        return "Belge Başlığı Bulunamadı"
    
    def _extract_articles(self, text: str) -> List[Dict]:
        """Extract articles and their paragraphs."""
        articles = []
        
        # Improved article pattern to catch various formats
        article_pattern = r'(?:^|\n)\s*(?:MADDE\s+(\d+)|Madde\s+(\d+))\s*[-–—]?\s*(.*?)(?=(?:\n\s*(?:MADDE\s+\d+|Madde\s+\d+))|$)'
        
        matches = re.finditer(article_pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            article_num = match.group(1) or match.group(2)
            article_content = match.group(3).strip()
            
            if not article_content:
                continue
            
            # Create article header
            article_header = f"Madde {article_num}"
            if match.group(3) and len(match.group(3).strip()) > 0:
                first_line = match.group(3).strip().split('\n')[0].strip()
                if first_line and not first_line.startswith(('1)', '(1)', 'a)', '(a)')):
                    article_header += f" - {first_line}"
            
            paragraphs = self._extract_paragraphs(article_content)
            
            if paragraphs:
                articles.append({
                    'madde_numarasi': article_header,
                    'fikralar': paragraphs
                })
        
        return articles
    
    def _extract_paragraphs(self, article_content: str) -> List[str]:
        """Extract paragraphs from article content with proper numbered paragraph and sub-item handling."""
        paragraphs = []
        lines = article_content.split('\n')
        current_paragraph = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip parenthetical metadata
            if re.match(r'^\(.*\)$', line):
                logger.debug(f"Skipping parenthetical metadata: {line}")
                continue
            
            # Skip subject headers
            if self._is_subject_header(line):
                logger.debug(f"Skipping subject header: {line}")
                continue
            
            # Check for numbered paragraphs (1), 2), a), b), etc.
            numbered_match = re.match(r'^(\d+\)|[a-zA-Z]\)|\(\d+\)|\([a-zA-Z]\))', line)
            
            if numbered_match:
                # Save previous paragraph if exists
                if current_paragraph:
                    paragraphs.append(current_paragraph.strip())
                
                # Start new paragraph
                current_paragraph = line
            else:
                # Continue current paragraph
                if current_paragraph:
                    current_paragraph += " " + line
                else:
                    current_paragraph = line
        
        # Add the last paragraph
        if current_paragraph:
            paragraphs.append(current_paragraph.strip())
        
        # Filter out very short or invalid paragraphs
        valid_paragraphs = []
        for para in paragraphs:
            if len(para) > 10 and not self._is_subject_header(para):
                valid_paragraphs.append(para)
        
        return valid_paragraphs
    
    def _clean_article_header(self, header: str) -> str:
        """Clean and standardize article header."""
        # Remove extra whitespace and normalize
        header = re.sub(r'\s+', ' ', header.strip())
        
        # Ensure proper format
        if not header.upper().startswith('MADDE'):
            header = f"Madde {header}"
        
        return header