import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Bell, Settings, TrendingUp, Wallet } from 'lucide-react';
import { usePythonBridge } from '../hooks/usePythonBridge';
import OddsMatrix from './OddsMatrix';
import AlertSettings from './AlertSettings';

const Dashboard = () => {
  const [opportunities, setOpportunities] = useState([]);
  const [activeOpportunities, setActiveOpportunities] = useState(0);
  const [totalProfit, setTotalProfit] = useState(0);
  const [error, setError] = useState(null);

  // Subscribe to Python messages
  usePythonBridge('odds_update', (data) => {
    console.log('Received odds update:', data);
    // Update OddsMatrix component
  });

  usePythonBridge('new_opportunity', (data) => {
    console.log('Received new opportunity:', data);
    setOpportunities(prev => [...prev, data]);
    setActiveOpportunities(prev => prev + 1);
  });

  usePythonBridge('error', (data) => {
    console.error('Received error:', data);
    setError(data.message);
  });

  // Send settings updates to Python
  const sendToPython = usePythonBridge('alert_settings');
  
  const handleSettingsChange = (settings) => {
    sendToPython(settings);
  };

  return (
    <div className="p-4 max-w-7xl mx-auto">
      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <div className="text-2xl font-bold">{activeOpportunities}</div>
            </div>
            <p className="text-sm text-gray-500">Active Opportunities</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Wallet className="h-4 w-4 text-blue-500" />
              <div className="text-2xl font-bold">${totalProfit.toLocaleString()}</div>
            </div>
            <p className="text-sm text-gray-500">Total Profit Today</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="opportunities" className="space-y-4">
        <TabsList>
          <TabsTrigger value="opportunities">Opportunities</TabsTrigger>
          <TabsTrigger value="matrix">Odds Matrix</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="opportunities">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Current Arbitrage Opportunities</span>
                <Bell className="h-4 w-4" />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Market</th>
                      <th className="text-right p-2">Profit %</th>
                      <th className="text-right p-2">Required Stake</th>
                      <th className="text-left p-2">Platforms</th>
                    </tr>
                  </thead>
                  <tbody>
                    {opportunities.map(opp => (
                      <tr key={opp.id} className="border-b">
                        <td className="p-2">{opp.market}</td>
                        <td className="text-right p-2 text-green-500">
                          {opp.profit.toFixed(2)}%
                        </td>
                        <td className="text-right p-2">
                          ${opp.requiredStake.toLocaleString()}
                        </td>
                        <td className="p-2">{opp.platforms.join(', ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="matrix">
          <OddsMatrix />
        </TabsContent>

        <TabsContent value="alerts">
          <AlertSettings onSettingsChange={handleSettingsChange} />
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <h3 className="font-medium">Data Sources</h3>
                  <div className="space-y-1">
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" className="rounded" defaultChecked />
                      <span>Betfair Exchange</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" className="rounded" defaultChecked />
                      <span>OddsJet</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" className="rounded" defaultChecked />
                      <span>Odds.com.au</span>
                    </label>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;