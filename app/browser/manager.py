"""Browser automation manager"""

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Optional
from datetime import datetime
import os


class BrowserManager:
    """Manages Playwright browser instances"""
    
    def __init__(
        self,
        headless: bool = False,
        timeout: int = 30000,
        screenshots_dir: str = "screenshots"
    ):
        self.headless = headless
        self.timeout = timeout
        self.screenshots_dir = screenshots_dir
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # Create screenshots directory if needed
        os.makedirs(screenshots_dir, exist_ok=True)
    
    async def launch(self):
        """
        Launch browser
        """
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless
            )
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.timeout)
            
            return True
        except Exception as e:
            print(f"Error launching browser: {e}")
            return False
    
    async def navigate(self, url: str) -> bool:
        """
        Navigate to a URL
        
        Args:
            url: URL to navigate to
        
        Returns:
            True if navigation was successful
        """
        if not self.page:
            print("Browser not launched")
            return False
        
        try:
            response = await self.page.goto(url, wait_until="networkidle")
            return response.status < 400
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            await self.screenshot(f"error_navigation")
            return False
    
    async def screenshot(
        self,
        name: str = "screenshot"
    ) -> Optional[str]:
        """
        Take a screenshot
        
        Args:
            name: Screenshot name (without extension)
        
        Returns:
            Path to screenshot file
        """
        if not self.page:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            await self.page.screenshot(path=filepath)
            return filepath
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None
    
    async def save_html(
        self,
        name: str = "page"
    ) -> Optional[str]:
        """
        Save page HTML for debugging
        
        Args:
            name: File name (without extension)
        
        Returns:
            Path to HTML file
        """
        if not self.page:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.html"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            content = await self.page.content()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return filepath
        except Exception as e:
            print(f"Error saving HTML: {e}")
            return None
    
    async def close(self):
        """
        Close browser
        """
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Error closing browser: {e}")
