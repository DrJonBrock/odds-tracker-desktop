import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from src.data_collection.odds_collector import OddsCollector
from src.analysis.arbitrage_detector import ArbitrageDetector
from src.database.models import ArbitrageOpportunities

@pytest.mark.integration
@pytest.mark.asyncio
async def test_arbitrage_detection_pipeline(test_database, mock_betfair_response, mock_oddsjet_data):
    mock_betfair_response["markets"][0]["runners"][0]["lastPriceTraded"] = 2.1
    mock_oddsjet_data[0]["selections"][1]["odds"] = 2.2
    
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            arbitrage_detector = ArbitrageDetector()
            
            await odds_collector.collect_all_odds()
            opportunities = await arbitrage_detector.analyze_markets()
            
            assert len(opportunities) > 0
            
            with Session(test_database) as session:
                stored_opportunities = session.query(ArbitrageOpportunities).all()
                assert len(stored_opportunities) > 0
                
                opportunity = stored_opportunities[0]
                assert opportunity.profit_percentage > 0
                assert opportunity.status == "ACTIVE"