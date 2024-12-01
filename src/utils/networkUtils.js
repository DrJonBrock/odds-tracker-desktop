// These network utilities help us make proper web requests to odds.com.au
// By including these headers, we make our requests look like they're coming from a regular web browser

export const fetchOptions = {
  headers: {
    // This identifies our request as coming from a modern Chrome browser
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    // This tells the server what types of content we can handle
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    // This indicates our language preference
    'Accept-Language': 'en-US,en;q=0.5',
    // This tells the server which site referred us
    'Referer': 'https://www.odds.com.au'
  }
};