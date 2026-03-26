import re

def is_empty(value):
    """Check if a value is empty (None, empty string, or string with only whitespace)."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False

def validate_email(email):
    """Check if an email address has a valid format."""
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(regex, email))

def validate_password_strength(password):
    """
    Check the strength of a password:
    - At least 8 characters
    - Contains uppercase, lowercase, digit, and special character.
    """
    if len(password) < 8:
        return False
    
    if re.search(r"\s", password):
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))
    
    return all([has_upper, has_lower, has_digit, has_special])

def is_numeric(value):
    """Check if a value is a number."""
    return str(value).isdigit()