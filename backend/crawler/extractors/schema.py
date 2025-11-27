"""
Schema.org structured data extractor
"""
import json
from typing import List, Dict
from bs4 import BeautifulSoup
from loguru import logger


class SchemaExtractor:
    """Extracts and validates structured data"""
    
    REQUIRED_FIELDS = {
        'Article': ['headline', 'author', 'datePublished'],
        'BlogPosting': ['headline', 'author', 'datePublished'],
        'Person': ['name'],
        'Organization': ['name'],
        'FAQPage': ['mainEntity'],
        'HowTo': ['name', 'step'],
        'Product': ['name', 'offers']
    }
    
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
    
    def extract_jsonld(self) -> List[Dict]:
        """Extract all JSON-LD blocks"""
        jsonld_blocks = []
        
        for script in self.soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                
                # Handle @graph arrays
                if isinstance(data, dict) and '@graph' in data:
                    jsonld_blocks.extend(data['@graph'])
                elif isinstance(data, list):
                    jsonld_blocks.extend(data)
                else:
                    jsonld_blocks.append(data)
                    
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to parse JSON-LD: {e}")
                jsonld_blocks.append({
                    'error': 'Invalid JSON',
                    'raw': str(script.string)[:200] if script.string else ''
                })
        
        logger.debug(f"Extracted {len(jsonld_blocks)} JSON-LD blocks")
        return jsonld_blocks
    
    def detect_schema_types(self, jsonld_blocks: List[Dict]) -> List[str]:
        """Get list of schema types present"""
        schema_types = []
        
        for block in jsonld_blocks:
            if 'error' not in block:
                schema_type = block.get('@type', 'Unknown')
                if schema_type not in schema_types:
                    schema_types.append(schema_type)
        
        return schema_types
    
    def extract_faq_schema(self, jsonld_blocks: List[Dict]) -> Dict:
        """Extract FAQ schema details"""
        for block in jsonld_blocks:
            if block.get('@type') == 'FAQPage':
                qa_pairs = []
                
                for entity in block.get('mainEntity', []):
                    question = entity.get('name', '')
                    accepted_answer = entity.get('acceptedAnswer', {})
                    
                    if isinstance(accepted_answer, dict):
                        answer = accepted_answer.get('text', '')
                    else:
                        answer = ''
                    
                    qa_pairs.append({
                        'question': question,
                        'answer': answer[:200],  # Limit length
                        'valid': bool(question and answer)
                    })
                
                return {
                    'found': True,
                    'qa_pairs': qa_pairs,
                    'valid_pairs': sum(1 for qa in qa_pairs if qa['valid'])
                }
        
        return {'found': False, 'qa_pairs': [], 'valid_pairs': 0}
    
    def validate_schema(self, schema_block: Dict) -> Dict:
        """Validate a schema block"""
        schema_type = schema_block.get('@type')
        
        if not schema_type or 'error' in schema_block:
            return {
                'valid': False,
                'reason': 'Missing @type or parse error',
                'schema_type': schema_type
            }
        
        required = self.REQUIRED_FIELDS.get(schema_type, [])
        present = [field for field in required if field in schema_block]
        missing = [field for field in required if field not in schema_block]
        
        return {
            'valid': len(missing) == 0,
            'schema_type': schema_type,
            'required_fields': required,
            'present_fields': present,
            'missing_fields': missing,
            'completeness': len(present) / len(required) if required else 1.0
        }
    
    def validate_all_schemas(self, jsonld_blocks: List[Dict]) -> List[Dict]:
        """Validate all schema blocks"""
        validations = []
        
        for block in jsonld_blocks:
            if 'error' not in block:
                validation = self.validate_schema(block)
                validations.append(validation)
        
        return validations

