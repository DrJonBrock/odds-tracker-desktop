import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from src.data_collection.odds_collector import OddsCollector
from src.database.models import ErrorLogs, Markets

@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_failure_recovery(test_database, mock_betfair_response, mock_oddsjet_data):
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.side_effect = [
            Exception("API Error"),
            mock_betfair_response
        ]
        
        odds_collector = OddsCollector()
        
        await odds_collector.collect_all_odds()
        
        with Session(test_database) as session:
            error_logs = session.query(ErrorLogs).all()
            assert len(error_logs) > 0
            assert "API Error" in error_logs[0].error_message
        
        await odds_collector.collect_all_odds()
        
        with Session(test_database) as session:
            markets = session.query(Markets).all()
            assert len(markets) > 0