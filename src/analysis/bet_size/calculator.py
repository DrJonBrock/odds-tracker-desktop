"""Core bet size calculation logic.

This module implements sophisticated betting strategies including Kelly Criterion
and position balancing. It provides a comprehensive approach to optimal bet sizing
that accounts for multiple factors including:

1. Risk management through fractional Kelly sizing
2. Position balancing across multiple books
3. Liquidity constraints and book reliability
4. Minimum profit thresholds
"""

from typing import Dict, Optional, List
from datetime import datetime
from .models import BookPosition, ArbitrageOpportunity
from .constants import (
    DEFAULT_MAX_EXPOSURE_RATIO,
    DEFAULT_KELLY_FRACTION,
    DEFAULT_MIN_RELIABILITY
)

class BetSizeCalculator:
    """Calculates optimal bet sizes for arbitrage opportunities.
    
    This class implements advanced bet sizing strategies that combine the Kelly
    Criterion with practical constraints like position balancing and liquidity
    limits. It aims to maximize long-term growth while managing risk.
    """
    
    def __init__(
        self,
        total_bankroll: float,
        max_exposure_ratio: float = DEFAULT_MAX_EXPOSURE_RATIO,
        kelly_fraction: float = DEFAULT_KELLY_FRACTION,
        min_reliability_score: float = DEFAULT_MIN_RELIABILITY,
        min_profit_rate: float = 0.002  # 0.2% minimum profit
    ):
        """Initialize the calculator with risk parameters.
        
        The calculator uses several parameters to control risk exposure and bet
        sizing. These can be adjusted based on risk tolerance and market conditions.
        
        Args:
            total_bankroll: Total available capital across all books
            max_exposure_ratio: Maximum portion of bankroll to risk on one opportunity
            kelly_fraction: Conservative multiplier for Kelly bet sizes (0-1)
            min_reliability_score: Minimum acceptable book reliability score
            min_profit_rate: Minimum acceptable profit rate after all costs
        """
        if total_bankroll <= 0:
            raise ValueError("Bankroll must be positive")
        if not 0 < max_exposure_ratio <= 1:
            raise ValueError("Max exposure ratio must be between 0 and 1")
        if not 0 < kelly_fraction <= 1:
            raise ValueError("Kelly fraction must be between 0 and 1")
        if not 0 <= min_reliability_score <= 1:
            raise ValueError("Reliability score must be between 0 and 1")
        if min_profit_rate < 0:
            raise ValueError("Minimum profit rate cannot be negative")
            
        self.total_bankroll = total_bankroll
        self.max_exposure_ratio = max_exposure_ratio
        self.kelly_fraction = kelly_fraction
        self.min_reliability_score = min_reliability_score
        self.min_profit_rate = min_profit_rate
        
    def calculate_optimal_bet_sizes(
        self,
        opportunity: ArbitrageOpportunity,
        book_positions: Dict[str, BookPosition]
    ) -> Optional[Dict[str, float]]:
        """Calculate optimal bet sizes for an arbitrage opportunity.
        
        This method implements the core logic for determining bet sizes. It follows
        a multi-step process:
        1. Validate book reliability and basic constraints
        2. Calculate base Kelly stakes
        3. Apply position balancing across books
        4. Apply liquidity and exposure constraints
        5. Validate final profitability
        
        Args:
            opportunity: The detected arbitrage opportunity
            book_positions: Current positions and constraints for each book
            
        Returns:
            Dictionary mapping selections to optimal bet sizes, or None if the
            opportunity should be skipped
        """
        # Skip if any book is below minimum reliability score
        if not self._validate_books(opportunity, book_positions):
            return None
            
        # Calculate Kelly stakes before constraints
        base_stakes = self._calculate_kelly_stakes(opportunity)
        
        # Apply position balancing
        balanced_stakes = self._balance_positions(base_stakes, opportunity, book_positions)
        
        # Apply liquidity and exposure constraints
        final_stakes = self._apply_constraints(balanced_stakes, opportunity, book_positions)
        
        # Validate profitability after all adjustments
        if not self._validate_profit(final_stakes, opportunity):
            return None
            
        return final_stakes
        
    def _validate_books(
        self,
        opportunity: ArbitrageOpportunity,
        book_positions: Dict[str, BookPosition]
    ) -> bool:
        """Validate that all books meet reliability and basic requirements."""
        for selection, book in opportunity.books.items():
            position = book_positions.get(book)
            if not position:
                return False
            if position.reliability_score < self.min_reliability_score:
                return False
            if position.max_bet_size <= position.min_bet_size:
                return False
        return True
        
    def _calculate_kelly_stakes(
        self,
        opportunity: ArbitrageOpportunity
    ) -> Dict[str, float]:
        """Calculate Kelly Criterion-based stakes for each selection.
        
        This implements a modified Kelly formula adapted for arbitrage betting
        where we have multiple concurrent positions with known outcomes.
        """
        stakes = {}
        total_stake = self.total_bankroll * self.max_exposure_ratio * self.kelly_fraction
        
        # Calculate implied probabilities
        total_prob = sum(1/odd for odd in opportunity.odds.values())
        
        # Allocate stakes to achieve equal profit across outcomes
        for selection, odd in opportunity.odds.items():
            implied_prob = 1/odd
            fair_prob = implied_prob / total_prob
            stakes[selection] = total_stake * fair_prob
            
        return stakes
        
    def _balance_positions(
        self,
        stakes: Dict[str, float],
        opportunity: ArbitrageOpportunity,
        book_positions: Dict[str, BookPosition]
    ) -> Dict[str, float]:
        """Balance stakes based on current book exposure.
        
        This helps maintain balanced exposure across books and prevent
        overconcentration of risk at any single book.
        """
        balanced = stakes.copy()
        
        # Calculate current exposure ratios
        total_exposure = sum(pos.current_exposure for pos in book_positions.values())
        if total_exposure > 0:
            exposure_ratios = {
                book: pos.current_exposure / total_exposure
                for book, pos in book_positions.items()
            }
            
            # Reduce stakes for books with high exposure
            for selection, stake in balanced.items():
                book = opportunity.books[selection]
                ratio = exposure_ratios.get(book, 0)
                balanced[selection] *= (1 - ratio * 0.5)  # Scale factor of 0.5
                
        return balanced
        
    def _apply_constraints(
        self,
        stakes: Dict[str, float],
        opportunity: ArbitrageOpportunity,
        book_positions: Dict[str, BookPosition]
    ) -> Dict[str, float]:
        """Apply all constraints to the stakes.
        
        This includes:
        - Book-specific bet size limits
        - Available liquidity
        - Maximum exposure limits
        """
        constrained = stakes.copy()
        
        for selection, stake in stakes.items():
            book = opportunity.books[selection]
            position = book_positions[book]
            
            # Apply all relevant constraints
            max_allowed = min(
                position.available_liquidity,
                position.max_bet_size,
                self.total_bankroll * self.max_exposure_ratio
            )
            
            # Ensure we meet minimum bet size if betting at all
            if stake < position.min_bet_size:
                constrained[selection] = 0
            else:
                constrained[selection] = min(stake, max_allowed)
                
        return constrained
        
    def _validate_profit(
        self,
        stakes: Dict[str, float],
        opportunity: ArbitrageOpportunity
    ) -> bool:
        """Verify that the opportunity still meets minimum profit threshold."""
        total_stake = sum(stakes.values())
        if total_stake == 0:
            return False
            
        # Calculate worst-case profit rate
        min_profit = float('inf')
        for selection, stake in stakes.items():
            if stake > 0:  # Only consider active positions
                odd = opportunity.odds[selection]
                profit = stake * odd - total_stake
                profit_rate = profit / total_stake
                min_profit = min(min_profit, profit_rate)
                
        return min_profit >= self.min_profit_rate
        
    def update_parameters(
        self,
        total_bankroll: Optional[float] = None,
        max_exposure_ratio: Optional[float] = None,
        kelly_fraction: Optional[float] = None,
        min_reliability_score: Optional[float] = None,
        min_profit_rate: Optional[float] = None
    ):
        """Update calculator parameters while maintaining validation."""
        if total_bankroll is not None:
            if total_bankroll <= 0:
                raise ValueError("Bankroll must be positive")
            self.total_bankroll = total_bankroll
            
        if max_exposure_ratio is not None:
            if not 0 < max_exposure_ratio <= 1:
                raise ValueError("Max exposure ratio must be between 0 and 1")
            self.max_exposure_ratio = max_exposure_ratio
            
        if kelly_fraction is not None:
            if not 0 < kelly_fraction <= 1:
                raise ValueError("Kelly fraction must be between 0 and 1")
            self.kelly_fraction = kelly_fraction
            
        if min_reliability_score is not None:
            if not 0 <= min_reliability_score <= 1:
                raise ValueError("Reliability score must be between 0 and 1")
            self.min_reliability_score = min_reliability_score
            
        if min_profit_rate is not None:
            if min_profit_rate < 0:
                raise ValueError("Minimum profit rate cannot be negative")
            self.min_profit_rate = min_profit_rate