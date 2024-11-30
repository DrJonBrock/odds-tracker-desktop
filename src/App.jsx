import React, { useState, useEffect } from 'react';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon, AlertCircle, PlusCircle } from 'lucide-react';

const OddsTracker = () => {
  const [events, setEvents] = useState([
    {
      id: 1,
      name: '',
      horse: { current: 0, previous: 0 },
      field: { current: 0, previous: 0 }
    }
  ]);

  const calculateImpliedProbability = (odds) => {
    if (odds > 0) {
      return (100 / (odds + 100)) * 100;
    } else {
      return (Math.abs(odds) / (Math.abs(odds) + 100)) * 100;
    }
  };

  const calculateDifferential = (horse, field) => {
    const horseProb = calculateImpliedProbability(horse);
    const fieldProb = calculateImpliedProbability(field);
    return Math.abs(horseProb - fieldProb);
  };

  const hasLargeVariance = (horse, field) => {
    return calculateDifferential(horse, field) > 10;
  };

  const getOddsTrend = (current, previous) => {
    if (current > previous) return <ArrowUpIcon className="w-4 h-4 text-red-500" />;
    if (current < previous) return <ArrowDownIcon className="w-4 h-4 text-green-500" />;
    return <MinusIcon className="w-4 h-4 text-gray-500" />;
  };

  const addEvent = () => {
    const name = prompt('Enter horse name:');
    if (!name) return;

    const horseOdds = Number(prompt('Enter horse odds:')) || 0;
    const fieldOdds = Number(prompt('Enter field odds:')) || 0;

    const newEvent = {
      id: events.length + 1,
      name,
      horse: { current: horseOdds, previous: horseOdds },
      field: { current: fieldOdds, previous: fieldOdds }
    };
    setEvents([...events, newEvent]);
  };

  const updateOdds = (eventId, type) => {
    const newOdds = prompt(`Enter new ${type} odds:`);
    if (!newOdds) return;

    setEvents(events.map(event => {
      if (event.id === eventId) {
        return {
          ...event,
          [type]: {
            previous: event[type].current,
            current: Number(newOdds)
          }
        };
      }
      return event;
    }));
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <div className="mb-6 bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">Horse vs Field Odds Tracker</h2>
            <button 
              onClick={addEvent}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 flex items-center gap-2"
            >
              <PlusCircle className="w-4 h-4" /> Add Horse
            </button>
          </div>
        </div>
        <div className="p-4">
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
                  const differential = calculateDifferential(event.horse.current, event.field.current);
                  const hasAlert = hasLargeVariance(event.horse.current, event.field.current);
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
                      <td 
                        className="p-2 border text-center cursor-pointer hover:bg-gray-50"
                        onClick={() => updateOdds(event.id, 'horse')}
                      >
                        <div className="flex items-center justify-center gap-2">
                          {event.horse.current}
                          {getOddsTrend(
                            event.horse.current,
                            event.horse.previous
                          )}
                        </div>
                      </td>
                      <td 
                        className="p-2 border text-center cursor-pointer hover:bg-gray-50"
                        onClick={() => updateOdds(event.id, 'field')}
                      >
                        <div className="flex items-center justify-center gap-2">
                          {event.field.current}
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