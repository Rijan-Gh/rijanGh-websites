import re
from typing import Optional, List
from datetime import datetime, date
import phonenumbers
from email_validator import validate_email, EmailNotValidError

class Validators:
    
    @staticmethod
    def validate_phone(phone: str, country: str = "IN") -> Optional[str]:
        """Validate and format phone number"""
        try:
            parsed = phonenumbers.parse(phone, country)
            if not phonenumbers.is_valid_number(parsed):
                return None
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except:
            return None
    
    @staticmethod
    def validate_email(email: str) -> Optional[str]:
        """Validate email address"""
        try:
            validated = validate_email(email, check_deliverability=False)
            return validated.email
        except EmailNotValidError:
            return None
    
    @staticmethod
    def validate_pincode(pincode: str, country: str = "IN") -> bool:
        """Validate postal/pin code"""
        if country == "IN":
            # Indian pincode validation (6 digits)
            return bool(re.match(r'^[1-9][0-9]{5}$', pincode))
        return True  # For other countries, basic validation
    
    @staticmethod
    def validate_password(password: str) -> List[str]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r"[0-9]", password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        return errors
    
    @staticmethod
    def validate_latitude(lat: float) -> bool:
        """Validate latitude value"""
        return -90 <= lat <= 90
    
    @staticmethod
    def validate_longitude(lng: float) -> bool:
        """Validate longitude value"""
        return -180 <= lng <= 180
    
    @staticmethod
    def validate_date_string(date_str: str, format: str = "%Y-%m-%d") -> bool:
        """Validate date string format"""
        try:
            datetime.strptime(date_str, format)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_time_string(time_str: str) -> bool:
        """Validate time string format (HH:MM)"""
        return bool(re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', time_str))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL"""
        pattern = re.compile(
            r'^(https?://)?'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(pattern.match(url))
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # Basic HTML escaping (for safety)
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        return text