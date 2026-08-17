"""Form field detection logic"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FormField:
    """Represents a detected form field"""
    selector: str
    field_type: str
    value: Optional[str] = None
    score: float = 0.0
    name: Optional[str] = None
    id: Optional[str] = None
    placeholder: Optional[str] = None
    label: Optional[str] = None


class FieldDetector:
    """Detects form fields and matches them to user data"""
    
    # Field type definitions with scoring weights
    FIELD_PATTERNS = {
        "first_name": {
            "keywords": ["first", "fname", "firstname", "given"],
            "types": ["text"],
        },
        "last_name": {
            "keywords": ["last", "lname", "lastname", "surname", "family"],
            "types": ["text"],
        },
        "full_name": {
            "keywords": ["name", "fullname", "full_name", "username", "display"],
            "types": ["text"],
        },
        "email": {
            "keywords": ["email", "mail", "e-mail"],
            "types": ["email", "text"],
            "autocomplete": ["email"],
        },
        "username": {
            "keywords": ["username", "user", "login", "handle"],
            "types": ["text"],
        },
        "password": {
            "keywords": ["password", "passwd", "pass"],
            "types": ["password"],
            "autocomplete": ["password", "new-password"],
        },
        "confirm_password": {
            "keywords": ["confirm", "repeat", "verify", "retype"],
            "types": ["password"],
        },
        "phone": {
            "keywords": ["phone", "mobile", "telephone", "tel"],
            "types": ["tel", "text"],
        },
        "date_of_birth": {
            "keywords": ["birth", "dob", "birthdate", "age", "born"],
            "types": ["date", "text"],
        },
    }
    
    def __init__(self):
        self.detected_fields = []
    
    def detect_fields(self, page_html: str) -> List[FormField]:
        """Detect form fields from HTML"""
        # This will be called with Playwright's page object in actual implementation
        pass
    
    def score_field_match(
        self, 
        field_element: Dict,
        field_type: str
    ) -> float:
        """Score how well a field matches a field type"""
        score = 0.0
        
        # Get field attributes
        name = field_element.get("name", "").lower()
        id_attr = field_element.get("id", "").lower()
        type_attr = field_element.get("type", "").lower()
        placeholder = field_element.get("placeholder", "").lower()
        label = field_element.get("label", "").lower()
        autocomplete = field_element.get("autocomplete", "").lower()
        aria_label = field_element.get("aria-label", "").lower()
        
        patterns = self.FIELD_PATTERNS.get(field_type, {})
        keywords = patterns.get("keywords", [])
        allowed_types = patterns.get("types", [])
        allowed_autocomplete = patterns.get("autocomplete", [])
        
        # Type matching (high weight)
        if type_attr in allowed_types:
            score += 30
        
        # Autocomplete matching (high weight)
        if autocomplete in allowed_autocomplete:
            score += 25
        
        # Name attribute matching (medium-high weight)
        for keyword in keywords:
            if keyword in name:
                score += 15
                break
        
        # ID attribute matching (medium weight)
        for keyword in keywords:
            if keyword in id_attr:
                score += 10
                break
        
        # Placeholder text matching (medium weight)
        for keyword in keywords:
            if keyword in placeholder:
                score += 8
                break
        
        # Label text matching (medium weight)
        for keyword in keywords:
            if keyword in label:
                score += 8
                break
        
        # Aria-label matching (low-medium weight)
        for keyword in keywords:
            if keyword in aria_label:
                score += 5
                break
        
        return score
    
    def find_best_field(
        self,
        fields: List[FormField],
        field_type: str
    ) -> Optional[FormField]:
        """Find the best matching field for a type"""
        best_field = None
        best_score = 0
        
        for field in fields:
            score = self.score_field_match({
                "name": field.name or "",
                "id": field.id or "",
                "type": field.field_type,
                "placeholder": field.placeholder or "",
                "label": field.label or "",
            }, field_type)
            
            if score > best_score:
                best_score = score
                best_field = field
                best_field.score = best_score
        
        return best_field if best_score > 0 else None
