import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from src.data_collection.odds_collector import OddsCollector
from src.database.models import Markets, Odds

@pytest.mark.integration
@pytest.mark.asyncio
async def test_odds_collection_to_database(test_database, mock_betfair_response, mock_oddsjet_data):
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            await odds_collector.collect_all_odds()
            
            with Session(test_database) as session:
                markets = session.query(Markets).all()
                odds = session.query(Odds).all()
                
                assert len(markets) == 1
                assert len(odds) == 4  # 2 selections × 2 sources
                
                market = markets[0]
                assert market.event_name == "Test Match"
                assert market.market_type == "MATCH_ODDS"