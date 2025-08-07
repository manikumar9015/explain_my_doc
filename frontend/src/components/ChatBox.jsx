// frontend/src/components/ChatBox.jsx

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import TextareaAutosize from 'react-textarea-autosize';
import { FaUserCircle, FaPaperPlane, FaRobot, FaBook } from 'react-icons/fa';
import CodeBlock from './CodeBlock';
import Modal from 'react-modal';

Modal.setAppElement('#root');

function ChatBox({ sessionId }) {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I have read your document. What would you like to know?", sender: 'ai', sources: [] }
  ]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const [currentSources, setCurrentSources] = useState([]);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(scrollToBottom, [messages, isLoading]);

  const openSourcesModal = (sources) => {
    setCurrentSources(sources);
    setModalIsOpen(true);
  };

  const handleSendMessage = async () => {
    if (!userInput.trim() || isLoading) return;

    const userMessage = { id: Date.now(), text: userInput, sender: 'user', sources: [] };
    const aiPlaceholder = { id: Date.now() + 1, text: '', sender: 'ai', sources: [] };
    
    const historyForAPI = messages.slice(-4).map(msg => ({
      sender: msg.sender,
      text: msg.text
    }));

    setMessages(prev => [...prev, userMessage, aiPlaceholder]);
    setUserInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/query/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question: userInput,
          chat_history: historyForAPI,
        }),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      const sourcesHeader = response.headers.get('X-Source-Chunks');
      const decodedSources = sourcesHeader ? JSON.parse(atob(sourcesHeader)) : [];

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let finalAnswer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        finalAnswer += chunk;
        setMessages(prev => prev.map(msg => 
          msg.id === aiPlaceholder.id ? { ...msg, text: finalAnswer } : msg
        ));
      }

      setMessages(prev => prev.map(msg =>
        msg.id === aiPlaceholder.id ? { ...msg, text: finalAnswer, sources: decodedSources } : msg
      ));

    } catch (error) {
      console.error("Streaming/history request failed:", error);
      setMessages(prev => prev.map(msg => 
        msg.id === aiPlaceholder.id ? { ...msg, text: 'Sorry, I encountered an error. Please try again.', isError: true } : msg
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
          {messages.map((msg) => (
            <div key={msg.id} className={`flex items-start gap-4 p-4 my-2 rounded-lg ${msg.sender === 'user' ? 'bg-transparent' : 'bg-[#444654]'}`}>
              {msg.sender === 'ai' ? <FaRobot className="text-2xl text-white mt-1" /> : <FaUserCircle className="text-2xl text-sky-400 mt-1" />}
              <div className="flex-1 pt-1">
                <div className={`${msg.isError ? 'text-red-400' : 'text-gray-100'}`}>
                  <ReactMarkdown components={CodeBlock}>{msg.text}</ReactMarkdown>
                </div>
                {/* THIS IS THE CORRECTED LINE */}
                {msg.sender === 'ai' && msg.sources && msg.sources.length > 0 && !isLoading && (
                  <button onClick={() => openSourcesModal(msg.sources)} className="mt-2 flex items-center gap-2 text-xs text-slate-400 hover:text-sky-400 transition-colors">
                    <FaBook />
                    <span>Show Sources</span>
                  </button>
                )}
              </div>
            </div>
          ))}
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

      <Modal
        isOpen={modalIsOpen}
        onRequestClose={() => setModalIsOpen(false)}
        style={{
          overlay: { backgroundColor: 'rgba(0, 0, 0, 0.75)', zIndex: 50 },
          content: {
            top: '50%', left: '50%', right: 'auto', bottom: 'auto',
            marginRight: '-50%', transform: 'translate(-50%, -50%)',
            background: '#444654', border: '1px solid #555',
            borderRadius: '10px', color: 'white', maxWidth: '90%', width: '700px',
            padding: '2rem'
          }
        }}
        contentLabel="Source Chunks"
      >
        <h2 className="text-xl font-bold mb-4 text-sky-300">Source Material</h2>
        <div className="max-h-[60vh] overflow-y-auto pr-2">
          {currentSources.map((source, index) => (
            <div key={index} className="bg-slate-700 p-4 mb-3 rounded-lg border border-slate-600">
              <p className="text-slate-300 whitespace-pre-wrap">{source}</p>
            </div>
          ))}
        </div>
        <button onClick={() => setModalIsOpen(false)} className="mt-6 bg-sky-600 hover:bg-sky-700 text-white font-bold py-2 px-4 rounded transition-colors">Close</button>
      </Modal>
    </div>
  );
}

export default ChatBox;