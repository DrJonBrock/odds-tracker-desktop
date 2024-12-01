import React, { useState, useEffect } from 'react';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon, AlertCircle, PlusCircle, RefreshCw } from 'lucide-react';
import { fetch } from '@tauri-apps/api/http';
import { parseRaceData, calculateFieldOdds } from './utils/oddsParser';

const OddsTracker = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [raceUrl, setRaceUrl] = useState('');
  const [error, setError] = useState('');

  const parseOddsData = (data) => {
    return data.map(horse => ({
      id: horse.number,
      name: horse.name,
      horse: {
        current: horse.bestOdds,
        previous: events.find(e => e.name === horse.name)?.horse.current || horse.bestOdds
      },
      field: {
        current: calculateFieldOdds(horse.bestOdds),
        previous: events.find(e => e.name === horse.name)?.field.current || calculateFieldOdds(horse.bestOdds)
      }
    }));
  };

  const fetchOdds = async (url) => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(url);
      const data = await response.text();
      const parsedData = parseRaceData(data);
      const processedOdds = parseOddsData(parsedData);
      setEvents(processedOdds);
    } catch (error) {
      console.error('Error fetching odds:', error);
      setError('Failed to fetch odds. Please check the URL and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUrlSubmit = (e) => {
    e.preventDefault();
    if (raceUrl) {
      fetchOdds(raceUrl);
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <div className="mb-6 bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <form onSubmit={handleUrlSubmit} className="mb-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={raceUrl}
                onChange={(e) => setRaceUrl(e.target.value)}
                placeholder="Enter odds.com.au race URL"
                className="flex-1 p-2 border rounded"
              />
              <button 
                type="submit"
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center gap-2"
                disabled={loading}
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}}`} />
                Fetch Odds
              </button>
            </div>
          </form>
          
          {error && (
            <div className="p-2 mb-4 text-red-700 bg-red-100 rounded">
              {error}
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="p-2 border text-left">Horse</th>
                  <th className="p-2 border text-center">Horse Odds</th>
                  <th className="p-2 border text-center">Field Odds</th>
                  <th className="p-2 border text-center">Probability Differential</th>
                </tr>
              </thead>
              <tbody>
                {events.map(event => {
                  const horseProb = (1 / event.horse.current) * 100;
                  const fieldProb = (1 / event.field.current) * 100;
                  const differential = Math.abs(horseProb - fieldProb);
                  const hasAlert = differential > 10;

                  return (
                    <tr key={event.id} className={hasAlert ? "bg-yellow-50" : ""}>
                      <td className="p-2 border font-medium">
                        <div className="flex items-center gap-2">
                          {event.name}
                          {hasAlert && (
                            <AlertCircle className="w-4 h-4 text-yellow-500" />
                          )}
                        </div>
                      </td>
                      <td className="p-2 border text-center">
                        <div className="flex items-center justify-center gap-2">
                          {event.horse.current.toFixed(2)}
                          {getOddsTrend(
                            event.horse.current,
                            event.horse.previous
                          )}
                        </div>
                      </td>
                      <td className="p-2 border text-center">
                        <div className="flex items-center justify-center gap-2">
                          {event.field.current.toFixed(2)}
                          {getOddsTrend(
                            event.field.current,
                            event.field.previous
                          )}
                        </div>
                      </td>
                      <td className="p-2 border text-center">
                        {differential.toFixed(1)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OddsTracker;
