# Odds Tracker Desktop

A desktop application for tracking betting odds and identifying arbitrage opportunities across multiple platforms. The application integrates with Betfair's API and scrapes data from OddsJet and Odds.com.au to find profitable betting opportunities.

## Features

- Real-time odds tracking from multiple sources:
  - Betfair Exchange API integration
  - OddsJet.com web scraping
  - Odds.com.au web scraping
- Automated arbitrage opportunity detection
- Kelly Criterion-based bet size calculation
- Real-time alerts for profitable opportunities
- User-friendly desktop interface
- Configurable alert thresholds
- Historical odds tracking and analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DrJonBrock/odds-tracker-desktop.git
cd odds-tracker-desktop
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

5. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
BETFAIR_API_KEY=your_api_key
BETFAIR_USERNAME=your_username
BETFAIR_PASSWORD=your_password
```

## Usage

1. Start the application:
```bash
python main.py
```

2. Configure data sources in the Settings panel:
   - Enter your Betfair API credentials
   - Enable/disable specific odds sources
   - Set update intervals

3. Monitor the dashboard for arbitrage opportunities:
   - View current odds across platforms
   - Monitor identified arbitrage opportunities
   - Configure alert thresholds

## Development

### Project Structure

```
odds-tracker-desktop/
├── src/                    # Source code
│   ├── data_collection/    # Odds data collection
│   ├── analysis/          # Arbitrage detection and analysis
│   ├── database/          # Database models and operations
│   └── ui/               # User interface components
├── tests/                 # Test files
└── main.py               # Application entry point
```

### Running Tests

```bash
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Please ensure you comply with all relevant laws and regulations in your jurisdiction regarding sports betting and gambling.