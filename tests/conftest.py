import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database.database import init_database

# This fixture provides consistent mock data for Betfair API responses
# It simulates a typical match with two teams and their odds
@pytest.fixture
def mock_betfair_response():
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

# This fixture simulates scraped data from OddsJet
# The structure matches what our scraper would return from the website
@pytest.fixture
def mock_oddsjet_data():
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

# This fixture creates an in-memory SQLite database for testing
# Using in-memory database ensures tests are isolated and fast
@pytest.fixture
async def test_database():
    database_url = "sqlite:///:memory:"
    engine = init_database(database_url)
    
    # Create all tables defined in our models
    from src.database.models import Base
    Base.metadata.create_all(engine)
    
    # Return the engine for use in tests
    return engine

# This fixture provides a clean database session for each test
@pytest.fixture
def db_session(test_database):
    Session = sessionmaker(bind=test_database)
    session = Session()
    
    try:
        yield session
    finally:
        # Ensure we clean up after each test
        session.rollback()
        session.close()