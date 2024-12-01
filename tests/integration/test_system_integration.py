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
    """Test that odds collection properly stores data in the database"""
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
                
                betfair_odds = [o for o in odds if o.source == "Betfair"]
                oddsjet_odds = [o for o in odds if o.source == "OddsJet"]
                
                assert len(betfair_odds) == 2
                assert len(oddsjet_odds) == 2

@pytest.mark.asyncio
async def test_arbitrage_detection_pipeline(test_database, mock_betfair_response, mock_oddsjet_data):
    """Test the complete pipeline from collection through arbitrage detection"""
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

@pytest.mark.asyncio
async def test_ui_data_flow(test_database, mock_betfair_response, mock_oddsjet_data, qtbot):
    """Test that collected data properly flows to the UI"""
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            arbitrage_detector = ArbitrageDetector()
            main_window = MainWindow(odds_collector, arbitrage_detector)
            
            qtbot.addWidget(main_window)
            
            await odds_collector.collect_all_odds()
            main_window.update_display()
            
            market_table = main_window.market_table
            assert market_table.rowCount() > 0
            assert market_table.item(0, 0).text() == "Test Match"

@pytest.mark.asyncio
async def test_error_handling_and_recovery(test_database, mock_betfair_response, mock_oddsjet_data):
    """Test system resilience and error handling"""
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.side_effect = [
            Exception("API Error"),  # First call fails
            mock_betfair_response   # Second call succeeds
        ]
        
        odds_collector = OddsCollector()
        
        # First attempt should handle error gracefully
        await odds_collector.collect_all_odds()
        
        with Session(test_database) as session:
            error_logs = session.query(ErrorLogs).all()
            assert len(error_logs) > 0
            assert "API Error" in error_logs[0].error_message
        
        # Second attempt should succeed
        await odds_collector.collect_all_odds()
        
        with Session(test_database) as session:
            markets = session.query(Markets).all()
            assert len(markets) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])