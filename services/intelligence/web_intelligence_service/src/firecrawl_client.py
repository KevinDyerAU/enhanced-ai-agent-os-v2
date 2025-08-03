import logging
from typing import Dict, Any, Optional
from firecrawl import FirecrawlApp

class FirecrawlClient:
    def __init__(self, api_key: str):
        self.app = FirecrawlApp(api_key=api_key)
        self.logger = logging.getLogger(__name__)

    async def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        self.logger.info(f"Scraping URL: {url}")
        try:
            return self.app.scrape_url(url)
        except Exception as e:
            self.logger.error(f"Failed to scrape URL {url}: {e}")
            return None
