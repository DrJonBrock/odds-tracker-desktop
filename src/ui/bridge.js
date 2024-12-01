// Bridge between React and Python

class PythonBridge {
  constructor() {
    this.listeners = new Map();
    
    // Set up listener for Python messages
    window.handlePythonMessage = this.handlePythonMessage.bind(this);
  }

  // Send message to Python
  sendToPython(channel, data) {
    if (window.pythonApi) {
      window.pythonApi.sendToPython(channel, data);
    } else {
      console.error('Python API not available');
    }
  }

  // Handle incoming messages from Python
  handlePythonMessage(message) {
    try {
      const { channel, data } = message;
      const listeners = this.listeners.get(channel) || [];
      
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in listener for channel ${channel}:`, error);
        }
      });
      
    } catch (error) {
      console.error('Error handling Python message:', error);
    }
  }

  // Subscribe to a channel
  subscribe(channel, callback) {
    if (!this.listeners.has(channel)) {
      this.listeners.set(channel, new Set());
    }
    this.listeners.get(channel).add(callback);
    
    return () => {
      const listeners = this.listeners.get(channel);
      if (listeners) {
        listeners.delete(callback);
      }
    };
  }
}

// Create singleton instance
const pythonBridge = new PythonBridge();
export default pythonBridge;