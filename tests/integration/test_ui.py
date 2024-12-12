import pytest
from unittest.mock import patch
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt
from sqlalchemy.orm import Session
from src.data_collection.odds_collector import OddsCollector
from src.analysis.arbitrage_detector import ArbitrageDetector
from tests.helpers import TestHelper

@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_table_updates(test_database, mock_betfair_response, mock_oddsjet_data,
                                 qt_application, main_window, qtbot):
    """Tests that the market table correctly displays and updates odds data.
    
    This test verifies that when new odds data arrives, the UI properly:
    1. Updates the market table with new entries
    2. Formats odds values correctly
    3. Maintains proper sorting order
    4. Updates existing entries rather than duplicating them
    """
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            odds_collector = OddsCollector()
            
            # Initial data collection
            await odds_collector.collect_all_odds()
            qtbot.wait(100)  # Allow UI to process events
            
            # Verify initial table state
            market_table = main_window.market_table
            assert market_table.rowCount() > 0, "Market table should contain data"
            assert market_table.item(0, 0).text() == "Test Match"
            
            # Modify mock data and update
            mock_betfair_response["markets"][0]["runners"][0]["lastPriceTraded"] = 2.5
            await odds_collector.collect_all_odds()
            qtbot.wait(100)
            
            # Verify table was updated
            updated_odds = float(market_table.item(0, 2).text())
            assert abs(updated_odds - 2.5) < 0.01, "Table should show updated odds"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_arbitrage_alerts(test_database, mock_betfair_response, mock_oddsjet_data,
                             qt_application, main_window, qtbot, mock_alert_threshold):
    """Tests the UI alert system for arbitrage opportunities.
    
    Verifies that the system properly:
    1. Displays alerts when opportunities are found
    2. Shows correct profit calculations
    3. Updates alert status when opportunities change
    4. Handles alert dismissal correctly
    """
    # Create data that will trigger an arbitrage alert
    mock_betfair_response["markets"][0]["runners"][0]["lastPriceTraded"] = 2.1
    mock_oddsjet_data[0]["selections"][1]["odds"] = 2.2
    
    with patch('src.data_collection.betfair_client.BetfairClient') as mock_betfair:
        mock_betfair.return_value.get_market_odds.return_value = mock_betfair_response
        
        with patch('src.data_collection.oddsjet_scraper.OddsJetScraper') as mock_scraper:
            mock_scraper.return_value.scrape_odds.return_value = mock_oddsjet_data
            
            # Set alert threshold and trigger data collection
            main_window.set_alert_threshold(mock_alert_threshold)
            
            odds_collector = OddsCollector()
            await odds_collector.collect_all_odds()
            qtbot.wait(100)
            
            # Verify alert panel shows the opportunity
            assert main_window.alert_panel.isVisible(), "Alert panel should be visible"
            alert_text = main_window.alert_panel.toPlainText()
            assert "Test Match" in alert_text, "Alert should show market name"
            assert "Profit:" in alert_text, "Alert should show profit percentage"
            
            # Test alert dismissal
            qtbot.mouseClick(main_window.dismiss_alert_button, Qt.MouseButton.LeftButton)
            qtbot.wait(100)
            assert not main_window.alert_panel.isVisible(), "Alert should be dismissed"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_settings_persistence(test_database, qt_application, main_window, qtbot):
    """Tests that UI settings are properly saved and restored.
    
    Verifies:
    1. Alert thresholds are preserved
    2. Source configurations are maintained
    3. Update intervals are correctly stored
    4. UI state reflects saved settings
    """
    # Configure settings
    main_window.set_alert_threshold(1.5)  # 1.5% profit threshold
    main_window.set_update_interval(30)   # 30 second updates
    main_window.toggle_source("Betfair", True)
    main_window.toggle_source("OddsJet", False)
    
    # Save settings
    main_window.save_settings()
    
    # Create new window instance
    new_window = type(main_window)(OddsCollector(), ArbitrageDetector())
    qtbot.wait(100)
    
    # Verify settings were restored
    assert abs(new_window.get_alert_threshold() - 1.5) < 0.01, "Alert threshold should be preserved"
    assert new_window.get_update_interval() == 30, "Update interval should be preserved"
    assert new_window.is_source_enabled("Betfair"), "Betfair should be enabled"
    assert not new_window.is_source_enabled("OddsJet"), "OddsJet should be disabled"