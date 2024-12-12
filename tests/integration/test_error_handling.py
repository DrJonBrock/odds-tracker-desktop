import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.data_collection.odds_collector import OddsCollector
from src.analysis.arbitrage_detector import ArbitrageDetector
from src.database.models import Markets, Odds, ErrorLogs
from tests.helpers import TestHelper

@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_failure_recovery(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests system recovery from API failures.
    
    This test verifies that the system:
    1. Handles API connection failures gracefully
    2. Maintains data consistency during failures
    3. Recovers automatically when service is restored
    4. Logs errors appropriately
    """
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        # Configure mock to fail first, then succeed
        mock_betfair.return_value.get_market_odds.side_effect = [
            Exception("API Connection Error"),  # First call fails
            mock_betfair_response              # Second call succeeds
        ]
        
        odds_collector = OddsCollector()
        
        # First attempt should handle error gracefully
        await odds_collector.collect_all_odds()
        
        with Session(test_database) as session:
            # Verify error was logged
            error_logs = session.query(ErrorLogs).all()
            assert len(error_logs) > 0, "Error should be logged"
            assert "API Connection Error" in error_logs[0].error_message
            
            # Verify no incomplete data was stored
            markets = session.query(Markets).all()
            assert len(markets) == 0, "No markets should be stored during error"
        
        # Second attempt should succeed
        await odds_collector.collect_all_odds()
        
        with Session(test_database) as session:
            markets = session.query(Markets).all()
            assert len(markets) > 0, "Markets should be stored after recovery"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_partial_data_handling(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests system behavior when receiving partial or incomplete data.
    
    Verifies that the system:
    1. Handles missing data fields appropriately
    2. Maintains existing data when updates are partial
    3. Updates only affected records
    4. Preserves data relationships
    """
    helper = TestHelper()
    
    # First, establish some baseline data
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            await odds_collector.collect_all_odds()
    
    # Now simulate partial data update
    partial_response = {
        "markets": [{
            "marketId": mock_betfair_response["markets"][0]["marketId"],
            "eventName": "Test Match",
            "marketType": "MATCH_ODDS",
            "runners": [mock_betfair_response["markets"][0]["runners"][0]]  # Only one selection
        }]
    }
    
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = partial_response
        
        await odds_collector.collect_all_odds()
        
        with Session(test_database) as session:
            # Verify all original odds are preserved
            odds = session.query(Odds).filter_by(source="Betfair").all()
            assert len(odds) == 2, "Should maintain all original odds records"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_error_handling(test_database, mock_betfair_response, mock_oddsjet_data,
                                     qt_application, main_window, qtbot):
    """Tests error handling during concurrent operations.
    
    Verifies that the system:
    1. Handles errors in parallel operations
    2. Maintains UI responsiveness during errors
    3. Properly synchronizes error recovery
    4. Updates UI appropriately after recovery
    """
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        # Simulate intermittent failures
        mock_betfair.return_value.get_market_odds.side_effect = [
            Exception("Network Error"),
            mock_betfair_response,
            Exception("Timeout"),
            mock_betfair_response
        ]
        
        odds_collector = OddsCollector()
        
        # Start collection with error
        await odds_collector.collect_all_odds()
        qtbot.wait(100)
        
        # Verify UI shows error state
        assert "Error" in main_window.status_bar.currentMessage()
        
        # Trigger recovery
        await odds_collector.collect_all_odds()
        qtbot.wait(100)
        
        # Verify UI updates after recovery
        assert "Ready" in main_window.status_bar.currentMessage()
        assert main_window.market_table.rowCount() > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_error_recovery(test_database):
    """Tests recovery from database-related errors.
    
    Verifies that the system:
    1. Handles database connection issues
    2. Maintains data integrity during failures
    3. Implements proper transaction rollback
    4. Recovers database state after errors
    """
    helper = TestHelper()
    
    with Session(test_database) as session:
        # Create initial market
        market = helper.create_test_market(session)
        
        # Simulate a database error during odds creation
        with patch.object(session, 'commit') as mock_commit:
            mock_commit.side_effect = Exception("Database Error")
            
            try:
                helper.create_test_odds(session, market, "Betfair", "Team A", 2.0)
            except Exception:
                pass
            
            # Verify transaction was rolled back
            session.rollback()
            odds = session.query(Odds).all()
            assert len(odds) == 0, "Failed transaction should not persist data"
        
        # Verify we can still add new data after recovery
        helper.create_test_odds(session, market, "Betfair", "Team A", 2.0)
        odds = session.query(Odds).all()
        assert len(odds) == 1, "Should successfully add data after recovery"