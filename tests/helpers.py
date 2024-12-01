from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from src.database.models import Markets, Odds, ArbitrageOpportunities

class TestHelper:
    @staticmethod
    def create_test_market(session: Session, event_name: str = "Test Match") -> Markets:
        """Creates a test market entry in the database"""
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
        """Creates a test odds entry in the database"""
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
        """Verifies the properties of an arbitrage opportunity"""
        return (
            opportunity.market_id == market_id and
            abs(opportunity.profit_percentage - expected_profit) < 0.01 and
            opportunity.status == "ACTIVE"
        )

    @staticmethod
    def compare_odds_data(stored_odds: Odds, 
                         expected_data: Dict) -> bool:
        """Compares stored odds with expected data"""
        return (
            stored_odds.selection == expected_data["selection"] and
            abs(stored_odds.odds_value - expected_data["odds_value"]) < 0.01 and
            stored_odds.source == expected_data["source"]
        )