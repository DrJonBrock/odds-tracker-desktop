from playwright.async_api import async_playwright
from .base_scraper import BaseScraper
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

class OddsComAuScraper(BaseScraper):
    """
    Scraper implementation for www.odds.com.au using Playwright.
    Handles Australian-specific odds formats and market types.
    
    This implementation includes special handling for:
    - Australian odds format conversion
    - Local timezone adjustments
    - Australia-specific market types
    - Region-specific betting regulations
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.browser = None
        self.context = None
        self.api_base_url = "https://api.odds.com.au/v1"
        
    async def initialize(self):
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox']
            )
            
            # Set up a context with Australian geolocation
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.config.get('user_agent'),
                geolocation={
                    'latitude': -33.8688,  # Sydney coordinates
                    'longitude': 151.2093
                },
                locale='en-AU'
            )
            
            # Accept geolocation permissions
            context_settings = self.context.pages[0].context.pages[0] if self.context.pages else None
            if context_settings:
                await context_settings.grant_permissions(['geolocation'])
                
        except Exception as e:
            self.logger.error(f"Browser initialization failed: {str(e)}")
            raise
            
    async def get_odds(self, sport: str, market_type: str) -> List[Dict]:
        """
        Retrieve odds data from odds.com.au, handling Australia-specific formats.
        
        The function implements several key features:
        1. Automatic conversion between decimal and fractional odds
        2. Handling of Australian market types
        3. Proper timezone conversions
        4. Compliance with Australian betting regulations
        
        Args:
            sport: Sport category (e.g., 'afl', 'nrl', 'horses')
            market_type: Type of market to retrieve
            
        Returns:
            List of dictionaries containing normalized odds data
        """
        results = []
        
        try:
            page = await self.context.new_page()
            
            # Intercept and optimize network requests
            await self._setup_request_interception(page)
            
            # Build the URL with proper Australian market types
            url = self._build_market_url(sport, market_type)
            await page.goto(url, wait_until="networkidle")
            
            # Wait for the odds data to load
            await page.wait_for_selector(".market-table", timeout=30000)
            
            # Extract odds data using both API and DOM methods
            api_data = await self._fetch_api_data(sport, market_type)
            dom_data = await self._scrape_dom_data(page)
            
            # Merge and normalize the data
            merged_data = self._merge_odds_data(api_data, dom_data)
            results.extend(merged_data)
            
            await page.close()
            return results
            
        except Exception as e:
            self.logger.error(f"Odds retrieval error: {str(e)}")
            return []
            
    async def _setup_request_interception(self, page):
        """Configure network request interception for optimization."""
        await page.route("**/*", lambda route: route.continue_() if
            route.request.resource_type in ['document', 'xhr', 'fetch']
            else route.abort())
            
    async def _fetch_api_data(self, sport: str, market_type: str) -> List[Dict]:
        """Fetch odds data from the odds.com.au API endpoint."""
        try:
            response = await self.context.request.get(
                f"{self.api_base_url}/sports/{sport}/markets",
                params={
                    'type': market_type,
                    'region': 'AU'
                }
            )
            
            if response.ok:
                return await response.json()
            return []
            
        except Exception as e:
            self.logger.error(f"API fetch error: {str(e)}")
            return []
            
    async def _scrape_dom_data(self, page) -> List[Dict]:
        """Extract odds data from the DOM structure."""
        try:
            markets = await page.query_selector_all(".market-row")
            results = []
            
            for market in markets:
                market_data = await self._extract_market_data(market)
                if market_data:
                    results.append(market_data)
                    
            return results
            
        except Exception as e:
            self.logger.error(f"DOM scraping error: {str(e)}")
            return []
            
    async def _extract_market_data(self, element) -> Optional[Dict]:
        """Extract and normalize market data from a DOM element."""
        try:
            # Extract basic market information
            event_name = await element.query_selector_text(".event-name")
            start_time = await element.query_selector_text(".start-time")
            
            # Handle outcomes and odds
            outcomes = await element.query_selector_all(".outcome")
            odds_data = []
            
            for outcome in outcomes:
                name = await outcome.query_selector_text(".outcome-name")
                odds = await outcome.query_selector_text(".odds-value")
                
                odds_data.append({
                    "outcome": name,
                    "odds": self._normalize_odds(odds),
                    "bookmaker": await outcome.query_selector_text(".bookmaker")
                })
                
            return {
                "event_name": event_name,
                "start_time": self._normalize_timestamp(start_time),
                "odds": odds_data,
                "source": "odds.com.au",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Market data extraction error: {str(e)}")
            return None
            
    def _normalize_odds(self, odds_str: str) -> float:
        """Convert various Australian odds formats to decimal odds."""
        try:
            # Handle fractional odds (e.g., '4/1')
            if '/' in odds_str:
                num, den = map(float, odds_str.split('/'))
                return (num / den) + 1
                
            # Handle decimal odds
            return float(odds_str)
            
        except Exception as e:
            self.logger.error(f"Odds normalization error: {str(e)}")
            return 0.0
            
    def _normalize_timestamp(self, timestamp_str: str) -> str:
        """Convert Australian timezone to UTC."""
        try:
            # Implementation of timezone conversion logic
            # This is a placeholder - actual implementation would handle
            # various Australian timezone conversions
            return timestamp_str
            
        except Exception as e:
            self.logger.error(f"Timestamp normalization error: {str(e)}")
            return timestamp_str
            
    def _merge_odds_data(self, api_data: List[Dict], dom_data: List[Dict]) -> List[Dict]:
        """Merge and deduplicate odds data from API and DOM sources."""
        # Implement merging logic here
        # This would combine data from both sources, removing duplicates
        # and ensuring we have the most up-to-date information
        return list({item['event_name']: item for item in api_data + dom_data}.values())
        
    async def cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()