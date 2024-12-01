# UI Components

This directory contains the React components for the Odds Tracker Desktop application's user interface.

## Component Overview

### Dashboard.jsx
The main dashboard component that provides an overview of current arbitrage opportunities and key metrics.

### OddsMatrix.jsx
A component for comparing odds across different platforms in a matrix format.

### AlertSettings.jsx
Configuration component for setting up alerts and notifications.

## Development Status

These components are part of the initial UI implementation. Future updates will include:

- Position management interface
- Advanced settings panel
- Real-time data visualization
- Mobile responsive layouts

## Usage

Components are built using React with Tailwind CSS for styling. They require the following dependencies:

- @/components/ui/* (shadcn/ui components)
- lucide-react (for icons)
- recharts (for charts and visualizations)

## Contributing

When adding new components:

1. Follow the existing component structure
2. Use Tailwind CSS for styling
3. Implement responsive design
4. Add appropriate documentation
5. Include prop-types or TypeScript interfaces