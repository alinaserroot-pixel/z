"""Registration service - main business logic"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.registration import RegistrationRequest, RegistrationStatus
from app.database.db import RegistrationDatabase
from app.browser.manager import BrowserManager
from app.browser.detector import FieldDetector, FormField
from app.browser.filler import FormFiller
from app.browser.submitter import FormSubmitter, SubmissionResult
from app.config import settings


class RegistrationService:
    """Main service for handling registration automation"""
    
    def __init__(self):
        self.db = RegistrationDatabase()
        self.detector = FieldDetector()
    
    async def process_registration(
        self,
        request: RegistrationRequest
    ) -> str:
        """
        Process a registration request
        
        Args:
            request: Registration request with user data
        
        Returns:
            Registration ID
        """
        # Create registration record
        registration_id = self.db.create_registration(
            website_url=request.website_url,
            email=request.email,
            additional_data=request.additional_fields
        )
        
        # Update status to in progress
        self.db.update_registration(
            registration_id,
            RegistrationStatus.IN_PROGRESS,
            message="Starting browser automation"
        )
        
        # Start registration process in background
        asyncio.create_task(self._run_registration(
            registration_id,
            request
        ))
        
        return registration_id
    
    async def _run_registration(
        self,
        registration_id: str,
        request: RegistrationRequest
    ):
        """
        Internal method to run the registration process
        """
        browser_manager = BrowserManager(
            headless=not settings.browser_headless,
            timeout=settings.browser_timeout
        )
        
        try:
            # Launch browser
            if not await browser_manager.launch():
                self.db.update_registration(
                    registration_id,
                    RegistrationStatus.FAILED,
                    error_reason="Failed to launch browser"
                )
                return
            
            # Navigate to website
            self.db.update_registration(
                registration_id,
                RegistrationStatus.IN_PROGRESS,
                message="Opening website"
            )
            
            if not await browser_manager.navigate(request.website_url):
                await browser_manager.screenshot(f"error_{registration_id}")
                self.db.update_registration(
                    registration_id,
                    RegistrationStatus.FAILED,
                    error_reason="Failed to navigate to website"
                )
                return
            
            # Detect form
            self.db.update_registration(
                registration_id,
                RegistrationStatus.IN_PROGRESS,
                message="Detecting registration form"
            )
            
            # Find form element
            try:
                form = browser_manager.page.locator("form").first
                await form.wait_for(timeout=5000)
            except:
                await browser_manager.screenshot(f"error_form_{registration_id}")
                self.db.update_registration(
                    registration_id,
                    RegistrationStatus.FAILED,
                    error_reason="Could not find registration form"
                )
                return
            
            # Extract all form fields
            field_elements = await browser_manager.page.evaluate("""
                () => {
                    const form = document.querySelector('form');
                    if (!form) return [];
                    const inputs = form.querySelectorAll('input, textarea, select');
                    return Array.from(inputs).map(el => ({
                        name: el.name,
                        id: el.id,
                        type: el.type,
                        placeholder: el.placeholder,
                        label: el.labels ? el.labels[0]?.textContent : '',
                        autocomplete: el.autocomplete,
                        ariaLabel: el.getAttribute('aria-label') || '',
                    }));
                }
            """)
            
            if not field_elements:
                self.db.update_registration(
                    registration_id,
                    RegistrationStatus.FAILED,
                    error_reason="No form fields found"
                )
                return
            
            # Create FormField objects
            form_fields = [
                FormField(
                    selector=f"[name='{f['name']}']" if f['name'] else f"[id='{f['id']}']" if f['id'] else f"input[type='{f['type']}']",
                    field_type=f['type'],
                    name=f['name'],
                    id=f['id'],
                    placeholder=f['placeholder'],
                    label=f['label']
                )
                for f in field_elements
            ]
            
            # Fill form fields
            self.db.update_registration(
                registration_id,
                RegistrationStatus.IN_PROGRESS,
                message="Filling registration fields"
            )
            
            filler = FormFiller(browser_manager.page)
            
            # Map fields to data
            field_mapping = self._create_field_mapping(
                form_fields,
                request
            )
            
            # Fill fields
            if not await filler.fill_registration_data(request, field_mapping):
                self.db.update_registration(
                    registration_id,
                    RegistrationStatus.FAILED,
                    error_reason="Failed to fill all required fields"
                )
                return
            
            # Check for CAPTCHA
            self.db.update_registration(
                registration_id,
                RegistrationStatus.IN_PROGRESS,
                message="Checking for CAPTCHA"
            )
            
            submitter = FormSubmitter(browser_manager.page)
            if await submitter.detect_captcha():
                self.db.update_registration(
                    registration_id,
                    RegistrationStatus.WAITING_VERIFICATION,
                    message="Please complete the CAPTCHA in the browser window"
                )
                # Wait for user to complete CAPTCHA
                await asyncio.sleep(30)
            
            # Submit form
            self.db.update_registration(
                registration_id,
                RegistrationStatus.IN_PROGRESS,
                message="Submitting registration form"
            )
            
            if not await submitter.submit_form(dry_run=settings.dry_run):
                self.db.update_registration(
                    registration_id,
                    RegistrationStatus.FAILED,
                    error_reason="Failed to submit form"
                )
                return
            
            # Detect result
            result, message = await submitter.detect_success()
            
            status_map = {
                SubmissionResult.SUCCESS: RegistrationStatus.SUCCESS,
                SubmissionResult.EMAIL_VERIFICATION_REQUIRED: RegistrationStatus.WAITING_VERIFICATION,
                SubmissionResult.PHONE_VERIFICATION_REQUIRED: RegistrationStatus.WAITING_VERIFICATION,
                SubmissionResult.HUMAN_VERIFICATION_REQUIRED: RegistrationStatus.HUMAN_VERIFICATION_REQUIRED,
                SubmissionResult.FAILED: RegistrationStatus.FAILED,
                SubmissionResult.UNKNOWN: RegistrationStatus.UNKNOWN,
            }
            
            status = status_map.get(result, RegistrationStatus.UNKNOWN)
            
            self.db.update_registration(
                registration_id,
                status,
                message=message,
                completed_at=datetime.now()
            )
            
            # Take final screenshot
            await browser_manager.screenshot(f"result_{registration_id}")
            await browser_manager.save_html(f"result_{registration_id}")
        
        except Exception as e:
            self.db.update_registration(
                registration_id,
                RegistrationStatus.FAILED,
                error_reason=f"Unexpected error: {str(e)}",
                completed_at=datetime.now()
            )
        
        finally:
            await browser_manager.close()
    
    def _create_field_mapping(
        self,
        form_fields: list,
        request: RegistrationRequest
    ) -> Dict[str, str]:
        """
        Create a mapping of field types to selectors
        
        Returns:
            Dictionary mapping field names to CSS selectors
        """
        mapping = {}
        
        # Look for email field
        email_field = self.detector.find_best_field(form_fields, "email")
        if email_field:
            mapping["email"] = email_field.selector
        
        # Look for password field
        password_field = self.detector.find_best_field(form_fields, "password")
        if password_field:
            mapping["password"] = password_field.selector
        
        # Look for name field
        name_field = self.detector.find_best_field(form_fields, "full_name")
        if not name_field:
            name_field = self.detector.find_best_field(form_fields, "first_name")
        if name_field:
            mapping["full_name"] = name_field.selector
        
        return mapping
    
    def get_registration(self, registration_id: str):
        """
        Get registration status
        """
        return self.db.get_registration(registration_id)
    
    def get_history(self, limit: int = 50):
        """
        Get registration history
        """
        return self.db.get_history(limit)
