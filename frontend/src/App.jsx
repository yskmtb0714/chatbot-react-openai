import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css'; // Import CSS file

function App() {
  // State for the input message
  const [message, setMessage] = useState('');
  // State for the chat history (array of objects)
  const [chatHistory, setChatHistory] = useState([]);
  // State for loading indicator
  const [isLoading, setIsLoading] = useState(false);
  // Ref for the chat history container (for scrolling)
  const chatHistoryRef = useRef(null);

  // Async function to handle sending messages
  const sendMessage = async () => {
    const userMessageText = message.trim(); // Use state variable directly
    // Do nothing if message is empty or already loading
    if (userMessageText === '' || isLoading) return;

    // 1. Add user message to history using functional update
    setChatHistory(prevHistory => [
      ...prevHistory,
      { sender: 'user', text: userMessageText, type: 'message' }
    ]);
    console.log('User message added to history state:', userMessageText);

    // Clear input field AFTER getting its value
    setMessage('');
    setIsLoading(true); // Start loading
    console.log("Set loading: true"); // Debug log

    try {
      // 2. Call backend API
      console.log(`Sending query to backend: ${userMessageText}`); // Use the correct variable
      const response = await axios.post('http://localhost:5000/chat', {
        query: userMessageText
      });
      console.log('Received response from backend:', response.data);

      // 3. Add AI response or backend error to history
      let aiResponse = { sender: 'ai', text: 'Received an unexpected response format from the server.', type: 'error' }; // Default error
      if (response.data && response.data.response) {
        // Success response
        aiResponse = { sender: 'ai', text: response.data.response, type: 'message' };
      } else if (response.data && response.data.error) {
        // Backend returned error in JSON
        console.error("Backend returned an error:", response.data.error);
        aiResponse = { sender: 'ai', text: `Error from backend: ${response.data.error}`, type: 'error' };
      } else {
        // Unexpected response format
        console.error("Unexpected response format from backend:", response.data);
      }
      setChatHistory(prevHistory => [...prevHistory, aiResponse]);
      console.log('AI/Error message added to history state'); // Debug log

    } catch (error) {
      // 4. Handle API call failure (network error, etc.)
      console.error('API call error:', error);
      let errorMessage = 'An error occurred while contacting the server.';
       if (error.response) {
         errorMessage = `Server error (Status: ${error.response.status})`;
       } else if (error.request) {
         errorMessage = 'No response from server. Is the backend running?';
       }
      // Add error message to history
      setChatHistory(prevHistory => [
        ...prevHistory,
        { sender: 'ai', text: errorMessage, type: 'error' }
      ]);
      console.log('Network/Request error message added to history state'); // Debug log
    } finally {
      // 5. Finish loading (regardless of success/failure)
      setIsLoading(false);
      console.log("Set loading: false"); // Debug log
    }
  };

  // Handle Enter key press
  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !isLoading) { // Use isLoading directly
      sendMessage();
    }
  };

  // Scroll to bottom when chatHistory changes
  useEffect(() => {
    // ★ Add console log here to check if state update triggers effect ★
    console.log("Chat history state (inside useEffect):", chatHistory);

    if (chatHistoryRef.current) {
      const { scrollHeight } = chatHistoryRef.current;
      chatHistoryRef.current.scrollTo({ top: scrollHeight, behavior: 'smooth' });
      console.log('JS Scrolled to bottom attempt. Target scrollHeight:', scrollHeight);
    }
  }, [chatHistory]); // Dependency array is correct

  // --- JSX for rendering ---
  console.log("Rendering App component. History length:", chatHistory.length); // ★ Add render log ★
  return (
    <div className="app-container">
      <h1>AI Chatbot MVP (React)</h1>

      <div className="chat-history" ref={chatHistoryRef}>
        {chatHistory.length === 0 && !isLoading && (
          <div className="no-messages">
            Enter a message below to start...
          </div>
        )}

        {/* Render chat history */}
        {chatHistory.map((msg, index) => {
           // ★ Add log inside map to see if it iterates ★
           console.log(`Rendering message index ${index}, sender: ${msg.sender}`); 
           return (
             <div key={index}
                  className={`message-wrapper ${msg.sender === 'user' ? 'user-wrapper' : 'ai-wrapper'}`}>
               <div className={`message ${
                                msg.sender === 'user' ? 'user-message' : 'ai-message'} ${
                                msg.type === 'error' ? 'error-message' : ''
                              }`}>
                 <span className="text" style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</span>
               </div>
             </div>
           );
        })}

        {/* Loading Indicator */}
        {isLoading && (
            <div className="message-wrapper ai-wrapper loading-indicator">
                <div className="message ai-message loading-message">
                    <div className="spinner"></div>
                    <span className="text loading-text">AI is thinking...</span>
                </div>
            </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-area">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter your message..."
          onKeyUp={handleKeyPress}
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
  // --- End JSX ---
}

export default App;