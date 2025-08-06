// src/App.jsx

import React, { useState } from 'react';
import UploadBox from './components/UploadBox';
import ChatBox from './components/ChatBox';

function App() {
  const [appState, setAppState] = useState('upload'); // 'upload' or 'chat'
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
    // This is the main container for the entire page
    <div className="bg-[#343541] h-screen flex flex-col text-white font-sans">
      
      {/* Top Header with your new gradient styles */}
      <header className="w-full p-4 flex justify-between items-center border-b border-gray-600 shadow-md">
        <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 via-pink-500 to-indigo-500 bg-clip-text text-transparent">
          ExplainMyDoc.ai
        </h1>
        {appState === 'chat' && (
            <button 
              onClick={handleNewUpload} 
              className="bg-gradient-to-r from-sky-500 to-blue-700 hover:from-sky-600 hover:to-blue-800 text-white font-semibold py-2 px-4 rounded-md text-sm transition-all duration-300"
            >
              Upload New File
            </button>
        )}
      </header>

      {/* Main Content Area with the layout fix applied */}
      <main className="flex-grow w-full overflow-hidden">
        {appState === 'upload' && (
          // Centering wrapper for the upload view
          <div className="h-full flex items-center justify-center p-4">
            <div className="bg-[#444654] p-8 rounded-lg shadow-xl max-w-lg w-full">
              <UploadBox onUploadSuccess={handleUploadSuccess} />
            </div>
          </div>
        )}

        {appState === 'chat' && sessionId && (
          // ChatBox now correctly fills the main area
          <ChatBox sessionId={sessionId} />
        )}
      </main>

    </div>
  );
}

export default App;