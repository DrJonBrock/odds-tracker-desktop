import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from src.data_collection.odds_collector import OddsCollector
from src.analysis.arbitrage_detector import ArbitrageDetector
from tests.helpers import TestHelper

@pytest.mark.integration
@pytest.mark.asyncio
async def test_arbitrage_detection_pipeline(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests the complete pipeline from odds collection through arbitrage detection
    
    This test verifies:
    1. Collection of odds data from multiple sources
    2. Processing of collected data for arbitrage opportunities
    3. Storage of detected opportunities
    4. Accuracy of profit calculations
    """
    # Modify mock data to create a clear arbitrage opportunity
    mock_betfair_response["markets"][0]["runners"][0]["lastPriceTraded"] = 2.1
    mock_oddsjet_data[0]["selections"][1]["odds"] = 2.2
    
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            arbitrage_detector = ArbitrageDetector()
            
            # Run the complete pipeline
            await odds_collector.collect_all_odds()
            opportunities = await arbitrage_detector.analyze_markets()
            
            assert len(opportunities) > 0, "Expected at least one arbitrage opportunity"
            
            with Session(test_database) as session:
                stored_opportunities = session.query(ArbitrageOpportunities).all()
                assert len(stored_opportunities) > 0
                
                opportunity = stored_opportunities[0]
                helper = TestHelper()
                
                # Calculate expected profit based on the odds
                expected_profit = ((1/2.1 + 1/2.2) - 1) * 100
                assert helper.verify_arbitrage_opportunity(
                    opportunity,
                    expected_profit,
                    opportunity.market_id
                )