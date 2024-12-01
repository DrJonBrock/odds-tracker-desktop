from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

@dataclass
class ArbitrageOpportunity:
    """Represents a detected arbitrage opportunity across multiple bookmakers."""
    event_name: str
    market_type: str
    timestamp: datetime
    total_profit_percentage: float
    required_total_stake: float
    bets: List[Dict]  # List of individual bets to place
    risk_score: float  # 0-1 score indicating opportunity reliability
    sources: List[str]  # List of bookmakers involved

class ArbitrageDetector:
    """Analyzes odds from multiple sources to identify arbitrage opportunities.
    
    The detector uses sophisticated mathematical analysis to find cases where the
    combined odds from different bookmakers create a guaranteed profit opportunity.
    It considers factors like:
    - Margin calculation across all outcomes
    - Time sensitivity of opportunities
    - Liquidity requirements
    - Risk assessment of each bookmaker
    - Optimal stake distribution
    """
    
    def __init__(self, min_profit_percentage: float = 1.0,
                 max_stake: float = 1000.0,
                 min_liquidity_ratio: float = 2.0):
        self.logger = logging.getLogger(self.__name__)
        self.min_profit_percentage = min_profit_percentage
        self.max_stake = max_stake
        self.min_liquidity_ratio = min_liquidity_ratio
        
        # Store current opportunities
        self.current_opportunities = []
        
        # Track processed events to avoid duplicates
        self.processed_events = set()
        
        # Store callbacks for opportunity notifications
        self.opportunity_callbacks = []
        
        # Configure bookmaker reliability scores (0-1)
        self.bookmaker_reliability = {
            'betfair': 0.95,  # Most reliable due to exchange nature
            'oddsjet': 0.85,
            'oddscomau': 0.85
        }
    
    def register_opportunity_callback(self, callback):
        """Register a callback to be notified of new opportunities."""
        self.opportunity_callbacks.append(callback)
    
    async def analyze_odds(self, odds_data: Dict) -> List[ArbitrageOpportunity]:
        """Analyze new odds data to identify arbitrage opportunities."""
        try:
            # Group odds by event and market type
            grouped_odds = self._group_odds_by_event(odds_data)
            
            opportunities = []
            for event_key, event_odds in grouped_odds.items():
                # Skip if we've recently processed this event
                if self._is_recently_processed(event_key):
                    continue
                
                # Find arbitrage opportunities for this event
                event_opportunities = self._find_arbitrage(event_odds)
                
                # Validate and filter opportunities
                valid_opportunities = [
                    opp for opp in event_opportunities
                    if self._validate_opportunity(opp)
                ]
                
                opportunities.extend(valid_opportunities)
                
                # Mark event as processed
                self.processed_events.add(event_key)
            
            # Update current opportunities
            self.current_opportunities = opportunities
            
            # Notify callbacks
            for opportunity in opportunities:
                for callback in self.opportunity_callbacks:
                    await callback(opportunity)
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error analyzing odds: {str(e)}")
            return []
    
    def _find_arbitrage(self, event_odds: List[Dict]) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities within an event's odds.
        
        This is the core algorithm that identifies profitable betting combinations
        by analyzing the odds matrices and finding cases where the sum of inverse
        odds is less than 1, indicating an arbitrage opportunity.
        """
        opportunities = []
        
        try:
            # Create odds matrix for all outcomes and bookmakers
            odds_matrix = self._create_odds_matrix(event_odds)
            
            # Find best odds for each outcome
            best_odds = self._find_best_odds(odds_matrix)
            
            # Calculate inverse sum to check for arbitrage
            inverse_sum = sum(1/odd for odd in best_odds.values())
            
            if inverse_sum < 1:  # Arbitrage exists
                # Calculate profit percentage
                profit_percentage = ((1 / inverse_sum) - 1) * 100
                
                if profit_percentage >= self.min_profit_percentage:
                    # Calculate optimal stakes
                    total_stake = self.max_stake
                    stakes = self._calculate_stakes(best_odds, total_stake)
                    
                    # Create opportunity object
                    opportunity = ArbitrageOpportunity(
                        event_name=event_odds[0]['event_name'],
                        market_type=event_odds[0].get('market_type', 'match_odds'),
                        timestamp=datetime.utcnow(),
                        total_profit_percentage=profit_percentage,
                        required_total_stake=total_stake,
                        bets=[
                            {
                                'outcome': outcome,
                                'odds': odds,
                                'stake': stakes[outcome],
                                'source': best_odds['sources'][outcome]
                            }
                            for outcome, odds in best_odds.items()
                            if outcome != 'sources'
                        ],
                        risk_score=self._calculate_risk_score(best_odds['sources']),
                        sources=list(set(best_odds['sources'].values()))
                    )
                    
                    opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error finding arbitrage: {str(e)}")
            return []
    
    def _calculate_stakes(self, odds: Dict[str, float], total_stake: float) -> Dict[str, float]:
        """Calculate optimal stakes for each outcome.
        
        Uses the principle that each bet should return the same amount to ensure
        equal profit regardless of the outcome.
        """
        # Remove sources from odds dictionary for calculations
        betting_odds = {k: v for k, v in odds.items() if k != 'sources'}
        
        # Calculate the proportion for each outcome
        inverse_sum = sum(1/odd for odd in betting_odds.values())
        unit_stake = total_stake / inverse_sum
        
        return {
            outcome: unit_stake / odd
            for outcome, odd in betting_odds.items()
        }
    
    def _calculate_risk_score(self, sources: Dict[str, str]) -> float:
        """Calculate a risk score for the opportunity based on bookmaker reliability.
        
        Considers:
        1. Reliability scores of involved bookmakers
        2. Number of different bookmakers involved
        3. Time sensitivity of odds
        """
        # Get reliability scores for involved bookmakers
        reliability_scores = [self.bookmaker_reliability[source]
                            for source in sources.values()]
        
        # Calculate average reliability
        avg_reliability = sum(reliability_scores) / len(reliability_scores)
        
        # Adjust based on number of bookmakers (more bookmakers = higher risk)
        num_bookmakers = len(set(sources.values()))
        bookmaker_factor = 1 - (0.1 * (num_bookmakers - 1))  # Subtract 10% for each additional bookmaker
        
        return avg_reliability * bookmaker_factor
    
    def _validate_opportunity(self, opportunity: ArbitrageOpportunity) -> bool:
        """Validate an arbitrage opportunity by checking various risk factors."""
        try:
            # Check if profit percentage meets minimum threshold
            if opportunity.total_profit_percentage < self.min_profit_percentage:
                return False
            
            # Check if risk score is acceptable
            if opportunity.risk_score < 0.7:  # Minimum 70% confidence required
                return False
            
            # Verify liquidity is sufficient
            for bet in opportunity.bets:
                required_liquidity = bet['stake'] * self.min_liquidity_ratio
                if not self._verify_liquidity(bet['source'], required_liquidity):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating opportunity: {str(e)}")
            return False
    
    def _verify_liquidity(self, source: str, required_liquidity: float) -> bool:
        """Verify that a source has sufficient liquidity for the bet."""
        try:
            # For now, assume Betfair always has enough liquidity and others have limited
            if source == 'betfair':
                return True
            else:
                # For other sources, assume they can handle up to max_stake
                return required_liquidity <= self.max_stake
                
        except Exception as e:
            self.logger.error(f"Error verifying liquidity: {str(e)}")
            return False
