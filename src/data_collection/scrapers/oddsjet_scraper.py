from playwright.async_api import async_playwright
from .base_scraper import BaseScraper
import logging
from typing import Dict, List
import asyncio

class OddsjetScraper(BaseScraper):
    """
    Scraper implementation for www.oddsjet.com using Playwright.
    Handles dynamic content loading and data extraction.
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.browser = None
        self.context = None
        
    async def initialize(self):
        """Initialize Playwright browser and context."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox']
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.config.get('user_agent')
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {str(e)}")
            raise
            
    async def get_odds(self, sport: str, market_type: str) -> List[Dict]:
        """
        Scrape odds data from OddsJet.
        
        Args:
            sport: Sport category to scrape
            market_type: Type of market to retrieve
            
        Returns:
            List of dictionaries containing normalized odds data
        """
        results = []
        
        try:
            page = await self.context.new_page()
            
            # Configure request interception for optimization
            await page.route("**/*", lambda route: route.continue_())
            
            # Navigate to sport-specific page
            url = f"https://www.oddsjet.com/sports/{sport}/{market_type}"
            await page.goto(url, wait_until="networkidle")
            
            # Wait for odds data to load
            await page.wait_for_selector(".odds-container", timeout=30000)
            
            # Extract odds data
            odds_elements = await page.query_selector_all(".market-row")
            
            for element in odds_elements:
                market_data = await self._extract_market_data(element)
                if market_data:
                    results.append(market_data)
                    
            await page.close()
            return results
            
        except Exception as e:
            self.logger.error(f"Error scraping odds: {str(e)}")
            return []
            
    async def _extract_market_data(self, element) -> Optional[Dict]:
        """Extract structured data from a market element."""
        try:
            # Extract event details
            event_name = await element.query_selector_text(".event-name")
            start_time = await element.query_selector_text(".start-time")
            
            # Extract odds for different outcomes
            odds_data = []
            odds_elements = await element.query_selector_all(".outcome")
            
            for odds_elem in odds_elements:
                outcome_name = await odds_elem.query_selector_text(".outcome-name")
                odds_value = await odds_elem.query_selector_text(".odds-value")
                
                odds_data.append({
                    "outcome": outcome_name,
                    "odds": float(odds_value)
                })
                
            return {
                "event_name": event_name,
                "start_time": start_time,
                "odds": odds_data,
                "source": "oddsjet",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting market data: {str(e)}")
            return None
            
    async def cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()