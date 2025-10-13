import { useEffect, useCallback } from 'react';
import pythonBridge from '../bridge';

// React hook for communicating with Python
export function usePythonBridge(channel, callback) {
  useEffect(() => {
    // Subscribe to channel
    const unsubscribe = pythonBridge.subscribe(channel, callback);
    
    // Cleanup subscription
    return () => unsubscribe();
  }, [channel, callback]);

  // Return function to send messages to Python
  const sendToPython = useCallback(
    (data) => pythonBridge.sendToPython(channel, data),
    [channel]
  );

  return sendToPython;
}
