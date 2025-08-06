// src/components/UploadBox.jsx

import React, { useState } from 'react';
import axios from 'axios';

// This component will receive a function from its parent (App.jsx)
// to notify it when the upload is successful.
function UploadBox({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [status, setStatus] = useState('idle'); // 'idle', 'uploading', 'success', 'error'
  const [errorMessage, setErrorMessage] = useState('');

  const handleFileChange = (event) => {
    setStatus('idle');
    setErrorMessage('');
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setErrorMessage('Please select a file first.');
      return;
    }

    // Create a FormData object to send the file
    const formData = new FormData();
    formData.append('file', selectedFile);

    setStatus('uploading');
    setErrorMessage('');

    try {
      // Make the API call to our backend
      const response = await axios.post('http://127.0.0.1:8000/process/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setStatus('success');
      // Call the parent's function with the new session_id
      onUploadSuccess(response.data.session_id);

    } catch (error) {
      setStatus('error');
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        setErrorMessage(error.response.data.detail || 'An error occurred during upload.');
      } else {
        // Something happened in setting up the request that triggered an Error
        setErrorMessage('Network error or server is not reachable.');
      }
    }
  };

  return (
    <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center">
      <input 
        type="file" 
        onChange={handleFileChange} 
        className="block w-full text-sm text-slate-400
                   file:mr-4 file:py-2 file:px-4
                   file:rounded-full file:border-0
                   file:text-sm file:font-semibold
                   file:bg-sky-50 file:text-sky-700
                   hover:file:bg-sky-100 mb-4"
        accept=".pdf,.docx,.txt" // Restrict file types
      />
      
      {selectedFile && (
        <p className="text-slate-400 mb-4">
          Selected: {selectedFile.name}
        </p>
      )}

      <button
        onClick={handleUpload}
        disabled={!selectedFile || status === 'uploading'}
        className="bg-sky-600 hover:bg-sky-700 disabled:bg-slate-500 text-white font-bold py-2 px-6 rounded-lg transition-colors"
      >
        {status === 'uploading' ? 'Processing...' : 'Upload & Process'}
      </button>

      {status === 'error' && (
        <p className="text-red-400 mt-4">{errorMessage}</p>
      )}
    </div>
  );
}

export default UploadBox;