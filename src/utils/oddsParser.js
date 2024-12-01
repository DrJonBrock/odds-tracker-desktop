export const parseRaceData = (html) => {
  // Create a DOM parser
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');

  // Find the table rows containing horse data
  const rows = doc.querySelectorAll('tr[data-testid="horse-row"]');

  return Array.from(rows).map(row => {
    // Extract horse details
    const nameCell = row.querySelector('.horse-name');
    const number = nameCell?.getAttribute('data-number');
    const name = nameCell?.textContent?.trim();

    // Extract odds from different bookmakers
    const odds = {
      number: parseInt(number),
      name: name,
      sportsbet: parseFloat(row.querySelector('[data-bookmaker="sportsbet"]')?.textContent),
      bet365: parseFloat(row.querySelector('[data-bookmaker="bet365"]')?.textContent),
      tabtouch: parseFloat(row.querySelector('[data-bookmaker="tab"]')?.textContent),
      neds: parseFloat(row.querySelector('[data-bookmaker="neds"]')?.textContent),
      ladbrokes: parseFloat(row.querySelector('[data-bookmaker="ladbrokes"]')?.textContent)
    };

    // Calculate best odds
    const validOdds = Object.values(odds).filter(odd => !isNaN(odd) && typeof odd === 'number');
    odds.bestOdds = Math.max(...validOdds);

    return odds;
  });
};

export const calculateFieldOdds = (winOdds) => {
  // Convert winning odds to probability
  const winProb = 1 / winOdds;
  // Field probability is 1 - win probability
  const fieldProb = 1 - winProb;
  // Convert back to odds
  return 1 / fieldProb;
};
