"""
HTML content parser
"""
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from loguru import logger


class ContentParser:
    """Parses HTML content and extracts structured data"""
    
    def __init__(self, html: str):
        """
        Initialize parser
        
        Args:
            html: Raw HTML string
        """
        self.soup = BeautifulSoup(html, 'lxml')
        self.remove_noise()
    
    def remove_noise(self):
        """Remove non-content elements (less aggressive for compatibility)"""
        # Remove scripts and styles only - keep structural elements
        for element in self.soup.find_all(['script', 'style']):
            element.decompose()
        
        # Remove obvious navigation/footer only if they have identifying classes/ids
        for element in self.soup.find_all(['nav', 'footer']):
            element.decompose()
        
        logger.debug("Removed noise elements from HTML")
    
    def get_main_content(self) -> str:
        """
        Extract primary content text
        
        Returns:
            Clean text content
        """
        # Priority search for main content area
        # Try multiple strategies to find content
        main = (
            self.soup.find('main') or
            self.soup.find('article') or
            self.soup.find('div', {'id': 'content'}) or  # Wikipedia uses id="content"
            self.soup.find('div', {'id': 'mw-content-text'}) or  # Wikipedia main content
            self.soup.find('div', {'role': 'main'}) or
            self.soup.find('div', class_=lambda x: x and 'content' in str(x).lower()) or
            self.soup.find('body')
        )
        
        if main:
            # Extract text but remove navigation/sidebar elements
            for noise in main.find_all(['nav', 'aside', '.sidebar', '.navigation']):
                noise.decompose()
            
            text = main.get_text(separator=' ', strip=True)
            logger.debug(f"Extracted {len(text)} characters of main content")
            return text
        
        return ""
    
    def get_title(self) -> str:
        """Extract page title"""
        title_tag = self.soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        # Fallback to h1
        h1 = self.soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def extract_headings(self) -> List[Dict]:
        """
        Extract all headings with hierarchy
        
        Returns:
            List of heading dicts with level, text, id, classes
        """
        headings = []
        
        for level in range(1, 7):
            for tag in self.soup.find_all(f'h{level}'):
                headings.append({
                    'level': level,
                    'text': tag.get_text(strip=True),
                    'html': str(tag),
                    'id': tag.get('id', ''),
                    'classes': tag.get('class', [])
                })
        
        logger.debug(f"Extracted {len(headings)} headings")
        return headings
    
    def extract_paragraphs(self) -> List[Dict]:
        """Extract paragraph blocks"""
        paragraphs = []
        main_content = self.soup.find('main') or self.soup.find('article') or self.soup.find('body')
        
        if main_content:
            for p in main_content.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 20:  # Skip tiny paragraphs
                    paragraphs.append({
                        'text': text,
                        'word_count': len(text.split()),
                        'has_emphasis': bool(p.find(['strong', 'b', 'em', 'i']))
                    })
        
        logger.debug(f"Extracted {len(paragraphs)} paragraphs")
        return paragraphs
    
    def extract_lists(self) -> List[Dict]:
        """Extract lists (ul, ol)"""
        lists = []
        
        for list_tag in self.soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in list_tag.find_all('li', recursive=False)]
            if len(items) >= 2:
                lists.append({
                    'type': list_tag.name,
                    'items': items,
                    'item_count': len(items)
                })
        
        logger.debug(f"Extracted {len(lists)} lists")
        return lists
    
    def extract_tables(self) -> List[Dict]:
        """Extract data tables"""
        tables = []
        
        for table in self.soup.find_all('table'):
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            rows = []
            
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all('td')]
                if cells:
                    rows.append(cells)
            
            if rows:
                tables.append({
                    'headers': headers,
                    'rows': rows,
                    'row_count': len(rows),
                    'col_count': len(headers) if headers else len(rows[0])
                })
        
        logger.debug(f"Extracted {len(tables)} tables")
        return tables
    
    def extract_meta_tags(self) -> Dict:
        """Extract meta tags"""
        meta_data = {}
        
        # Standard meta tags
        for meta in self.soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                meta_data[name] = content
        
        # Canonical URL
        canonical = self.soup.find('link', rel='canonical')
        if canonical:
            meta_data['canonical'] = canonical.get('href')
        
        logger.debug(f"Extracted {len(meta_data)} meta tags")
        return meta_data
    
    def get_dom(self) -> BeautifulSoup:
        """Get BeautifulSoup object"""
        return self.soup


# Example usage
if __name__ == "__main__":
    sample_html = """
    <html>
    <head><title>Sample Page</title></head>
    <body>
        <h1>Main Title</h1>
        <p>This is a paragraph with <strong>bold text</strong>.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    </body>
    </html>
    """
    
    parser = ContentParser(sample_html)
    print("Title:", parser.get_title())
    print("Headings:", parser.extract_headings())
    print("Paragraphs:", parser.extract_paragraphs())
    print("Lists:", parser.extract_lists())

