// frontend/src/components/UploadBox.jsx

import React, { useState, useRef } from 'react';
import axios from 'axios';
import { FiFile, FiUploadCloud, FiLoader, FiCheckCircle, FiAlertTriangle } from 'react-icons/fi';

function UploadBox({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [status, setStatus] = useState('idle'); // 'idle', 'uploading', 'success', 'error'
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    setStatus('idle');
    setErrorMessage('');
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setErrorMessage('Please select a file first.');
      return;
    }
    const formData = new FormData();
    formData.append('file', selectedFile);
    setStatus('uploading');
    setErrorMessage('');
    try {
      // --- THIS IS THE CORRECTED LINE ---
      // It now uses the environment variable and has the correct commas.
      const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/process/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      // --- END OF CORRECTION ---

      setStatus('success');
      onUploadSuccess(response.data.session_id);
    } catch (error) {
      setStatus('error');
      setErrorMessage(error.response?.data?.detail || 'An error occurred during upload.');
    }
  };

  const onAreaClick = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-6">
      <div
        onClick={onAreaClick}
        className="w-full h-48 border-2 border-dashed border-gray-600 rounded-xl flex flex-col items-center justify-center 
                   text-gray-400 hover:border-purple-500 hover:text-purple-400 transition-all duration-300 cursor-pointer"
      >
        <FiUploadCloud className="text-4xl mb-2" />
        <p className="text-lg font-semibold">Click to browse or drag & drop</p>
        <p className="text-sm">Supports PDF, DOCX, TXT</p>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileChange}
          className="hidden"
          accept=".pdf,.docx,.txt"
        />
      </div>

      {selectedFile && (
        <div className="flex items-center gap-3 bg-black border border-gray-700 p-2 rounded-lg w-full max-w-sm">
          <FiFile className="text-sky-400 text-xl" />
          <span className="text-gray-300 truncate">{selectedFile.name}</span>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!selectedFile || status === 'uploading'}
        className="w-full max-w-sm flex items-center justify-center gap-3 font-bold py-3 px-6 rounded-lg text-white 
                   bg-gradient-to-r from-fuchsia-600 to-indigo-600 
                   hover:from-fuchsia-700 hover:to-indigo-700
                   disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed
                   transition-all duration-300 transform hover:scale-105"
      >
        {status === 'uploading' && <FiLoader className="animate-spin" />}
        <span>{status === 'uploading' ? 'Processing Document...' : 'Analyze Document'}</span>
      </button>

      {status === 'error' && (
        <div className="flex items-center gap-2 text-red-400">
          <FiAlertTriangle />
          <span>{errorMessage}</span>
        </div>
      )}
      {status === 'success' && (
         <div className="flex items-center gap-2 text-green-400">
           <FiCheckCircle />
           <span>Upload successful! Starting chat...</span>
         </div>
      )}
    </div>
  );
}

export default UploadBox;