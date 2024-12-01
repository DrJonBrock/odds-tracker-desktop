import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from src.data_collection.odds_collector import OddsCollector
from src.database.models import ErrorLogs, Markets
from tests.helpers import TestHelper

@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_failure_recovery(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests system recovery from API failures
    
    This test verifies that the system:
    1. Handles API failures gracefully
    2. Logs errors appropriately
    3. Continues operation after recovery
    4. Maintains data consistency
    """
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        # Configure mock to fail first, then succeed
        mock_betfair.return_value.get_market_odds.side_effect = [
            Exception("API Connection Error"),  # First call fails
            mock_betfair_response              # Second call succeeds
        ]
        
        odds_collector = OddsCollector()
        
        # First attempt - should handle error gracefully
        await odds_collector.collect_all_odds()
        
        with Session(test_database) as session:
            # Verify error was logged
            error_logs = session.query(ErrorLogs).all()
            assert len(error_logs) > 0, "Error should be logged"
            assert "API Connection Error" in error_logs[0].error_message
            
            # Verify no incomplete data was stored
            markets = session.query(Markets).all()
            assert len(markets) == 0, "No markets should be stored during error"
        
        # Second attempt - should succeed
        await odds_collector.collect_all_odds()
        
        with Session(test_database) as session:
            markets = session.query(Markets).all()
            assert len(markets) > 0, "Markets should be stored after recovery"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_data_consistency_during_errors(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests data consistency during partial failures
    
    This test ensures:
    1. Partial data collection failures don't corrupt the database
    2. Transaction rollback works correctly
    3. Previous valid data remains accessible
    4. System state remains consistent
    """
    # First, populate database with initial valid data
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        odds_collector = OddsCollector()
        await odds_collector.collect_all_odds()
        
        # Now simulate a partial failure
        mock_betfair.return_value.get_market_odds.side_effect = Exception("Partial Update Failed")
        
        # Attempt update - should maintain previous valid data
        await odds_collector.collect_all_odds()
        
        with Session(test_database) as session:
            markets = session.query(Markets).all()
            assert len(markets) > 0, "Previous valid data should be preserved"
            
            # Verify data consistency
            market = markets[0]
            assert market.event_name == "Test Match"
            assert market.status == "ACTIVE"
            
            # Verify error logging
            error_logs = session.query(ErrorLogs).all()
            latest_error = error_logs[-1]
            assert "Partial Update Failed" in latest_error.error_message