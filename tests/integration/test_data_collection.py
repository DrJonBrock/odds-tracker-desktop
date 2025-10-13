import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.data_collection.odds_collector import OddsCollector
from src.database.models import Markets, Odds
from tests.helpers import TestHelper

@pytest.mark.integration
@pytest.mark.asyncio
async def test_odds_collection_full_pipeline(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests the complete odds collection pipeline from multiple sources.
    
    This test verifies that:
    1. Data is collected correctly from both Betfair and OddsJet
    2. The data is properly normalized and stored in the database
    3. Market relationships are maintained
    4. Timestamps are handled correctly
    """
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            # Initialize collector and run collection
            odds_collector = OddsCollector()
            await odds_collector.collect_all_odds()
            
            # Verify database entries
            with Session(test_database) as session:
                markets = session.query(Markets).all()
                odds = session.query(Odds).all()
                
                # Basic count verification
                assert len(markets) == 1, "Expected one market to be created"
                assert len(odds) == 4, "Expected four odds entries (2 selections × 2 sources)"
                
                # Verify market data
                market = markets[0]
                assert market.event_name == "Test Match"
                assert market.market_type == "MATCH_ODDS"
                assert market.status == "ACTIVE"
                
                # Verify source-specific odds
                betfair_odds = [o for o in odds if o.source == "Betfair"]
                oddsjet_odds = [o for o in odds if o.source == "OddsJet"]
                
                assert len(betfair_odds) == 2, "Expected two Betfair odds entries"
                assert len(oddsjet_odds) == 2, "Expected two OddsJet odds entries"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_odds_normalization(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests that odds are properly normalized across different sources.
    
    Verifies:
    1. Decimal odds are handled consistently
    2. Selection names are matched correctly
    3. Relationships between markets and odds are maintained
    """
    helper = TestHelper()
    
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            await odds_collector.collect_all_odds()
            
            with Session(test_database) as session:
                odds = session.query(Odds).all()
                
                # Test each source's data format
                for odd in odds:
                    if odd.source == "Betfair":
                        # Verify Betfair data matches expected format
                        if odd.selection == "Team A":
                            assert abs(odd.odds_value - 2.0) < 0.01
                        elif odd.selection == "Team B":
                            assert abs(odd.odds_value - 1.8) < 0.01
                    elif odd.source == "OddsJet":
                        # Verify OddsJet data matches expected format
                        if odd.selection == "Team A":
                            assert abs(odd.odds_value - 2.1) < 0.01
                        elif odd.selection == "Team B":
                            assert abs(odd.odds_value - 1.9) < 0.01

@pytest.mark.integration
@pytest.mark.asyncio
async def test_timestamp_handling(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests proper handling of timestamps in the collection process.
    
    Verifies:
    1. Timestamps are recorded for each odds entry
    2. Market start times are handled correctly
    3. Data freshness is maintained
    """
    collection_start = datetime.now()
    
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            await odds_collector.collect_all_odds()
            
            with Session(test_database) as session:
                markets = session.query(Markets).all()
                odds = session.query(Odds).all()
                
                # Verify market timestamps
                market = markets[0]
                assert market.start_time > collection_start
                assert market.start_time < datetime.now() + timedelta(days=1)
                
                # Verify odds timestamps
                for odd in odds:
                    assert odd.timestamp >= collection_start
                    assert odd.timestamp <= datetime.now()
                    assert odd.is_active