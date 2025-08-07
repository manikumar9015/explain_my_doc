// src/components/ChatBox.jsx

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import TextareaAutosize from 'react-textarea-autosize';
import { FaUserCircle, FaPaperPlane, FaRobot } from 'react-icons/fa';
import CodeBlock from './CodeBlock';

function ChatBox({ sessionId }) {
  const [messages, setMessages] = useState([
    { text: "Hello! I have read your document. Feel free to ask me any questions about it.", sender: 'ai' }
  ]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages, isLoading]);

  const handleSendMessage = async () => {
    if (!userInput.trim() || isLoading) return;

    const userMessage = { text: userInput, sender: 'user' };
    
    // Add the user message and an empty AI message placeholder
    setMessages(prev => [...prev, userMessage, { text: '', sender: 'ai' }]);
    setUserInput('');
    setIsLoading(true);

    try {
      // Use the Fetch API for streaming
      const response = await fetch('http://127.0.0.1:8000/query/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: userInput,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Read the stream
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break; // Stream finished
        }
        const chunk = decoder.decode(value, { stream: true });
        
        // Update the last message (the AI's placeholder) with the new chunk
        setMessages(prev => prev.map((msg, index) => 
          index === prev.length - 1 
            ? { ...msg, text: msg.text + chunk } 
            : msg
        ));
      }

    } catch (error) {
      console.error("Streaming failed:", error);
      setMessages(prev => prev.map((msg, index) => 
        index === prev.length - 1 
          ? { ...msg, text: 'Sorry, I encountered an error. Please try again.', isError: true } 
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="h-full flex flex-col w-full">
      <div className="flex-grow overflow-y-auto p-4">
        <div className="max-w-3xl mx-auto">
          {messages.map((msg, index) => (
            <div key={index} className={`flex items-start gap-4 p-4 my-2 rounded-lg ${msg.sender === 'user' ? 'bg-transparent' : 'bg-[#444654]'}`}>
              {msg.sender === 'ai' ? <FaRobot className="text-2xl text-white mt-1" /> : <FaUserCircle className="text-2xl text-sky-400 mt-1" />}
              <div className={`flex-1 pt-1 ${msg.isError ? 'text-red-400' : 'text-gray-100'}`}>
                <ReactMarkdown components={CodeBlock}>{msg.text}</ReactMarkdown>
              </div>
            </div>
          ))}
          {/* We no longer need the "Thinking..." bubble, the streaming is the indicator */}
          <div ref={chatEndRef} />
        </div>
      </div>
      <div className="w-full border-t border-gray-600 bg-[#343541] pt-4 pb-4">
        <div className="max-w-3xl mx-auto relative">
          <TextareaAutosize
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask a question about your document..."
            className="w-full bg-[#40414f] rounded-lg p-4 pr-12 text-gray-100 focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none shadow-lg"
            maxRows={5}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !userInput.trim()}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-sky-400 disabled:text-gray-600 disabled:cursor-not-allowed"
          >
            <FaPaperPlane className="text-xl" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatBox;