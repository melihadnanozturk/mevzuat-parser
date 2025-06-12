import re
import logging
from docx import Document
import pdfplumber
from typing import Dict, List, Optional

class DocumentParser:
    """Parser for Turkish legal documents in Word and PDF formats."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Regex patterns for Turkish legal documents
        self.article_patterns = [
            r'(?:^|\n)\s*(?:MADDE|Madde)\s+(\d+|[IVXLCDM]+)\s*[–\-:]\s*',
            r'(?:^|\n)\s*(?:MADDE|Madde)\s+(\d+|[IVXLCDM]+)\s*\.?\s*',
            r'(?:^|\n)\s*(\d+)\s*\.\s*(?:MADDE|Madde)\s*[–\-:]?\s*'
        ]
        
        # Pattern for numbered paragraph markers (main paragraphs)
        self.main_paragraph_pattern = r'^\s*(\d+)\)\s*'
        
        # Pattern for lettered sub-items
        self.sub_item_pattern = r'^\s*([a-z])\)\s*'
        
        # Patterns for subject headers that should be excluded from paragraphs
        self.subject_header_patterns = [
            r'^\s*(?:DAYANAK|dayanak)\s*(?:/|\|)?\s*(?:AMAÇ|amaç)\s*(?:/|\|)?\s*(?:KAPSAM|kapsam)?\s*$',
            r'^\s*(?:TANIM|tanım|TANIMLAR|tanımlar|TARİF|tarif|TARİFLER|tarifler)\s*$',
            r'^\s*(?:DANIŞMAN|danışman)\s*$',
            r'^\s*(?:DANIŞMANLIK|danışmanlık)\s+(?:KRİTERLERİ|kriterleri)\s*$',
            r'^\s*(?:DANIŞMANIN|danışmanın)\s+(?:GÖREVLERİ|görevleri)\s*$',
            r'^\s*(?:DANIŞMAN|danışman)\s+(?:GÖREVLENDİRİLMESİ|görevlendirilmesi)\s*$',
            r'^\s*(?:DANIŞMAN|danışman)\s+(?:TERCİHİ|tercihi)\s+(?:VE|ve)\s+(?:ATANMASI|atanması)\s*$',
            r'^\s*(?:DANIŞMAN|danışman)\s+(?:DEĞİŞİKLİĞİ|değişikliği)\s*$',
            r'^\s*(?:ZORUNLU|zorunlu)\s+(?:HALLERDE|hallerde)\s+(?:DANIŞMAN|danışman)\s+(?:DEĞİŞİKLİĞİ|değişikliği)\s*$',
            r'^\s*(?:İKİNCİ|ikinci)\s+(?:TEZ|tez)\s+(?:DANIŞMANI|danışmanı)\s+(?:ATAMA|atama)\s*(?:\(.*\))?\s*$',
            r'^\s*(?:YÜRÜRLÜK|yürürlük)\s*$',
            r'^\s*(?:AMAÇ|amaç)\s*$',
            r'^\s*(?:KAPSAM|kapsam)\s*$',
            r'^\s*(?:DAYANAK|dayanak)\s*$',
            r'^\s*(?:BAŞVURU|başvuru)\s*(?:ŞARTLARI|şartları)?\s*$',
            r'^\s*(?:UYGULAMA|uygulama)\s*(?:ESASLARI|esasları)?\s*$',
            r'^\s*(?:DEĞERLENDIRME|değerlendirme)\s*(?:KRİTERLERİ|kriterleri)?\s*$',
            r'^\s*(?:İLGİLİ|ilgili)\s+(?:MEVZUAT|mevzuat)\s*$',
            r'^\s*(?:GENEL|genel)\s+(?:HÜKÜMLER|hükümler)\s*$',
            r'^\s*(?:ÖZEL|özel)\s+(?:HÜKÜMLER|hükümler)\s*$',
            r'^\s*(?:SON|son)\s+(?:HÜKÜMLER|hükümler)\s*$'
        ]
        
    def _is_subject_header(self, line: str) -> bool:
        """Check if a line is a subject header that should be excluded from paragraphs."""
        line = line.strip()
        
        # Skip very short lines (less than 3 characters)
        if len(line) < 3:
            return False
            
        # Check against subject header patterns
        for pattern in self.subject_header_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True
        
        # Additional heuristics for subject headers
        # Check if line is short (less than 50 chars), mostly uppercase, and doesn't end with punctuation
        if (len(line) < 50 and 
            line.isupper() and 
            not line.endswith(('.', ':', ';', '!', '?')) and
            not re.search(r'\d', line)):  # No numbers
            return True
            
        # Check if line contains common subject header words and is relatively short
        subject_keywords = [
            'dayanak', 'amaç', 'kapsam', 'tanım', 'danışman', 'yürürlük', 
            'başvuru', 'uygulama', 'değerlendirme', 'genel', 'özel', 'son'
        ]
        
        if (len(line) < 80 and 
            any(keyword in line.lower() for keyword in subject_keywords) and
            len(line.split()) <= 5):  # Maximum 5 words
            return True
            
        return False
        
    def parse_document(self, filepath: str) -> Optional[Dict]:
        """Parse a document and extract legal content."""
        try:
            file_extension = filepath.lower().split('.')[-1]
            
            if file_extension in ['doc', 'docx']:
                text = self._extract_text_from_word(filepath)
            elif file_extension == 'pdf':
                text = self._extract_text_from_pdf(filepath)
            else:
                self.logger.error(f"Unsupported file format: {file_extension}")
                return None
                
            if not text:
                self.logger.error("No text extracted from document")
                return None
                
            return self._parse_legal_content(text)
            
        except Exception as e:
            self.logger.error(f"Error parsing document: {str(e)}")
            return None
    
    def _extract_text_from_word(self, filepath: str) -> str:
        """Extract text from Word document."""
        try:
            doc = Document(filepath)
            paragraphs = []
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    paragraphs.append(text)
            
            return '\n'.join(paragraphs)
            
        except Exception as e:
            self.logger.error(f"Error extracting text from Word document: {str(e)}")
            return ""
    
    def _extract_text_from_pdf(self, filepath: str) -> str:
        """Extract text from PDF document."""
        try:
            text_content = []
            
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            
            return '\n'.join(text_content)
            
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def _parse_legal_content(self, text: str) -> Dict:
        """Parse the extracted text to identify title, articles, and paragraphs."""
        try:
            # Clean up the text
            text = self._clean_text(text)
            
            # Extract title
            title = self._extract_title(text)
            
            # Extract articles
            articles = self._extract_articles(text)
            
            return {
                "mevzuat_basligi": title,
                "maddeler": articles
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing legal content: {str(e)}")
            return {
                "mevzuat_basligi": "Başlık tespit edilemedi",
                "maddeler": []
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()
    
    def _extract_title(self, text: str) -> str:
        """Extract document title using heuristics."""
        lines = text.split('\n')
        
        # Look for title in first 10 lines
        candidates = []
        
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if not line:
                continue
                
            # Skip very short lines (less than 10 characters)
            if len(line) < 10:
                continue
                
            # Skip lines that look like article headers
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.article_patterns):
                continue
                
            # Prefer longer lines and lines appearing early
            score = len(line) + (10 - i) * 5
            
            # Bonus for all caps (common in titles)
            if line.isupper():
                score += 20
                
            # Bonus for centered-looking text (has spaces at start/end)
            if line.startswith(' ') or line.endswith(' '):
                score += 10
                
            candidates.append((score, line))
        
        if candidates:
            # Return the highest scoring candidate
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1].strip()
        
        return "Mevzuat Başlığı Tespit Edilemedi"
    
    def _extract_articles(self, text: str) -> List[Dict]:
        """Extract articles and their paragraphs."""
        articles = []
        
        # Find all article positions
        article_matches = []
        for pattern in self.article_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            for match in matches:
                article_matches.append((match.start(), match.end(), match.group().strip()))
        
        # Sort by position
        article_matches.sort(key=lambda x: x[0])
        
        if not article_matches:
            self.logger.warning("No articles found in document")
            return []
        
        # Remove duplicates and overlapping matches
        filtered_matches = []
        for start_pos, end_pos, article_header in article_matches:
            # Check if this match overlaps with any existing match
            is_duplicate = False
            for existing_start, existing_end, existing_header in filtered_matches:
                # If positions are very close (within 10 characters), consider it a duplicate
                if abs(start_pos - existing_start) <= 10:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_matches.append((start_pos, end_pos, article_header))
        
        # Extract content for each unique article
        for i, (start_pos, end_pos, article_header) in enumerate(filtered_matches):
            # Determine the end position of this article's content
            if i + 1 < len(filtered_matches):
                content_end = filtered_matches[i + 1][0]
            else:
                content_end = len(text)
            
            # Extract article content
            article_content = text[end_pos:content_end].strip()
            
            # Parse paragraphs
            paragraphs = self._extract_paragraphs(article_content)
            
            # Clean up article header
            article_number = self._clean_article_header(article_header)
            
            # Only add articles that have content
            if paragraphs:
                articles.append({
                    "madde_numarasi": article_number,
                    "fikralar": paragraphs
                })
        
        return articles
    
    def _extract_paragraphs(self, article_content: str) -> List[str]:
        """Extract paragraphs from article content with proper numbered paragraph and sub-item handling."""
        paragraphs = []
        
        # Process all lines together to maintain order
        lines = article_content.split('\n')
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip subject headers
            if self._is_subject_header(line):
                self.logger.debug(f"Skipping subject header: {line}")
                continue
            
            # Check if line starts with numbered paragraph marker like "1)", "2)", etc.
            main_paragraph_match = re.match(self.main_paragraph_pattern, line)
            
            if main_paragraph_match:
                # Save previous paragraph if exists
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph).strip()
                    if paragraph_text and not self._is_subject_header(paragraph_text):
                        paragraphs.append(paragraph_text)
                
                # Start new main paragraph
                current_paragraph = [line]
                
            else:
                # Check if line starts with lettered sub-item like "a)", "b)", etc.
                sub_item_match = re.match(self.sub_item_pattern, line)
                
                if sub_item_match:
                    # This is a sub-item, add it to current paragraph
                    if current_paragraph:
                        current_paragraph.append(line)
                    else:
                        # If no current paragraph, treat as standalone content
                        current_paragraph = [line]
                else:
                    # This is continuation text, add to current paragraph
                    if current_paragraph:
                        current_paragraph.append(line)
                    else:
                        # If no current paragraph, start a new one
                        current_paragraph = [line]
        
        # Add the last paragraph
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph).strip()
            if paragraph_text and not self._is_subject_header(paragraph_text):
                paragraphs.append(paragraph_text)
        
        return paragraphs
    
    def _clean_article_header(self, header: str) -> str:
        """Clean and standardize article header."""
        # Remove extra whitespace and normalize
        header = ' '.join(header.split())
        
        # Standardize format
        header = re.sub(r'(?i)(madde)\s+(\d+|[ivxlcdm]+)\s*[–\-:]\s*', r'Madde \2', header)
        header = re.sub(r'(?i)(madde)\s+(\d+|[ivxlcdm]+)\s*\.?\s*', r'Madde \2', header)
        header = re.sub(r'(?i)^(\d+)\s*\.\s*(madde)', r'Madde \1', header)
        
        return header.strip()
