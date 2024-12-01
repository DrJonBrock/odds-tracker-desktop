from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from src.database.models import Markets, Odds, ArbitrageOpportunities

class TestHelper:
    """A utility class that provides helper methods for common test operations.
    
    This class simplifies test setup and verification by providing methods to:
    - Create test market entries
    - Generate test odds data
    - Verify arbitrage opportunities
    - Compare odds data across sources
    """
    
    @staticmethod
    def create_test_market(session: Session, event_name: str = "Test Match") -> Markets:
        """Creates a test market entry in the database.
        
        Args:
            session: SQLAlchemy session for database operations
            event_name: Name of the event (default: "Test Match")
            
        Returns:
            The created Markets instance
        """
        market = Markets(
            event_name=event_name,
            market_type="MATCH_ODDS",
            start_time=datetime.now(),
            status="ACTIVE"
        )
        session.add(market)
        session.commit()
        return market

    @staticmethod
    def create_test_odds(session: Session, 
                        market: Markets,
                        source: str,
                        selection: str,
                        odds_value: float) -> Odds:
        """Creates a test odds entry in the database.
        
        Args:
            session: SQLAlchemy session for database operations
            market: The market these odds belong to
            source: Name of the odds source (e.g., "Betfair", "OddsJet")
            selection: Name of the selection (e.g., "Team A")
            odds_value: The decimal odds value
            
        Returns:
            The created Odds instance
        """
        odds = Odds(
            market_id=market.id,
            source=source,
            selection=selection,
            odds_value=odds_value,
            timestamp=datetime.now(),
            is_active=True
        )
        session.add(odds)
        session.commit()
        return odds

    @staticmethod
    def verify_arbitrage_opportunity(opportunity: ArbitrageOpportunities,
                                   expected_profit: float,
                                   market_id: int) -> bool:
        """Verifies that an arbitrage opportunity matches expected values.
        
        Args:
            opportunity: The ArbitrageOpportunities instance to verify
            expected_profit: The expected profit percentage
            market_id: The expected market ID
            
        Returns:
            True if the opportunity matches expectations, False otherwise
        """
        return (
            opportunity.market_id == market_id and
            abs(opportunity.profit_percentage - expected_profit) < 0.01 and
            opportunity.status == "ACTIVE"
        )

    @staticmethod
    def compare_odds_data(stored_odds: Odds, 
                         expected_data: Dict) -> bool:
        """Compares stored odds with expected data.
        
        Args:
            stored_odds: The Odds instance from the database
            expected_data: Dictionary containing expected values
            
        Returns:
            True if the stored odds match expectations, False otherwise
        """
        return (
            stored_odds.selection == expected_data["selection"] and
            abs(stored_odds.odds_value - expected_data["odds_value"]) < 0.01 and
            stored_odds.source == expected_data["source"]
        )