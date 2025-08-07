// src/App.jsx

import React, { useState } from 'react';
import UploadBox from './components/UploadBox';
import ChatBox from './components/ChatBox';
import { FiUpload } from 'react-icons/fi';

function App() {
  const [appState, setAppState] = useState('upload');
  const [sessionId, setSessionId] = useState(null);

  const handleUploadSuccess = (newSessionId) => {
    setSessionId(newSessionId);
    setAppState('chat');
  };

  const handleNewUpload = () => {
    setSessionId(null);
    setAppState('upload');
  };

  return (
    <div className="bg-black h-screen flex flex-col text-gray-100 font-sans">
      
      <header className="w-full p-4 flex justify-between items-center border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
        <h1 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-fuchsia-500 via-purple-500 to-indigo-600 bg-clip-text text-transparent">
          DocuMentor AI
        </h1>
        {appState === 'chat' && (
            <button 
              onClick={handleNewUpload} 
              title="Upload New File"
              className="bg-black h-10 w-10 flex items-center justify-center border-2 border-white rounded-full 
                         hover:bg-white hover:text-black transition-all duration-300 group"
            >
              <FiUpload className="text-white text-lg group-hover:text-black transition-colors" />
            </button>
        )}
      </header>

      <main className="flex-grow w-full overflow-hidden">
        {appState === 'upload' && (
          <div className="h-full flex items-center justify-center p-4">
            {/* --- THIS IS THE CORRECTED DIV WITH RESPONSIVE SIZING --- */}
            {/* It's max-w-lg by default, but becomes max-w-2xl on large screens */}
            <div className="bg-black border border-gray-700 p-6 md:p-8 rounded-xl shadow-2xl shadow-purple-500/5 w-full max-w-lg lg:max-w-2xl">
              <UploadBox onUploadSuccess={handleUploadSuccess} />
            </div>
          </div>
        )}

        {appState === 'chat' && sessionId && (
          <ChatBox sessionId={sessionId} />
        )}
      </main>

    </div>
  );
}

export default App;