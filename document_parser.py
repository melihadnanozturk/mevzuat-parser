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
        
        # Pattern for paragraph markers
        self.paragraph_pattern = r'^\s*\((\d+)\)\s*'
        
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
        """Extract paragraphs from article content."""
        paragraphs = []
        
        # Split by double newlines first to get potential paragraphs
        sections = re.split(r'\n\s*\n', article_content)
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if this section has numbered paragraphs
            lines = section.split('\n')
            current_paragraph = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line starts with paragraph marker like "(1)", "(2)", etc.
                paragraph_match = re.match(self.paragraph_pattern, line)
                
                if paragraph_match:
                    # Save previous paragraph if exists
                    if current_paragraph:
                        paragraphs.append(' '.join(current_paragraph).strip())
                        current_paragraph = []
                    
                    # Start new paragraph (remove the number marker)
                    line = re.sub(self.paragraph_pattern, '', line).strip()
                    if line:
                        current_paragraph = [line]
                else:
                    # Continue current paragraph
                    current_paragraph.append(line)
            
            # Add the last paragraph
            if current_paragraph:
                paragraphs.append(' '.join(current_paragraph).strip())
        
        # If no numbered paragraphs found, treat the whole content as one paragraph
        if not paragraphs and article_content.strip():
            # Remove any remaining newlines and clean up
            clean_content = ' '.join(article_content.split())
            if clean_content:
                paragraphs.append(clean_content)
        
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
