"""Form filling logic"""

from typing import Optional, Dict, Any
from app.models.registration import RegistrationRequest


class FormFiller:
    """Handles filling form fields with user data"""
    
    def __init__(self, page):
        self.page = page
    
    async def fill_field(
        self,
        selector: str,
        value: str,
        field_type: str = "text"
    ) -> bool:
        """
        Fill a form field with a value
        
        Args:
            selector: CSS/XPath selector for the field
            value: Value to fill
            field_type: Type of field (text, email, password, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Wait for element to be visible
            await self.page.wait_for_selector(selector, timeout=5000)
            
            # Clear any existing value
            await self.page.fill(selector, "")
            
            # Fill the field
            await self.page.fill(selector, value)
            
            # Verify the value was set
            filled_value = await self.page.input_value(selector)
            return filled_value == value
        
        except Exception as e:
            print(f"Error filling field {selector}: {e}")
            return False
    
    async def fill_registration_data(
        self,
        request: RegistrationRequest,
        field_mapping: Dict[str, str]
    ) -> bool:
        """
        Fill all registration fields
        
        Args:
            request: Registration request with user data
            field_mapping: Mapping of field names to selectors
        
        Returns:
            True if all fields filled successfully
        """
        all_filled = True
        
        # Map of field names to values
        data_map = {
            "full_name": request.full_name,
            "email": request.email,
            "password": request.password,
        }
        
        # Add additional fields
        if request.additional_fields:
            data_map.update(request.additional_fields)
        
        # Fill each field
        for field_name, selector in field_mapping.items():
            if field_name in data_map:
                value = data_map[field_name]
                if not await self.fill_field(selector, value):
                    all_filled = False
        
        return all_filled
    
    async def check_checkbox(
        self,
        selector: str,
        should_check: bool = True
    ) -> bool:
        """
        Check or uncheck a checkbox
        
        Args:
            selector: CSS/XPath selector for the checkbox
            should_check: True to check, False to uncheck
        
        Returns:
            True if successful
        """
        try:
            await self.page.wait_for_selector(selector, timeout=5000)
            
            is_checked = await self.page.is_checked(selector)
            
            if should_check and not is_checked:
                await self.page.check(selector)
            elif not should_check and is_checked:
                await self.page.uncheck(selector)
            
            return True
        
        except Exception as e:
            print(f"Error checking checkbox {selector}: {e}")
            return False
    
    async def select_option(
        self,
        selector: str,
        value: str
    ) -> bool:
        """
        Select an option from a dropdown
        
        Args:
            selector: CSS/XPath selector for the select element
            value: Value to select
        
        Returns:
            True if successful
        """
        try:
            await self.page.wait_for_selector(selector, timeout=5000)
            await self.page.select_option(selector, value)
            return True
        
        except Exception as e:
            print(f"Error selecting option in {selector}: {e}")
            return False
