"""Form submission and result detection"""

from enum import Enum
from typing import Optional, Tuple
import asyncio


class SubmissionResult(str, Enum):
    """Possible submission results"""
    SUCCESS = "success"
    EMAIL_VERIFICATION_REQUIRED = "email_verification_required"
    PHONE_VERIFICATION_REQUIRED = "phone_verification_required"
    HUMAN_VERIFICATION_REQUIRED = "human_verification_required"
    FAILED = "failed"
    UNKNOWN = "unknown"


class FormSubmitter:
    """Handles form submission and result detection"""
    
    def __init__(self, page):
        self.page = page
    
    async def find_submit_button(self) -> Optional[str]:
        """
        Find the submit button selector
        
        Returns:
            Selector of the submit button, or None if not found
        """
        # Common submit button patterns
        selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Sign up")',
            'button:has-text("Register")',
            'button:has-text("Create account")',
            'button:has-text("Join")',
            'button:has-text("Submit")',
            'input[value*="Sign"]',
            'input[value*="Register"]',
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible():
                    return selector
            except:
                continue
        
        return None
    
    async def submit_form(
        self,
        button_selector: Optional[str] = None,
        dry_run: bool = False
    ) -> bool:
        """
        Submit the form
        
        Args:
            button_selector: Selector of the submit button
            dry_run: If True, don't actually submit
        
        Returns:
            True if submission was triggered
        """
        if dry_run:
            print("[DRY RUN] Would submit form now")
            return True
        
        try:
            if not button_selector:
                button_selector = await self.find_submit_button()
            
            if not button_selector:
                print("Could not find submit button")
                return False
            
            await self.page.wait_for_selector(button_selector, timeout=5000)
            await self.page.click(button_selector)
            return True
        
        except Exception as e:
            print(f"Error submitting form: {e}")
            return False
    
    async def detect_captcha(self) -> bool:
        """
        Detect if a CAPTCHA is present
        
        Returns:
            True if CAPTCHA detected
        """
        captcha_selectors = [
            '[class*="captcha"]',
            '[id*="captcha"]',
            '[data-captcha]',
            'iframe[src*="recaptcha"]',
            'iframe[src*="turnstile"]',
            'iframe[src*="cloudflare"]',
        ]
        
        for selector in captcha_selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible():
                    return True
            except:
                continue
        
        return False
    
    async def detect_success(
        self,
        wait_time: int = 5000
    ) -> Tuple[SubmissionResult, Optional[str]]:
        """
        Detect if registration was successful
        
        Args:
            wait_time: Time to wait for result (milliseconds)
        
        Returns:
            Tuple of (result, message)
        """
        try:
            # Wait a bit for page to process
            await asyncio.sleep(1)
            
            # Get current URL and page content
            current_url = self.page.url
            page_content = await self.page.content()
            
            # Check for success messages
            success_keywords = [
                "success",
                "registered",
                "welcome",
                "account created",
                "check your email",
                "verify your email",
                "confirmation",
            ]
            
            content_lower = page_content.lower()
            
            for keyword in success_keywords:
                if keyword in content_lower:
                    if "verify" in keyword or "email" in keyword:
                        return (
                            SubmissionResult.EMAIL_VERIFICATION_REQUIRED,
                            f"Registration requires email verification"
                        )
                    return (
                        SubmissionResult.SUCCESS,
                        f"Registration completed successfully"
                    )
            
            # Check for error messages
            error_keywords = [
                "error",
                "invalid",
                "already exists",
                "failed",
                "not found",
            ]
            
            for keyword in error_keywords:
                if keyword in content_lower:
                    return (
                        SubmissionResult.FAILED,
                        f"Registration failed: {keyword} detected"
                    )
            
            # Check for CAPTCHA
            if await self.detect_captcha():
                return (
                    SubmissionResult.HUMAN_VERIFICATION_REQUIRED,
                    "Please complete the CAPTCHA in the browser window"
                )
            
            return (
                SubmissionResult.UNKNOWN,
                "Could not determine registration result"
            )
        
        except Exception as e:
            return (
                SubmissionResult.FAILED,
                f"Error detecting result: {str(e)}"
            )
