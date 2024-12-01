"""Unit tests for bet size calculator utility functions.

These tests verify the behavior of the utility functions that support our bet size
calculator. We test both normal operation and edge cases to ensure robust
performance in production.
"""

import unittest
from datetime import datetime
from decimal import Decimal
from src.analysis.bet_size.utils import (
    normalize_odds,
    calculate_implied_probability,
    validate_arbitrage_stakes,
    calculate_optimal_stakes,
    calculate_position_exposure,
    calculate_stake_adjustments
)

class TestOddsNormalization(unittest.TestCase):
    """Test the odds format normalization function.
    
    These tests verify that we can correctly convert between different odds
    formats (decimal, fractional, American) while maintaining accuracy.
    """
    
    def test_decimal_odds_unchanged(self):
        """Decimal odds should remain unchanged when normalized."""
        self.assertEqual(normalize_odds(2.0, 'decimal'), 2.0)
        self.assertEqual(normalize_odds(1.5, 'decimal'), 1.5)
        
    def test_fractional_odds_conversion(self):
        """Fractional odds should convert correctly to decimal format."""
        test_cases = [
            ('5/2', 3.5),  # 5/2 = 2.5 + 1 = 3.5
            ('1/1', 2.0),  # Evens
            ('2/7', 1.286),  # Rounded for floating point comparison
        ]
        
        for fractional, expected in test_cases:
            with self.subTest(odds=fractional):
                result = normalize_odds(fractional, 'fractional')
                self.assertAlmostEqual(result, expected, places=3)
                
    def test_american_odds_conversion(self):
        """American odds should convert correctly to decimal format."""
        test_cases = [
            (+150, 2.5),    # Positive odds (underdog)
            (-200, 1.5),    # Negative odds (favorite)
            (+100, 2.0),    # Even odds positive
            (-100, 2.0),    # Even odds negative
        ]
        
        for american, expected in test_cases:
            with self.subTest(odds=american):
                result = normalize_odds(american, 'american')
                self.assertAlmostEqual(result, expected, places=3)
                
    def test_invalid_format_raises_error(self):
        """Should raise ValueError for unsupported formats."""
        with self.assertRaises(ValueError):
            normalize_odds(2.0, 'unsupported_format')

class TestArbitrageValidation(unittest.TestCase):
    """Test the arbitrage stake validation function.
    
    These tests verify that we can correctly identify valid arbitrage
    opportunities and reject invalid ones.
    """
    
    def test_valid_arbitrage_opportunity(self):
        """Should return True for a valid arbitrage opportunity."""
        # Example: 2.0, 3.0 odds with properly balanced stakes
        stakes = {'A': 60.0, 'B': 40.0}
        odds = {'A': 2.0, 'B': 3.0}
        
        self.assertTrue(
            validate_arbitrage_stakes(
                stakes,
                odds,
                min_profit_rate=0.01
            )
        )
        
    def test_invalid_stakes_negative(self):
        """Should return False for negative stakes."""
        stakes = {'A': -10.0, 'B': 100.0}
        odds = {'A': 2.0, 'B': 3.0}
        
        self.assertFalse(
            validate_arbitrage_stakes(stakes, odds)
        )
        
    def test_insufficient_profit_rate(self):
        """Should return False when profit rate is below minimum."""
        # Stakes that produce very small profit
        stakes = {'A': 50.0, 'B': 50.0}
        odds = {'A': 2.01, 'B': 2.01}  # Small positive EV
        
        self.assertFalse(
            validate_arbitrage_stakes(
                stakes,
                odds,
                min_profit_rate=0.02  # Require 2% profit
            )
        )

