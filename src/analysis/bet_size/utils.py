"""Utility functions for bet size calculations.

This module provides helper functions for common betting calculations and data
transformations. These utilities support the main calculator by providing
reusable tools for odds processing, probability calculations, and stake
optimization.
"""

from typing import Dict, List, Tuple, Optional
from decimal import Decimal, ROUND_DOWN
import math

def normalize_odds(
    odds: float,
    format_type: str = 'decimal'
) -> float:
    """Convert odds between different formats.
    
    Betting odds can come in various formats (decimal, fractional, American).
    This function converts them to a standardized decimal format for calculations.
    
    Args:
        odds: The odds value to convert
        format_type: The format of the input odds ('decimal', 'fractional', 'american')
    
    Returns:
        float: The odds in decimal format
    """
    if format_type == 'decimal':
        return float(odds)
    elif format_type == 'fractional':
        # Convert fractional odds like '5/2' to decimal
        num, den = map(float, str(odds).split('/'))
        return 1 + (num / den)
    elif format_type == 'american':
        # Convert American odds to decimal
        if odds > 0:
            return 1 + (odds / 100)
        else:
            return 1 + (100 / abs(odds))
    else:
        raise ValueError(f"Unsupported odds format: {format_type}")

def calculate_implied_probability(odds: float) -> float:
    """Calculate implied probability from decimal odds.
    
    The implied probability represents the market's estimate of the likelihood
    of an outcome, derived from the odds being offered.
    
    Args:
        odds: Decimal format odds
    
    Returns:
        float: Implied probability as a decimal (0-1)
    """
    return 1 / odds

def validate_arbitrage_stakes(
    stakes: Dict[str, float],
    odds: Dict[str, float],
    min_profit_rate: float = 0.002,
    tolerance: float = 1e-6
) -> bool:
    """Validate that a set of stakes creates a valid arbitrage opportunity.
    
    This function checks several criteria:
    1. All stakes are non-negative
    2. Profit meets minimum threshold for all outcomes
    3. Stakes are balanced correctly for arbitrage
    
    Args:
        stakes: Dictionary mapping selections to stake amounts
        odds: Dictionary mapping selections to decimal odds
        min_profit_rate: Minimum acceptable profit rate
        tolerance: Numerical tolerance for floating point comparisons
    
    Returns:
        bool: True if stakes represent a valid arbitrage opportunity
    """
    if not stakes or not odds or set(stakes.keys()) != set(odds.keys()):
        return False
        
    # Check for negative stakes
    if any(stake < 0 for stake in stakes.values()):
        return False
        
    total_stake = sum(stakes.values())
    if total_stake == 0:
        return False
        
    # Calculate profit for each outcome
    min_profit_rate_achieved = float('inf')
    for selection, stake in stakes.items():
        if stake > 0:  # Only check active positions
            payout = stake * odds[selection]
            profit = payout - total_stake
            profit_rate = profit / total_stake
            min_profit_rate_achieved = min(min_profit_rate_achieved, profit_rate)
            
    return min_profit_rate_achieved >= min_profit_rate

def calculate_optimal_stakes(
    odds: Dict[str, float],
    total_stake: float,
    min_stake: Optional[Dict[str, float]] = None,
    max_stake: Optional[Dict[str, float]] = None
) -> Optional[Dict[str, float]]:
    """Calculate optimal stakes for arbitrage opportunity with constraints.
    
    This function finds the optimal distribution of stakes across selections
    to maximize profit while respecting minimum and maximum stake constraints.
    It uses an iterative approach to handle cases where simple proportional
    allocation would violate constraints.
    
    Args:
        odds: Dictionary mapping selections to decimal odds
        total_stake: Total amount to be staked
        min_stake: Optional minimum stakes per selection
        max_stake: Optional maximum stakes per selection
    
    Returns:
        Optional[Dict[str, float]]: Optimized stakes if solution exists, None if no
        valid solution is found
    """
    if min_stake is None:
        min_stake = {sel: 0.0 for sel in odds}
    if max_stake is None:
        max_stake = {sel: float('inf') for sel in odds}
        
    # Validate inputs
    if not all(min_stake[sel] <= max_stake[sel] for sel in odds):
        return None
        
    # Initial allocation based on equal profit
    stakes = optimize_stakes_for_equal_profit(odds, total_stake)
    
    # Apply constraints iteratively
    for _ in range(100):  # Limit iterations to prevent infinite loops
        violations = False
        remaining_stake = total_stake
        
        # Apply minimum stakes
        for sel in odds:
            if stakes[sel] < min_stake[sel]:
                stakes[sel] = min_stake[sel]
                remaining_stake -= min_stake[sel]
                violations = True
                
        # Apply maximum stakes
        for sel in odds:
            if stakes[sel] > max_stake[sel]:
                stakes[sel] = max_stake[sel]
                remaining_stake -= max_stake[sel]
                violations = True
                
        if not violations:
            break
            
        # Redistribute remaining stake among unconstrained selections
        unconstrained = [
            sel for sel in odds
            if min_stake[sel] < stakes[sel] < max_stake[sel]
        ]
        
        if not unconstrained:
            return None
            
        # Recalculate stakes for unconstrained selections
        unconstrained_odds = {sel: odds[sel] for sel in unconstrained}
        unconstrained_stakes = optimize_stakes_for_equal_profit(
            unconstrained_odds,
            remaining_stake
        )
        
        # Update stakes
        for sel in unconstrained:
            stakes[sel] = unconstrained_stakes[sel]
            
    # Validate final stakes
    if not validate_arbitrage_stakes(stakes, odds):
        return None
        
    return stakes

def calculate_position_exposure(
    positions: Dict[str, Dict[str, float]],  # Bookmaker -> {Market -> Stake}
    odds: Dict[str, Dict[str, float]]        # Bookmaker -> {Market -> Odds}
) -> Dict[str, float]:
    """Calculate current exposure at each bookmaker.
    
    This function calculates the maximum potential loss at each bookmaker
    considering all open positions.
    
    Args:
        positions: Nested dictionary of current positions
        odds: Nested dictionary of associated odds
    
    Returns:
        Dict[str, float]: Maximum exposure at each bookmaker
    """
    exposure = {}
    
    for book in positions:
        total_liability = 0
        total_stake = sum(positions[book].values())
        
        if total_stake > 0:
            max_payout = max(
                stake * odds[book][market]
                for market, stake in positions[book].items()
            )
            total_liability = max_payout - total_stake
            
        exposure[book] = total_liability
        
    return exposure

def calculate_stake_adjustments(
    target_stakes: Dict[str, float],
    current_positions: Dict[str, float],
    min_adjustment: float = 0.01
) -> Dict[str, float]:
    """Calculate required stake adjustments to reach target position.
    
    This function determines what bets need to be placed or laid to move from
    current positions to target positions, accounting for minimum bet sizes.
    
    Args:
        target_stakes: Target position sizes
        current_positions: Current position sizes
        min_adjustment: Minimum stake change to execute
    
    Returns:
        Dict[str, float]: Required stake adjustments (positive for back, negative for lay)
    """
    adjustments = {}
    
    for selection in set(target_stakes) | set(current_positions):
        target = target_stakes.get(selection, 0)
        current = current_positions.get(selection, 0)
        adjustment = target - current
        
        # Only include adjustments above minimum size
        if abs(adjustment) >= min_adjustment:
            adjustments[selection] = adjustment
            
    return adjustments
