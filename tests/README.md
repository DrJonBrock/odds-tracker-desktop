# Odds Tracker Test Suite

This directory contains the comprehensive test suite for the Odds Tracker Desktop application. The tests are organized into unit tests and integration tests to ensure both component-level correctness and system-wide reliability.

## Test Structure

```
tests/
├── conftest.py           # Shared test fixtures and configuration
├── helpers.py            # Test helper functions and utilities
├── integration/          # Integration tests
│   ├── conftest.py       # Integration-specific fixtures
│   ├── test_ui.py        # UI integration tests
│   ├── test_data_collection.py    # Data collection tests
│   ├── test_arbitrage_detection.py # Arbitrage detection tests
│   └── test_error_handling.py      # Error handling and recovery tests
└── unit/                # Unit tests for individual components
```

## Running Tests

### All Tests
```bash
pytest tests/
```

### Integration Tests Only
```bash
pytest tests/integration/
```

### Specific Test Categories
```bash
pytest tests/integration/test_ui.py         # UI tests only
pytest tests/integration/test_error_handling.py  # Error handling tests only
```

## Test Categories

### Integration Tests

1. Data Collection Pipeline (`test_data_collection.py`)
   - Verifies odds collection from multiple sources
   - Tests database storage and data integrity
   - Validates data normalization

2. Arbitrage Detection (`test_arbitrage_detection.py`)
   - Tests complete pipeline from collection to opportunity detection
   - Verifies profit calculations
   - Validates opportunity storage

3. UI Integration (`test_ui.py`)
   - Tests data flow to user interface
   - Verifies real-time updates
   - Tests alert system

4. Error Handling (`test_error_handling.py`)
   - Tests system resilience during failures
   - Verifies error recovery mechanisms
   - Validates data consistency

## Test Fixtures

Key fixtures are provided in `conftest.py`:

1. `test_database`: In-memory SQLite database for testing
2. `mock_betfair_response`: Consistent mock data for Betfair API
3. `mock_oddsjet_data`: Mock data for OddsJet scraping
4. `qt_application`: QApplication instance for UI testing

## Helper Utilities

The `TestHelper` class in `helpers.py` provides utilities for:

- Creating test market entries
- Generating test odds data
- Verifying arbitrage opportunities
- Comparing odds data

## Writing New Tests

When adding new tests:

1. Use appropriate markers:
   ```python
   @pytest.mark.integration  # For integration tests
   @pytest.mark.asyncio      # For async tests
   ```

2. Follow the existing structure:
   - Keep related tests together
   - Use descriptive test names
   - Include detailed docstrings

3. Use helper utilities:
   ```python
   from tests.helpers import TestHelper
   helper = TestHelper()
   ```

4. Handle asynchronous operations:
   ```python
   async def test_async_operation():
       await operation()
       # Use qtbot.wait() for UI tests
   ```

## Maintenance Guidelines

1. Keep fixtures updated with changes to the application
2. Maintain test isolation using database fixtures
3. Update mock data to reflect API changes
4. Keep UI tests in sync with interface changes