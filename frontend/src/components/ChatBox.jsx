// src/components/ChatBox.jsx

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
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
    setMessages(prev => [...prev, userMessage]);
    setUserInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:8000/query/', {
        session_id: sessionId,
        question: userInput,
      });
      const aiMessage = { text: response.data.answer, sender: 'ai' };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = { text: 'Sorry, I encountered an error. Please try again.', sender: 'ai', isError: true };
      setMessages(prev => [...prev, errorMessage]);
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
    // This is the root container of the ChatBox. The h-full class is the fix.
    <div className="h-full flex flex-col w-full">
      
      {/* Message Display Area: It now grows to fill available space */}
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
          {isLoading && (
            <div className="flex items-start gap-4 p-4 my-2 bg-[#444654] rounded-lg">
              <FaRobot className="text-2xl text-white mt-1" />
              <div className="flex-1 pt-1 text-gray-100 animate-pulse">Thinking...</div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Input Area: A separate footer, locked to the bottom */}
      <div className="w-full border-t border-gray-600 bg-[#343541] pt-4 pb-4">
        <div className="max-w-3xl mx-auto relative">
          <TextareaAutosize
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask a question about your document..."
            className="w-full bg-[#40414f] rounded-lg p-4 pr-12 text-gray-100 focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none shadow-lg"
            maxRows={5}
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