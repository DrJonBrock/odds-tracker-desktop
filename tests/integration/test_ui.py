import pytest
from unittest.mock import patch
from PyQt6.QtWidgets import QTableWidgetItem
from src.data_collection.odds_collector import OddsCollector
from src.analysis.arbitrage_detector import ArbitrageDetector

@pytest.mark.integration
@pytest.mark.asyncio
async def test_ui_data_flow(test_database, mock_betfair_response, mock_oddsjet_data, 
                          qt_application, main_window, qtbot):
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            await odds_collector.collect_all_odds()
            
            qtbot.wait(100)
            
            market_table = main_window.market_table
            assert market_table.rowCount() > 0
            assert market_table.item(0, 0).text() == "Test Match"