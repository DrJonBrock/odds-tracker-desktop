import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';

const App = () => {
    // Track whether our Python bridge is ready
    const [bridgeReady, setBridgeReady] = useState(false);

    useEffect(() => {
        // Listen for the Python bridge to become ready
        window.addEventListener('python_bridge_ready', () => {
            console.log('Python bridge is ready');
            setBridgeReady(true);
        });

        // Listen for messages from Python
        window.addEventListener('python_message', (event) => {
            const { type, payload } = event.detail;
            console.log('Received message from Python:', type, payload);
            // We'll handle different message types here later
        });
    }, []);

    if (!bridgeReady) {
        return <div>Loading...</div>;
    }

    return <Dashboard />;
};

export default App;