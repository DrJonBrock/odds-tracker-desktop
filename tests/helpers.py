from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session
from src.database.models import Markets, Odds, ArbitrageOpportunities

class TestHelper:
    @staticmethod
    def create_test_market(session: Session, event_name: str = "Test Match") -> Markets:
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
    def create_test_odds(session: Session, market: Markets, source: str, selection: str, odds_value: float) -> Odds:
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