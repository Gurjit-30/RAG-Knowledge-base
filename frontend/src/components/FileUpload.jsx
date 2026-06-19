import { useState, useCallback } from 'react';
import axios from 'axios';
import { UploadCloud, File, CheckCircle, AlertCircle, X } from 'lucide-react';

export default function FileUpload({ token }) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [status, setStatus] = useState('idle'); // idle, uploading, success, error
  const [message, setMessage] = useState('');

  const onDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  }, []);

  const onFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = (selectedFile) => {
    if (selectedFile.type !== 'application/pdf') {
      setStatus('error');
      setMessage('Only PDF files are supported.');
      return;
    }
    setFile(selectedFile);
    setStatus('idle');
    setMessage('');
    setUploadProgress(0);
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus('uploading');
    setUploadProgress(0);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${apiUrl}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });
      
      setStatus('success');
      setMessage(`Successfully processed ${response.data.chunks_added} chunks!`);
    } catch (error) {
      setStatus('error');
      setMessage(error.response?.data?.detail || 'Upload failed');
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 animate-fade-in-up">
      <div 
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300 ${
          isDragging 
            ? 'border-primary-500 bg-primary-500/10 scale-[1.02]' 
            : 'border-dark-600 bg-dark-800/50 hover:border-dark-500'
        }`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <input 
          type="file" 
          accept="application/pdf"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          onChange={onFileChange}
          disabled={status === 'uploading'}
        />

        {!file ? (
          <div className="flex flex-col items-center justify-center space-y-4 pointer-events-none">
            <div className="w-16 h-16 rounded-full bg-dark-700 flex items-center justify-center text-slate-400">
              <UploadCloud size={32} />
            </div>
            <div>
              <p className="text-lg font-medium text-slate-200">Drag & drop your PDF here</p>
              <p className="text-sm text-slate-500 mt-1">or click to browse from your computer</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-primary-500/20 text-primary-400 flex items-center justify-center relative">
              <File size={32} />
              {status === 'idle' && (
                <button 
                  onClick={(e) => {
                    e.preventDefault();
                    setFile(null);
                  }}
                  className="absolute -top-2 -right-2 bg-dark-700 hover:bg-red-500 text-white rounded-full p-1 z-10"
                >
                  <X size={14} />
                </button>
              )}
            </div>
            <div>
              <p className="text-lg font-medium text-slate-200">{file.name}</p>
              <p className="text-sm text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          </div>
        )}
      </div>

      {/* Progress & Status */}
      {file && status !== 'idle' && (
        <div className="mt-6 p-4 rounded-xl bg-dark-800 border border-dark-700">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-slate-300 font-medium">
              {status === 'uploading' ? 'Uploading & Processing...' : status === 'success' ? 'Complete' : 'Error'}
            </span>
            <span className="text-primary-400">{uploadProgress}%</span>
          </div>
          
          <div className="w-full bg-dark-900 rounded-full h-2 overflow-hidden">
            <div 
              className={`h-full transition-all duration-300 ${
                status === 'error' ? 'bg-red-500' : 'bg-primary-500'
              }`}
              style={{ width: `${uploadProgress}%` }}
            />
          </div>

          {message && (
            <div className={`mt-3 flex items-center gap-2 text-sm ${
              status === 'error' ? 'text-red-400' : 'text-primary-400'
            }`}>
              {status === 'error' ? <AlertCircle size={16} /> : <CheckCircle size={16} />}
              {message}
            </div>
          )}
        </div>
      )}

      {/* Action Button */}
      {file && status === 'idle' && (
        <div className="mt-6 flex justify-center">
          <button
            onClick={handleUpload}
            className="glass-button px-8 py-3 rounded-xl font-medium flex items-center gap-2"
          >
            <UploadCloud size={20} />
            Upload Document
          </button>
        </div>
      )}
      
      {/* Success Next Steps Button */}
      {status === 'success' && (
        <div className="mt-6 flex justify-center">
          <button
            onClick={() => {
              setFile(null);
              setStatus('idle');
              setMessage('');
              setUploadProgress(0);
            }}
            className="glass-button px-8 py-3 rounded-xl font-medium flex items-center gap-2"
          >
            <File size={20} />
            Upload Another Document
          </button>
        </div>
      )}
    </div>
  );
}
