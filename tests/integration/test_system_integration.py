import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from src.data_collection.odds_collector import OddsCollector
from src.analysis.arbitrage_detector import ArbitrageDetector
from src.database.database import init_database
from src.ui.main_window import MainWindow

# Shared fixtures and helper functions
@pytest.fixture
def mock_betfair_response():
    """Mock response from Betfair API for consistent testing"""
    return {
        "markets": [
            {
                "marketId": "1.234567",
                "eventName": "Test Match",
                "marketType": "MATCH_ODDS",
                "startTime": (datetime.now() + timedelta(hours=1)).isoformat(),
                "runners": [
                    {"selectionId": 1234, "runnerName": "Team A", "lastPriceTraded": 2.0},
                    {"selectionId": 5678, "runnerName": "Team B", "lastPriceTraded": 1.8}
                ]
            }
        ]
    }

@pytest.fixture
def mock_oddsjet_data():
    """Mock scraped data from OddsJet for testing"""
    return [
        {
            "event_name": "Test Match",
            "market_type": "MATCH_ODDS",
            "selections": [
                {"name": "Team A", "odds": 2.1},
                {"name": "Team B", "odds": 1.9}
            ]
        }
    ]

@pytest.fixture
async def test_database():
    """Initialize a test database with required tables"""
    database_url = "sqlite:///:memory:"
    engine = init_database(database_url)
    
    # Create all tables
    from src.database.models import Base
    Base.metadata.create_all(engine)
    
    return engine

# Integration Tests

@pytest.mark.asyncio
async def test_odds_collection_to_database(test_database, mock_betfair_response, mock_oddsjet_data):
    """
    Test that odds collection properly stores data in the database
    Verifies the data pipeline from collection to storage
    """
    # Set up mocked components
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            # Initialize components
            odds_collector = OddsCollector()
            
            # Collect odds
            await odds_collector.collect_all_odds()
            
            # Verify database entries
            with Session(test_database) as session:
                markets = session.query(Markets).all()
                odds = session.query(Odds).all()
                
                # Assert correct number of entries
                assert len(markets) == 1
                assert len(odds) == 4  # 2 selections × 2 sources
                
                # Verify market data
                market = markets[0]
                assert market.event_name == "Test Match"
                assert market.market_type == "MATCH_ODDS"
                
                # Verify odds data
                betfair_odds = [o for o in odds if o.source == "Betfair"]
                oddsjet_odds = [o for o in odds if o.source == "OddsJet"]
                
                assert len(betfair_odds) == 2
                assert len(oddsjet_odds) == 2

@pytest.mark.asyncio
async def test_arbitrage_detection_pipeline(test_database, mock_betfair_response, mock_oddsjet_data):
    """
    Test the complete pipeline from odds collection through arbitrage detection
    Verifies that arbitrage opportunities are correctly identified and stored
    """
    # Modify mock data to create an arbitrage opportunity
    mock_betfair_response["markets"][0]["runners"][0]["lastPriceTraded"] = 2.1
    mock_oddsjet_data[0]["selections"][1]["odds"] = 2.2
    
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            # Initialize components
            odds_collector = OddsCollector()
            arbitrage_detector = ArbitrageDetector()
            
            # Run collection and analysis
            await odds_collector.collect_all_odds()
            opportunities = await arbitrage_detector.analyze_markets()
            
            # Verify arbitrage detection
            assert len(opportunities) > 0
            
            # Verify database storage
            with Session(test_database) as session:
                stored_opportunities = session.query(ArbitrageOpportunities).all()
                assert len(stored_opportunities) > 0
                
                # Verify opportunity details
                opportunity = stored_opportunities[0]
                assert opportunity.profit_percentage > 0
                assert opportunity.status == "ACTIVE"

@pytest.mark.asyncio
async def test_ui_data_flow(test_database, mock_betfair_response, mock_oddsjet_data, qtbot):
    """
    Test that collected data properly flows to the UI
    Verifies the entire pipeline from collection through display
    """
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            # Initialize components
            odds_collector = OddsCollector()
            arbitrage_detector = ArbitrageDetector()
            main_window = MainWindow(odds_collector, arbitrage_detector)
            
            # Add window to qtbot
            qtbot.addWidget(main_window)
            
            # Trigger data collection and update
            await odds_collector.collect_all_odds()
            main_window.update_display()
            
            # Verify UI elements
            market_table = main_window.market_table
            assert market_table.rowCount() > 0
            
            # Verify market data in table
            assert market_table.item(0, 0).text() == "Test Match"

@pytest.mark.asyncio
async def test_error_handling_and_recovery(test_database, mock_betfair_response, mock_oddsjet_data):
    """
    Test system resilience and error handling
    Verifies that the system properly handles and recovers from various error conditions
    """
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        # Simulate API failure then recovery
        mock_betfair.return_value.get_market_odds.side_effect = [
            Exception("API Error"),  # First call fails
            mock_betfair_response   # Second call succeeds
        ]
        
        odds_collector = OddsCollector()
        
        # First attempt should handle error gracefully
        await odds_collector.collect_all_odds()
        
        # Verify error logging and recovery
        with Session(test_database) as session:
            error_logs = session.query(ErrorLogs).all()
            assert len(error_logs) > 0
            assert "API Error" in error_logs[0].error_message
        
        # Second attempt should succeed
        await odds_collector.collect_all_odds()
        
        # Verify successful data collection after recovery
        with Session(test_database) as session:
            markets = session.query(Markets).all()
            assert len(markets) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])