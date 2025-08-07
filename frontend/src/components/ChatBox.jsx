// frontend/src/components/ChatBox.jsx

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import TextareaAutosize from 'react-textarea-autosize';
import { FaUserCircle, FaPaperPlane, FaRobot, FaBook, FaQuestionCircle } from 'react-icons/fa';
import { FiDownload, FiLoader } from 'react-icons/fi';
import CodeBlock from './CodeBlock';
import Modal from 'react-modal';

Modal.setAppElement('#root');

function ChatBox({ sessionId }) {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I have read your document. Feel free to ask me any questions about it.", sender: 'ai', sources: [] }
  ]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const [currentSources, setCurrentSources] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); };
  useEffect(scrollToBottom, [messages, isLoading, suggestions]);

  const openSourcesModal = (sources) => { setCurrentSources(sources); setModalIsOpen(true); };

  const handleSendMessage = async (messageText = userInput) => {
    if (!messageText.trim() || isLoading) return;
    const userMessage = { id: Date.now(), text: messageText, sender: 'user', sources: [] };
    const aiPlaceholder = { id: Date.now() + 1, text: '', sender: 'ai', sources: [] };
    const historyForAPI = messages.slice(-4).map(msg => ({ sender: msg.sender, text: msg.text }));
    setMessages(prev => [...prev, userMessage, aiPlaceholder]);
    setUserInput('');
    setSuggestions([]);
    setIsLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/query/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, question: messageText, chat_history: historyForAPI }),
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
        setMessages(prev => prev.map(msg => msg.id === aiPlaceholder.id ? { ...msg, text: finalAnswer, sources: decodedSources } : msg));
      }
      const answerParts = finalAnswer.split('\n');
      const mainAnswer = answerParts.filter(part => !part.trim().startsWith('SUGGESTION:')).join('\n');
      const extractedSuggestions = answerParts.filter(part => part.trim().startsWith('SUGGESTION:')).map(s => s.replace('SUGGESTION:', '').trim());
      setMessages(prev => prev.map(msg => msg.id === aiPlaceholder.id ? { ...msg, text: mainAnswer } : msg));
      setSuggestions(extractedSuggestions);
    } catch (error) {
      console.error("Request failed:", error);
      setMessages(prev => prev.map(msg => msg.id === aiPlaceholder.id ? { ...msg, text: 'Sorry, I encountered an error.', isError: true } : msg));
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    if (messages.length <= 1) {
      alert("There is not enough conversation to export.");
      return;
    }
    setIsExporting(true);
    try {
      const historyForExport = messages.map(msg => ({
        sender: msg.sender, text: msg.text,
      }));
      const response = await axios.post('http://127.0.0.1:8000/export/pdf', {
          chat_history: historyForExport
      }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'DocuMentor_Summary.pdf');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("PDF Export failed:", error);
      alert("Sorry, there was an error creating your PDF report.");
    } finally {
      setIsExporting(false);
    }
  };

  const handleSuggestionClick = (suggestion) => { handleSendMessage(suggestion); };
  const handleKeyPress = (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); handleSendMessage(); } };

  return (
    <div className="h-full flex flex-col w-full bg-black">
      <div className="flex-grow overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto">
          {messages.map((msg) => (
            <div key={msg.id} className="flex items-start gap-4 my-6">
              {msg.sender === 'ai' 
                ? <div className="bg-gray-800 p-2 rounded-full"><FaRobot className="text-white text-lg" /></div>
                : <div className="bg-gradient-to-br from-fuchsia-600 to-indigo-600 p-2 rounded-full"><FaUserCircle className="text-white text-lg" /></div>
              }
              <div className="flex-1 pt-1">
                <div className={`prose prose-invert max-w-none ${msg.sender === 'ai' ? 'bg-gray-900 border border-gray-800 p-4 rounded-lg' : ''} ${msg.isError ? 'text-red-400' : 'text-gray-200'}`}>
                  <ReactMarkdown components={CodeBlock}>{msg.text}</ReactMarkdown>
                </div>
                {msg.sender === 'ai' && msg.sources && msg.sources.length > 0 && !isLoading && (
                  <button onClick={() => openSourcesModal(msg.sources)} className="mt-3 flex items-center gap-2 text-xs text-gray-500 hover:text-purple-400 transition-colors">
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
      
      <div className="w-full border-t border-gray-800 bg-black pt-4 pb-4">
        {suggestions.length > 0 && (
          <div className="max-w-4xl mx-auto px-4 mb-3">
            <h3 className="text-sm text-gray-500 mb-2 flex items-center gap-2"><FaQuestionCircle /> Suggestions:</h3>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s, i) => (
                <button 
                  key={i} 
                  onClick={() => handleSuggestionClick(s)}
                  className="bg-gray-800 text-left hover:bg-gray-700 text-gray-200 text-sm py-1 px-3 rounded-full transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="max-w-4xl mx-auto flex items-center gap-2 px-4">
          <button 
            title="Export Conversation to PDF"
            onClick={handleExport}
            disabled={isExporting || messages.length <= 1}
            className="p-3 bg-gray-900 border border-gray-700 hover:border-purple-500 rounded-lg text-gray-300 hover:text-purple-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExporting ? <FiLoader className="animate-spin text-xl" /> : <FiDownload className="text-xl"/>}
          </button>
          
          <div className="relative flex-grow">
            <TextareaAutosize
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask a question about your document..."
              className="w-full bg-black border-2 border-gray-700 rounded-lg p-4 pr-14 text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none shadow-lg transition-colors focus:border-purple-500"
              maxRows={5}
              disabled={isLoading}
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={isLoading || !userInput.trim()}
              className="absolute right-4 top-1/2 -translate-y-1/2 p-2 text-gray-500 hover:text-purple-400 disabled:text-gray-700 disabled:cursor-not-allowed transition-colors"
            >
              <FaPaperPlane className="text-2xl" />
            </button>
          </div>
        </div>
      </div>
      
      <Modal
        isOpen={modalIsOpen}
        onRequestClose={() => setModalIsOpen(false)}
        style={{
          overlay: { backgroundColor: 'rgba(0, 0, 0, 0.85)', zIndex: 50 },
          content: {
            top: '50%', left: '50%', right: 'auto', bottom: 'auto',
            marginRight: '-50%', transform: 'translate(-50%, -50%)',
            background: '#111827', border: '1px solid #374151',
            borderRadius: '10px', color: 'white', maxWidth: '90%', width: '800px',
            padding: '2rem'
          }
        }}
        contentLabel="Source Chunks"
      >
        <h2 className="text-2xl font-bold mb-4 bg-gradient-to-r from-fuchsia-500 to-purple-500 bg-clip-text text-transparent">Source Material</h2>
        <div className="max-h-[60vh] overflow-y-auto pr-4">
          {currentSources.map((source, index) => (
            <div key={index} className="bg-gray-900 p-4 mb-3 rounded-lg border border-gray-700">
              <p className="text-gray-300 whitespace-pre-wrap">{source}</p>
            </div>
          ))}
        </div>
        <button onClick={() => setModalIsOpen(false)} className="mt-6 w-full font-bold py-2 px-4 rounded-lg text-white bg-gradient-to-r from-fuchsia-600 to-indigo-600 hover:from-fuchsia-700 hover:to-indigo-700 transition-all">Close</button>
      </Modal>
    </div>
  );
}

export default ChatBox;