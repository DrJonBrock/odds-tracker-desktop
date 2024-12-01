import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Dashboard from '../Dashboard';
import { pythonBridge } from '../../bridge';

// Mock the Python bridge
jest.mock('../../bridge', () => ({
  pythonBridge: {
    sendToPython: jest.fn(),
    subscribe: jest.fn(),
  }
}));

describe('Dashboard Component Integration', () => {
  beforeEach(() => {
    // Clear mock data before each test
    jest.clearAllMocks();
    
    // Set up default subscription behavior
    pythonBridge.subscribe.mockImplementation((channel, callback) => {
      return () => {}; // Return cleanup function
    });
  });

  it('subscribes to necessary Python channels on mount', () => {
    render(<Dashboard />);
    
    // Verify subscriptions were created for all required channels
    expect(pythonBridge.subscribe).toHaveBeenCalledWith(
      'odds_update',
      expect.any(Function)
    );
    expect(pythonBridge.subscribe).toHaveBeenCalledWith(
      'new_opportunity',
      expect.any(Function)
    );
    expect(pythonBridge.subscribe).toHaveBeenCalledWith(
      'error',
      expect.any(Function)
    );
  });

  it('updates opportunities when receiving new opportunity message', async () => {
    // Capture the callback function when component subscribes
    let opportunityCallback;
    pythonBridge.subscribe.mockImplementation((channel, callback) => {
      if (channel === 'new_opportunity') {
        opportunityCallback = callback;
      }
      return () => {};
    });

    render(<Dashboard />);

    // Simulate receiving a new opportunity
    const testOpportunity = {
      id: 1,
      market: 'Test Market',
      profit: 2.5,
      requiredStake: 1000,
      platforms: ['Platform A', 'Platform B']
    };

    opportunityCallback(testOpportunity);

    // Verify the opportunity is displayed
    await waitFor(() => {
      expect(screen.getByText('Test Market')).toBeInTheDocument();
      expect(screen.getByText('2.50%')).toBeInTheDocument();
      expect(screen.getByText('$1,000')).toBeInTheDocument();
      expect(screen.getByText('Platform A, Platform B')).toBeInTheDocument();
    });
  });

  it('displays error messages when receiving error channel message', async () => {
    // Capture error callback
    let errorCallback;
    pythonBridge.subscribe.mockImplementation((channel, callback) => {
      if (channel === 'error') {
        errorCallback = callback;
      }
      return () => {};
    });

    render(<Dashboard />);

    // Simulate receiving an error
    errorCallback({
      message: 'Test error message',
      timestamp: '2024-01-01T12:00:00Z'
    });

    // Verify error is displayed
    await waitFor(() => {
      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });
  });

  it('sends settings updates to Python when changed', async () => {
    render(<Dashboard />);

    // Navigate to settings tab
    fireEvent.click(screen.getByText('Settings'));

    // Toggle a data source
    const betfairCheckbox = screen.getByLabelText('Betfair Exchange');
    fireEvent.click(betfairCheckbox);

    // Verify message was sent to Python
    expect(pythonBridge.sendToPython).toHaveBeenCalledWith(
      'alert_settings',
      expect.any(Object)
    );
  });

  it('updates odds matrix when receiving odds update', async () => {
    // Capture odds update callback
    let oddsCallback;
    pythonBridge.subscribe.mockImplementation((channel, callback) => {
      if (channel === 'odds_update') {
        oddsCallback = callback;
      }
      return () => {};
    });

    render(<Dashboard />);

    // Navigate to matrix tab
    fireEvent.click(screen.getByText('Odds Matrix'));

    // Simulate receiving odds update
    const testOdds = {
      market: 'Test Market',
      platform: 'Test Platform',
      odds: 1.95
    };

    oddsCallback(testOdds);

    // Verify odds are displayed in matrix
    await waitFor(() => {
      expect(screen.getByText('1.95')).toBeInTheDocument();
    });
  });
});