class TestOptimalStakeCalculation(unittest.TestCase):
    """Test the optimal stake calculation function.
    
    These tests verify that we can find valid stake distributions that
    maximize profit while respecting constraints.
    """
    
    def test_basic_stake_optimization(self):
        """Should find optimal stakes for simple two-outcome case."""
        odds = {'A': 2.0, 'B': 3.0}
        total_stake = 100.0
        
        stakes = calculate_optimal_stakes(odds, total_stake)
        
        self.assertIsNotNone(stakes)
        self.assertEqual(len(stakes), 2)
        
        # Verify stakes sum to total
        self.assertAlmostEqual(sum(stakes.values()), total_stake, places=2)
        
        # Verify profits are equal (within tolerance)
        profit_a = stakes['A'] * odds['A'] - total_stake
        profit_b = stakes['B'] * odds['B'] - total_stake
        self.assertAlmostEqual(profit_a, profit_b, places=2)
        
    def test_stake_constraints(self):
        """Should respect minimum and maximum stake constraints."""
        odds = {'A': 2.0, 'B': 3.0}
        total_stake = 100.0
        min_stake = {'A': 30.0, 'B': 20.0}
        max_stake = {'A': 70.0, 'B': 60.0}
        
        stakes = calculate_optimal_stakes(
            odds,
            total_stake,
            min_stake=min_stake,
            max_stake=max_stake
        )
        
        self.assertIsNotNone(stakes)
        
        # Verify constraints are respected
        for sel in stakes:
            self.assertGreaterEqual(stakes[sel], min_stake[sel])
            self.assertLessEqual(stakes[sel], max_stake[sel])
            
    def test_impossible_constraints(self):
        """Should return None when constraints cannot be satisfied."""
        odds = {'A': 2.0, 'B': 3.0}
        total_stake = 100.0
        
        # Impossible constraints - minimum stakes sum to more than total
        min_stake = {'A': 60.0, 'B': 50.0}
        
        stakes = calculate_optimal_stakes(
            odds,
            total_stake,
            min_stake=min_stake
        )
        
        self.assertIsNone(stakes)

class TestExposureCalculation(unittest.TestCase):
    """Test the position exposure calculation function.
    
    These tests verify that we can correctly calculate potential liability
    across different bookmakers.
    """
    
    def test_single_book_exposure(self):
        """Should calculate correct exposure for single book."""
        positions = {
            'BookA': {'Market1': 100.0}
        }
        odds = {
            'BookA': {'Market1': 2.0}
        }
        
        exposure = calculate_position_exposure(positions, odds)
        
        self.assertEqual(len(exposure), 1)
        self.assertEqual(exposure['BookA'], 100.0)  # Maximum liability
        
    def test_multiple_books_exposure(self):
        """Should calculate correct exposure across multiple books."""
        positions = {
            'BookA': {'Market1': 100.0, 'Market2': 50.0},
            'BookB': {'Market1': 75.0}
        }
        odds = {
            'BookA': {'Market1': 2.0, 'Market2': 3.0},
            'BookB': {'Market1': 2.5}
        }
        
        exposure = calculate_position_exposure(positions, odds)
        
        self.assertEqual(len(exposure), 2)
        
        # Verify maximum liability calculations
        expected_exposure_a = max(
            100.0 * 2.0,  # Market1 payout
            50.0 * 3.0    # Market2 payout
        ) - 150.0  # Total stake at BookA
        
        expected_exposure_b = (75.0 * 2.5) - 75.0  # BookB liability
        
        self.assertAlmostEqual(exposure['BookA'], expected_exposure_a)
        self.assertAlmostEqual(exposure['BookB'], expected_exposure_b)

class TestStakeAdjustments(unittest.TestCase):
    """Test the stake adjustment calculation function.
    
    These tests verify that we can correctly determine what bets need to be
    placed to move from current positions to target positions.
    """
    
    def test_basic_adjustments(self):
        """Should calculate correct adjustments for simple case."""
        current = {'A': 50.0, 'B': 30.0}
        target = {'A': 70.0, 'B': 20.0}
        
        adjustments = calculate_stake_adjustments(target, current)
        
        self.assertEqual(adjustments['A'], 20.0)  # Need to increase A
        self.assertEqual(adjustments['B'], -10.0)  # Need to decrease B
        
    def test_minimum_adjustment_threshold(self):
        """Should ignore adjustments below minimum threshold."""
        current = {'A': 50.0, 'B': 30.0}
        target = {'A': 50.1, 'B': 29.95}  # Small changes
        
        adjustments = calculate_stake_adjustments(
            target,
            current,
            min_adjustment=0.2  # Ignore changes smaller than 0.2
        )
        
        self.assertEqual(len(adjustments), 0)  # No significant adjustments
        
    def test_new_position(self):
        """Should handle creating entirely new positions."""
        current = {'A': 50.0}
        target = {'A': 50.0, 'B': 30.0}  # Adding new position B
        
        adjustments = calculate_stake_adjustments(target, current)
        
        self.assertEqual(len(adjustments), 1)
        self.assertEqual(adjustments['B'], 30.0)

if __name__ == '__main__':
    unittest.main()