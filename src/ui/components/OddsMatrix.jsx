import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const OddsMatrix = () => {
  // This component will show a comparison matrix of odds across different platforms
  const platforms = ['Betfair', 'OddsJet', 'Odds.com.au'];
  const markets = [
    {
      id: 1,
      name: 'NBA - Warriors vs Lakers',
      odds: {
        'Betfair': 1.95,
        'OddsJet': 2.00,
        'Odds.com.au': 1.98
      }
    }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Odds Comparison Matrix</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Market</th>
                {platforms.map(platform => (
                  <th key={platform} className="text-right p-2">{platform}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {markets.map(market => (
                <tr key={market.id} className="border-b">
                  <td className="p-2">{market.name}</td>
                  {platforms.map(platform => (
                    <td key={platform} className="text-right p-2">
                      {market.odds[platform]?.toFixed(2) || '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};

export default OddsMatrix;