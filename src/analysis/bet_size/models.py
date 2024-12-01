"""Core data models for the bet size calculator.

This module defines the fundamental data structures used throughout the calculator,
including position tracking and opportunity representation. The models are implemented
as dataclasses for clean, immutable data handling with proper type hints.
"""

from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class BookPosition:
    """Represents a position and constraints at a specific bookmaker.
    
    This class encapsulates all relevant information about a bookmaker's current
    state, including available liquidity, exposure, and reliability metrics.
    
    Attributes:
        bookmaker: Unique identifier for the bookmaker
        available_liquidity: Maximum amount that can be bet at current odds
        current_exposure: Sum of current open position values
        max_bet_size: Maximum allowed single bet size
        reliability_score: Historical measure of book reliability (0-1)
        min_bet_size: Minimum allowed bet size
        recent_limit_changes: Number of times limits were adjusted in last 24h
        last_odds_update: Timestamp of most recent odds update
    """
    bookmaker: str
    available_liquidity: float
    current_exposure: float
    max_bet_size: float
    reliability_score: float
    min_bet_size: float = 0.0
    recent_limit_changes: int = 0
    last_odds_update: datetime = None
    
    def __post_init__(self):
        """Validate the BookPosition data after initialization."""
        if self.reliability_score < 0 or self.reliability_score > 1:
            raise ValueError("Reliability score must be between 0 and 1")
        if self.available_liquidity < 0:
            raise ValueError("Available liquidity cannot be negative")
        if self.max_bet_size < self.min_bet_size:
            raise ValueError("Maximum bet size must be greater than minimum")

@dataclass
class ArbitrageOpportunity:
    """Represents a detected arbitrage opportunity across multiple bookmakers.
    
    This class contains all information needed to evaluate and execute an arbitrage
    opportunity, including odds, associated books, and expected profitability.
    
    Attributes:
        market_id: Unique identifier for the market
        selections: List of possible outcomes (e.g., ["Team A", "Draw", "Team B"])
        odds: Mapping of selection to best available odds
        books: Mapping of selection to bookmaker offering those odds
        timestamp: When the opportunity was detected
        expected_profit_rate: Theoretical profit rate if all bets are placed
        market_name: Description of the market (e.g., "Match Result")
        event_name: Name of the event (e.g., "Liverpool vs Chelsea")
        start_time: When the event begins
        category: Sport or category (e.g., "Soccer", "Tennis")
        total_matched: Total amount matched on this market (if available)
    """
    market_id: int
    selections: List[str]
    odds: Dict[str, float]
    books: Dict[str, str]
    timestamp: datetime
    expected_profit_rate: float
    market_name: str = ""
    event_name: str = ""
    start_time: datetime = None
    category: str = ""
    total_matched: float = 0.0
    
    def __post_init__(self):
        """Validate the ArbitrageOpportunity data after initialization."""
        if not self.selections:
            raise ValueError("Must have at least one selection")
        if set(self.odds.keys()) != set(self.selections):
            raise ValueError("Odds must be provided for all selections")
        if set(self.books.keys()) != set(self.selections):
            raise ValueError("Books must be specified for all selections")
        if self.expected_profit_rate < -1:
            raise ValueError("Expected profit rate cannot be less than -100%")
            
    def get_implied_probability(self) -> float:
        """Calculate the total implied probability from the odds.
        
        Returns:
            float: Sum of implied probabilities. Values > 1 indicate negative EV.
        """
        return sum(1/odd for odd in self.odds.values())
    
    def is_arbitrage(self) -> bool:
        """Determine if this opportunity represents a true arbitrage.
        
        Returns:
            bool: True if total implied probability < 1, indicating arbitrage.
        """
        return self.get_implied_probability() < 1