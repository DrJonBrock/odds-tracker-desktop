import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from src.data_collection.odds_collector import OddsCollector
from src.analysis.arbitrage_detector import ArbitrageDetector
from src.database.models import ArbitrageOpportunities, Markets
from tests.helpers import TestHelper

@pytest.mark.integration
@pytest.mark.asyncio
async def test_arbitrage_opportunity_detection(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests the complete arbitrage detection pipeline.
    
    This test verifies that:
    1. Arbitrage opportunities are correctly identified
    2. Profit calculations are accurate
    3. Opportunities are properly stored in the database
    4. Market relationships are maintained
    """
    # Modify mock data to create a clear arbitrage opportunity
    mock_betfair_response["markets"][0]["runners"][0]["lastPriceTraded"] = 2.1  # Team A at 2.1
    mock_oddsjet_data[0]["selections"][1]["odds"] = 2.2                      # Team B at 2.2
    
    helper = TestHelper()
    
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            # Run complete pipeline
            odds_collector = OddsCollector()
            arbitrage_detector = ArbitrageDetector()
            
            await odds_collector.collect_all_odds()
            opportunities = await arbitrage_detector.analyze_markets()
            
            assert len(opportunities) > 0, "Should detect arbitrage opportunity"
            
            with Session(test_database) as session:
                stored_opps = session.query(ArbitrageOpportunities).all()
                assert len(stored_opps) > 0, "Should store arbitrage opportunity"
                
                opp = stored_opps[0]
                # Calculate expected profit: (1/2.1 + 1/2.2 - 1) * 100
                expected_profit = ((1/2.1 + 1/2.2) - 1) * -100
                
                assert helper.verify_arbitrage_opportunity(
                    opp,
                    expected_profit,
                    opp.market_id
                )

@pytest.mark.integration
@pytest.mark.asyncio
async def test_arbitrage_threshold_filtering(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests that arbitrage opportunities are filtered based on profit thresholds.
    
    Verifies:
    1. Only opportunities above threshold are detected
    2. Threshold calculations are accurate
    3. Edge cases are handled properly
    """
    # Create a borderline opportunity (just above 1% profit)
    mock_betfair_response["markets"][0]["runners"][0]["lastPriceTraded"] = 2.05
    mock_oddsjet_data[0]["selections"][1]["odds"] = 2.07
    
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            arbitrage_detector = ArbitrageDetector(min_profit=1.0)  # 1% threshold
            
            await odds_collector.collect_all_odds()
            opportunities = await arbitrage_detector.analyze_markets()
            
            # Calculate actual profit
            profit = ((1/2.05 + 1/2.07) - 1) * -100
            
            if profit > 1.0:
                assert len(opportunities) > 0, "Should detect opportunity above threshold"
            else:
                assert len(opportunities) == 0, "Should not detect opportunity below threshold"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_status_handling(test_database, mock_betfair_response, mock_oddsjet_data):
    """Tests arbitrage detection with different market statuses.
    
    Verifies:
    1. Only active markets are considered
    2. Suspended markets are handled correctly
    3. Completed markets are properly excluded
    """
    helper = TestHelper()
    
    with Session(test_database) as session:
        # Create test markets with different statuses
        active_market = helper.create_test_market(session, "Active Match")
        suspended_market = helper.create_test_market(session, "Suspended Match")
        suspended_market.status = "SUSPENDED"
        completed_market = helper.create_test_market(session, "Completed Match")
        completed_market.status = "COMPLETED"
        session.commit()
        
        # Create favorable odds for arbitrage
        helper.create_test_odds(session, active_market, "Betfair", "Team A", 2.1)
        helper.create_test_odds(session, active_market, "OddsJet", "Team B", 2.2)
        
        helper.create_test_odds(session, suspended_market, "Betfair", "Team A", 2.1)
        helper.create_test_odds(session, suspended_market, "OddsJet", "Team B", 2.2)
        
        helper.create_test_odds(session, completed_market, "Betfair", "Team A", 2.1)
        helper.create_test_odds(session, completed_market, "OddsJet", "Team B", 2.2)
    
    arbitrage_detector = ArbitrageDetector()
    opportunities = await arbitrage_detector.analyze_markets()
    
    # Verify only active market opportunities are detected
    assert len(opportunities) == 1, "Should only detect opportunity in active market"
    assert opportunities[0].market_id == active_market.id