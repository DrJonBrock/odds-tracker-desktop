import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from src.data_collection.odds_collector import OddsCollector
from tests.helpers import TestHelper

@pytest.mark.integration
@pytest.mark.asyncio
async def test_odds_collection_to_database(test_database, mock_betfair_response, mock_oddsjet_data):
    """Verifies that odds collection properly stores data in the database
    
    This test ensures that:
    1. Data is collected from multiple sources successfully
    2. The data is properly normalized and stored
    3. All expected database entries are created
    4. The stored data matches the source data
    """
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            await odds_collector.collect_all_odds()
            
            with Session(test_database) as session:
                markets = session.query(Markets).all()
                odds = session.query(Odds).all()
                
                assert len(markets) == 1, "Expected one market to be created"
                assert len(odds) == 4, "Expected four odds entries (2 selections × 2 sources)"
                
                market = markets[0]
                assert market.event_name == "Test Match"
                assert market.market_type == "MATCH_ODDS"
                
                # Verify odds data from each source
                betfair_odds = [o for o in odds if o.source == "Betfair"]
                oddsjet_odds = [o for o in odds if o.source == "OddsJet"]
                
                assert len(betfair_odds) == 2, "Expected two odds entries from Betfair"
                assert len(oddsjet_odds) == 2, "Expected two odds entries from OddsJet"
                
                # Verify specific odds values
                helper = TestHelper()
                for odds_entry in betfair_odds:
                    if odds_entry.selection == "Team A":
                        assert abs(odds_entry.odds_value - 2.0) < 0.01
                    elif odds_entry.selection == "Team B":
                        assert abs(odds_entry.odds_value - 1.8) < 0.01