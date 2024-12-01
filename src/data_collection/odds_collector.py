import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from .betfair_client import BetfairClient
from .scrapers.oddsjet_scraper import OddsjetScraper
from .scrapers.oddscomau_scraper import OddsComAuScraper

class OddsCollector:
    """
    The OddsCollector serves as the central orchestrator for gathering odds data from multiple sources.
    It manages the scheduling, synchronization, and error handling for all data collection operations.
    
    Key responsibilities:
    1. Coordinating multiple data sources
    2. Ensuring data freshness
    3. Handling source-specific errors
    4. Managing rate limiting
    5. Data normalization and validation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__name__)
        
        # Initialize data sources
        self.betfair = None
        self.oddsjet = None
        self.oddscomau = None
        
        # Track last update times
        self.last_updates = defaultdict(lambda: datetime.min)
        
        # Store collected odds
        self.current_odds = defaultdict(dict)
        
        # Configure update intervals (in seconds)
        self.update_intervals = {
            'betfair': 5,      # Betfair API allows frequent updates
            'oddsjet': 30,     # Web scraping needs more spacing
            'oddscomau': 30    # Web scraping needs more spacing
        }
        
        # Track active collection tasks
        self.collection_tasks = {}
        
        # Store callbacks for odds updates
        self.update_callbacks = []
    
    def register_update_callback(self, callback):
        """Register a callback to be notified of odds updates."""
        self.update_callbacks.append(callback)
    
    async def initialize(self):
        """Initialize all data sources and establish connections."""
        try:
            # Initialize Betfair client if credentials are provided
            if all(k in self.config for k in ['betfair_api_key', 'betfair_username', 'betfair_password']):
                self.betfair = BetfairClient(
                    api_key=self.config['betfair_api_key'],
                    username=self.config['betfair_username'],
                    password=self.config['betfair_password']
                )
                await self.betfair.login()
            
            # Initialize web scrapers
            self.oddsjet = OddsjetScraper(self.config.get('oddsjet_config', {}))
            await self.oddsjet.initialize()
            
            self.oddscomau = OddsComAuScraper(self.config.get('oddscomau_config', {}))
            await self.oddscomau.initialize()
            
            # Start collection loops
            self.start_collection()
            
        except Exception as e:
            self.logger.error(f"Initialization error: {str(e)}")
            raise
    
    async def _collect_betfair_odds(self):
        """Collect odds from Betfair API."""
        try:
            # Get market catalogue for relevant events
            catalogue = await self.betfair.get_market_catalogue(
                event_type_ids=[1],  # Soccer markets
                market_projection=['EVENT', 'MARKET_START_TIME', 'RUNNER_DESCRIPTION']
            )
            
            # Get market IDs for active markets
            market_ids = [market['marketId'] for market in catalogue]
            
            # Get current odds for these markets
            if market_ids:
                market_books = await self.betfair.get_market_book(market_ids)
                
                # Process and store the odds
                for book in market_books:
                    market_id = book['marketId']
                    runners = book.get('runners', [])
                    
                    odds_data = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'betfair',
                        'market_id': market_id,
                        'event_name': next((m['event']['name'] for m in catalogue if m['marketId'] == market_id), ''),
                        'odds': []
                    }
                    
                    # Extract best available odds for each runner
                    for runner in runners:
                        if runner.get('ex', {}).get('availableToBack'):
                            best_odds = runner['ex']['availableToBack'][0]['price']
                            odds_data['odds'].append({
                                'runner_id': runner['selectionId'],
                                'odds': best_odds
                            })
                    
                    # Store the processed odds
                    self.current_odds['betfair'][market_id] = odds_data
                    
                    # Notify callbacks of the update
                    for callback in self.update_callbacks:
                        await callback(odds_data)
                        
        except Exception as e:
            self.logger.error(f"Betfair odds collection error: {str(e)}")
    
    async def _collect_oddsjet_odds(self):
        """Collect odds from OddsJet."""
        try:
            # Get odds for soccer matches
            odds_data = await self.oddsjet.get_odds('soccer', 'match_odds')
            
            # Process and store the odds
            for market in odds_data:
                market_id = f"oddsjet_{market['event_name']}"
                
                self.current_odds['oddsjet'][market_id] = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'oddsjet',
                    'market_id': market_id,
                    'event_name': market['event_name'],
                    'odds': market['odds']
                }
                
                # Notify callbacks
                for callback in self.update_callbacks:
                    await callback(self.current_odds['oddsjet'][market_id])
                    
        except Exception as e:
            self.logger.error(f"OddsJet collection error: {str(e)}")
    
    async def _collect_oddscomau_odds(self):
        """Collect odds from Odds.com.au."""
        try:
            # Get odds for soccer matches
            odds_data = await self.oddscomau.get_odds('soccer', 'match_odds')
            
            # Process and store the odds
            for market in odds_data:
                market_id = f"oddscomau_{market['event_name']}"
                
                self.current_odds['oddscomau'][market_id] = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'oddscomau',
                    'market_id': market_id,
                    'event_name': market['event_name'],
                    'odds': market['odds']
                }
                
                # Notify callbacks
                for callback in self.update_callbacks:
                    await callback(self.current_odds['oddscomau'][market_id])
                    
        except Exception as e:
            self.logger.error(f"Odds.com.au collection error: {str(e)}")
    
    def get_current_odds(self, source: Optional[str] = None) -> Dict:
        """Get the current odds, optionally filtered by source."""
        if source:
            return self.current_odds.get(source, {})
        return self.current_odds
    
    async def cleanup(self):
        """Clean up resources and stop collection tasks."""
        # Cancel all collection tasks
        for task in self.collection_tasks.values():
            task.cancel()
        
        # Clean up data sources
        if self.betfair:
            await self.betfair.cleanup()
        
        if self.oddsjet:
            await self.oddsjet.cleanup()
        
        if self.oddscomau:
            await self.oddscomau.cleanup()