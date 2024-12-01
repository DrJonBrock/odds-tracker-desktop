"""
Advanced Bet Size Calculator for Odds Tracker Desktop

This module implements sophisticated bet sizing strategies including:
- Kelly Criterion calculation with fractional Kelly options
- Position balancing across multiple books
- Risk-adjusted position sizing
- Bankroll management constraints
- Liquidity-aware bet sizing
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime

@dataclass
class BookPosition:
    """Represents a position at a specific bookmaker"""
    bookmaker: str
    available_liquidity: float
    current_exposure: float
    max_bet_size: float
    reliability_score: float  # Score from 0-1 indicating book reliability

@dataclass
class ArbitrageOpportunity:
    """Represents a detected arbitrage opportunity across books"""
    market_id: int
    selections: List[str]
    odds: Dict[str, float]  # Selection -> odds mapping
    books: Dict[str, str]   # Selection -> bookmaker mapping
    timestamp: datetime
    expected_profit_rate: float

class BetSizeCalculator:
    def __init__(
        self,
        total_bankroll: float,
        max_exposure_ratio: float = 0.25,
        kelly_fraction: float = 0.5,
        min_reliability_score: float = 0.7
    ):
        """
        Initialize the bet size calculator with risk parameters.
        
        Args:
            total_bankroll: Total available bankroll across all books
            max_exposure_ratio: Maximum portion of bankroll to risk on single opportunity
            kelly_fraction: Fraction of Kelly bet size to use (conservative approach)
            min_reliability_score: Minimum acceptable book reliability score
        """
        self.total_bankroll = total_bankroll
        self.max_exposure_ratio = max_exposure_ratio
        self.kelly_fraction = kelly_fraction
        self.min_reliability_score = min_reliability_score
        
    def calculate_optimal_bet_sizes(
        self,
        opportunity: ArbitrageOpportunity,
        book_positions: Dict[str, BookPosition]
    ) -> Optional[Dict[str, float]]:
        """
        Calculate optimal bet sizes for each leg of an arbitrage opportunity.
        
        Args:
            opportunity: Detected arbitrage opportunity
            book_positions: Current positions and constraints for each book
            
        Returns:
            Dictionary mapping selections to optimal bet sizes, or None if opportunity
            should be skipped
        """
        # Validate book reliability
        for selection, book in opportunity.books.items():
            if book_positions[book].reliability_score < self.min_reliability_score:
                return None
                
        # Calculate base Kelly bet sizes
        total_stake = self._calculate_kelly_stakes(opportunity)
        
        # Apply position balancing
        balanced_stakes = self._balance_positions(total_stake, opportunity, book_positions)
        
        # Apply liquidity constraints
        final_stakes = self._apply_liquidity_constraints(balanced_stakes, opportunity, book_positions)
        
        # Validate final stakes meet minimum profit threshold
        if not self._validate_profit_threshold(final_stakes, opportunity):
            return None
            
        return final_stakes
    
    def _calculate_kelly_stakes(
        self,
        opportunity: ArbitrageOpportunity
    ) -> Dict[str, float]:
        """
        Calculate Kelly Criterion-based stakes for each selection.
        
        The Kelly Criterion is modified for arbitrage betting where we have
        multiple concurrent positions with known outcomes.
        """
        stakes = {}
        total_stake = self.total_bankroll * self.max_exposure_ratio * self.kelly_fraction
        
        # Calculate implied probabilities
        total_probability = sum(1/odd for odd in opportunity.odds.values())
        
        # Allocate stakes to achieve equal profit across all outcomes
        for selection, odd in opportunity.odds.items():
            implied_prob = 1/odd
            fair_prob = implied_prob / total_probability
            stakes[selection] = total_stake * fair_prob
            
        return stakes
        
    def _balance_positions(
        self,
        base_stakes: Dict[str, float],
        opportunity: ArbitrageOpportunity,
        book_positions: Dict[str, BookPosition]
    ) -> Dict[str, float]:
        """
        Adjust stakes to account for existing positions at each book.
        
        This helps maintain balanced exposure across books and prevent
        overconcentration of risk.
        """
        balanced_stakes = base_stakes.copy()
        
        # Calculate current exposure ratios
        total_exposure = sum(pos.current_exposure for pos in book_positions.values())
        if total_exposure > 0:
            exposure_ratios = {
                book: pos.current_exposure / total_exposure
                for book, pos in book_positions.items()
            }
            
            # Adjust stakes based on current exposure
            for selection, stake in balanced_stakes.items():
                book = opportunity.books[selection]
                ratio = exposure_ratios.get(book, 0)
                # Reduce stakes for books with high existing exposure
                balanced_stakes[selection] *= (1 - ratio)
                
        return balanced_stakes
        
    def _apply_liquidity_constraints(
        self,
        stakes: Dict[str, float],
        opportunity: ArbitrageOpportunity,
        book_positions: Dict[str, BookPosition]
    ) -> Dict[str, float]:
        """
        Adjust stakes based on available liquidity at each book.
        
        This prevents placing bets that are too large for the market
        to handle without significant price impact.
        """
        constrained_stakes = stakes.copy()
        
        for selection, stake in stakes.items():
            book = opportunity.books[selection]
            position = book_positions[book]
            
            # Apply book-specific constraints
            max_allowed = min(
                position.available_liquidity,
                position.max_bet_size,
                self.total_bankroll * self.max_exposure_ratio
            )
            
            constrained_stakes[selection] = min(stake, max_allowed)
            
        return constrained_stakes
        
    def _validate_profit_threshold(
        self,
        stakes: Dict[str, float],
        opportunity: ArbitrageOpportunity,
        min_profit_rate: float = 0.002  # 0.2% minimum profit
    ) -> bool:
        """
        Verify that the opportunity still meets minimum profit threshold
        after all constraints are applied.
        """
        total_stake = sum(stakes.values())
        if total_stake == 0:
            return False
            
        # Calculate worst-case profit rate
        min_profit = float('inf')
        for selection, stake in stakes.items():
            profit = stake * opportunity.odds[selection] - total_stake
            profit_rate = profit / total_stake
            min_profit = min(min_profit, profit_rate)
            
        return min_profit >= min_profit_rate

    def update_bankroll(self, new_total: float):
        """Update total bankroll value"""
        self.total_bankroll = new_total
        
    def update_risk_parameters(
        self,
        max_exposure_ratio: Optional[float] = None,
        kelly_fraction: Optional[float] = None,
        min_reliability_score: Optional[float] = None
    ):
        """Update risk management parameters"""
        if max_exposure_ratio is not None:
            self.max_exposure_ratio = max_exposure_ratio
        if kelly_fraction is not None:
            self.kelly_fraction = kelly_fraction
        if min_reliability_score is not None:
            self.min_reliability_score = min_reliability_score