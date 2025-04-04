import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

def validate_email(email: str) -> bool:
    """Validate an email address format.
    
    Args:
        email: The email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate a phone number format.
    
    Args:
        phone: The phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Basic international phone number validation
    pattern = r'^\+?[0-9]{1,3}?[-.\s]?\(?[0-9]{1,3}\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}$'
    return bool(re.match(pattern, phone))

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
    """Validate that all required fields are present and not empty.
    
    Args:
        data: The data dictionary to validate
        required_fields: List of field names that must be present and non-empty
        
    Returns:
        Tuple of (is_valid, missing_fields)
    """
    missing = []
    
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing.append(field)
    
    return (len(missing) == 0, missing)

def validate_with_custom_validators(
    data: Dict[str, Any], 
    validators: Dict[str, Callable[[Any], bool]]
) -> Tuple[bool, Dict[str, str]]:
    """Validate data fields with custom validator functions.
    
    Args:
        data: The data dictionary to validate
        validators: Mapping of field names to validator functions
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = {}
    
    for field, validator in validators.items():
        if field in data and data[field] is not None:
            if not validator(data[field]):
                errors[field] = f"Invalid value for field '{field}'"
    
    return (len(errors) == 0, errors)
