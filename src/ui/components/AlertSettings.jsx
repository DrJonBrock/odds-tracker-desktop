import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const AlertSettings = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Alert Configuration</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium mb-2">Minimum Profit Threshold</h3>
            <input 
              type="number" 
              className="w-full p-2 border rounded"
              defaultValue={2.0}
              step={0.1}
            />
          </div>
          
          <div>
            <h3 className="text-sm font-medium mb-2">Notification Types</h3>
            <div className="space-y-2">
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" defaultChecked />
                <span>Desktop Notifications</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" defaultChecked />
                <span>Sound Alerts</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" />
                <span>Email Notifications</span>
              </label>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AlertSettings;