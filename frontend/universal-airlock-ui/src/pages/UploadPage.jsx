import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { trainingValidationAPI } from '../services/TrainingValidationAPI.js';

export default function UploadPage() {
  const [sessionId, setSessionId] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({ success: null, message: '' });

  const onDrop = useCallback(async (acceptedFiles) => {
    if (!sessionId) {
      setUploadStatus({ success: false, message: 'Please enter a session ID' });
      return;
    }

    const file = acceptedFiles[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus({ success: null, message: 'Uploading document...' });

    try {
      const response = await trainingValidationAPI.uploadDocument(sessionId, file);
      setUploadStatus({ 
        success: true, 
        message: `Document uploaded successfully! ID: ${response.id}` 
      });
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadStatus({ 
        success: false, 
        message: `Upload failed: ${error.response?.data?.detail || error.message}` 
      });
    } finally {
      setIsUploading(false);
    }
  }, [sessionId]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    maxFiles: 1,
    disabled: isUploading || !sessionId
  });

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Upload Documents for Validation</h1>
      
      <div className="mb-6">
        <label htmlFor="sessionId" className="block text-sm font-medium text-gray-700 mb-2">
          Validation Session ID
        </label>
        <input
          type="text"
          id="sessionId"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md"
          placeholder="Enter validation session ID"
          disabled={isUploading}
        />
      </div>

      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        {isUploading ? (
          <p className="text-gray-600">Uploading document, please wait...</p>
        ) : isDragActive ? (
          <p className="text-blue-600">Drop the document here...</p>
        ) : (
          <div>
            <p className="text-gray-600">
              Drag & drop a document here, or click to select a file
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Supported formats: PDF, DOC, DOCX, TXT
            </p>
          </div>
        )}
      </div>

      {uploadStatus.message && (
        <div 
          className={`mt-4 p-3 rounded-md ${
            uploadStatus.success === true ? 'bg-green-100 text-green-800' : 
            uploadStatus.success === false ? 'bg-red-100 text-red-800' : 
            'bg-blue-100 text-blue-800'
          }`}
        >
          {uploadStatus.message}
        </div>
      )}

      <div className="mt-6 p-4 bg-gray-50 rounded-md">
        <h2 className="text-lg font-semibold mb-2">Upload Instructions</h2>
        <ul className="list-disc pl-5 space-y-1 text-sm text-gray-600">
          <li>Enter a valid validation session ID before uploading</li>
          <li>Supported file types: PDF, Word documents, and text files</li>
          <li>Maximum file size: 10MB</li>
          <li>Documents will be processed for validation after upload</li>
        </ul>
      </div>
    </div>
  );
}
