from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import numpy as np

def create_odds_matrix(event_odds: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    Create a matrix of odds for each outcome and bookmaker.
    
    Args:
        event_odds: List of odds data from different sources for an event
        
    Returns:
        Dictionary mapping outcomes to bookmakers and their odds
    """
    matrix = defaultdict(dict)
    
    for source_data in event_odds:
        source = source_data['source']
        for outcome_data in source_data['odds']:
            outcome = outcome_data['outcome']
            odds = outcome_data['odds']
            matrix[outcome][source] = odds
    
    return matrix

def find_best_odds(odds_matrix: Dict[str, Dict[str, float]]) -> Dict[str, Tuple[float, str]]:
    """
    Find the best (highest) odds for each outcome across all bookmakers.
    
    Args:
        odds_matrix: Matrix of odds for each outcome and bookmaker
        
    Returns:
        Dictionary mapping outcomes to their best odds and source
    """
    best_odds = {}
    sources = {}
    
    for outcome, bookmaker_odds in odds_matrix.items():
        if bookmaker_odds:  # Check if we have any odds for this outcome
            best_odds[outcome] = max(bookmaker_odds.values())
            sources[outcome] = max(bookmaker_odds.items(), key=lambda x: x[1])[0]
    
    # Include sources in the result
    best_odds['sources'] = sources
    return best_odds

def calculate_kelly_stake(odds: float, probability: float, bankroll: float) -> float:
    """
    Calculate the optimal stake using the Kelly Criterion.
    
    Args:
        odds: Decimal odds for the bet
        probability: Estimated true probability of the outcome
        bankroll: Current bankroll size
        
    Returns:
        Optimal stake size
    """
    if odds <= 1 or probability <= 0 or probability >= 1:
        return 0
    
    # Kelly formula: f* = (bp - q)/b
    # where: b = odds - 1, p = probability of win, q = probability of loss
    b = odds - 1
    q = 1 - probability
    
    kelly_fraction = (b * probability - q) / b
    
    # Limit stake to a maximum of 10% of bankroll for risk management
    return min(kelly_fraction * bankroll, bankroll * 0.1)

def estimate_true_probability(bookmaker_odds: List[float]) -> float:
    """
    Estimate the true probability of an outcome using odds from multiple bookmakers.
    
    Args:
        bookmaker_odds: List of odds from different bookmakers
        
    Returns:
        Estimated true probability
    """
    # Convert odds to implied probabilities
    implied_probs = [1/odd for odd in bookmaker_odds]
    
    # Remove average bookmaker margin
    total_probability = sum(implied_probs)
    margin_factor = total_probability / len(implied_probs)
    
    # Take weighted average of normalized probabilities
    normalized_probs = [p/margin_factor for p in implied_probs]
    return sum(normalized_probs) / len(normalized_probs)

def calculate_arbitrage_profit(stakes: List[float], odds: List[float]) -> float:
    """
    Calculate the profit for an arbitrage bet.
    
    Args:
        stakes: List of stakes for each outcome
        odds: List of corresponding odds
        
    Returns:
        Guaranteed profit amount
    """
    total_stake = sum(stakes)
    potential_returns = [stake * odd for stake, odd in zip(stakes, odds)]
    
    # All potential returns should be equal in a properly structured arbitrage
    guaranteed_return = min(potential_returns)
    return guaranteed_return - total_stake

def verify_opportunity_timing(odds_timestamps: List[datetime], 
                            max_age_seconds: int = 30) -> bool:
    """
    Verify that all odds in an opportunity are fresh enough.
    
    Args:
        odds_timestamps: List of timestamps for each odds quote
        max_age_seconds: Maximum allowed age of odds in seconds
        
    Returns:
        True if all odds are fresh enough, False otherwise
    """
    current_time = datetime.utcnow()
    return all(
        (current_time - timestamp).total_seconds() <= max_age_seconds
        for timestamp in odds_timestamps
    )
