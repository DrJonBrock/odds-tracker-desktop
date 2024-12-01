import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database.database import init_database

@pytest.fixture
def mock_betfair_response():
    return {
        "markets": [{
            "marketId": "1.234567",
            "eventName": "Test Match",
            "marketType": "MATCH_ODDS",
            "startTime": (datetime.now() + timedelta(hours=1)).isoformat(),
            "runners": [
                {"selectionId": 1234, "runnerName": "Team A", "lastPriceTraded": 2.0},
                {"selectionId": 5678, "runnerName": "Team B", "lastPriceTraded": 1.8}
            ]
        }]
    }

@pytest.fixture
def mock_oddsjet_data():
    return [{
        "event_name": "Test Match",
        "market_type": "MATCH_ODDS",
        "selections": [
            {"name": "Team A", "odds": 2.1},
            {"name": "Team B", "odds": 1.9}
        ]
    }]

@pytest.fixture
async def test_database():
    database_url = "sqlite:///:memory:"
    engine = init_database(database_url)
    
    from src.database.models import Base
    Base.metadata.create_all(engine)
    
    return engine