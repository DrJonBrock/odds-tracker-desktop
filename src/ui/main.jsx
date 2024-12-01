import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/globals.css';

// Create a root element for our React application
const root = ReactDOM.createRoot(document.getElementById('root'));

// Render our application
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);