import { useState, useEffect } from 'react';
import { trainingValidationAPI } from '../services/TrainingValidationAPI.js';
import Dropzone from '../components/Dropzone.jsx';
import Progress from '../progress.jsx';
import ChatInterface from '../ChatInterface.jsx';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Helper function to extract unit code from URL
const deriveUnitCode = (url) => {
  if (!url) return 'UNKNOWN_UNIT';
  try {
    const parts = url.split('/').filter(Boolean);
    return parts[parts.length - 1] || 'UNKNOWN_UNIT';
  } catch {
    return 'UNKNOWN_UNIT';
  }
};

export default function ValidationPage() {
  const [uploads, setUploads] = useState([]); // {file, progress, status, id}
  const [validationStatus, setValidationStatus] = useState(null); // pending, running, approved, rejected
  const [sessionId, setSessionId] = useState(null);
  const [unitUrl, setUnitUrl] = useState('');
  const [reportUrl, setReportUrl] = useState('');
  const [unitCode, setUnitCode] = useState('');
  const [isScraping, setIsScraping] = useState(false);

  // Derive unit code from URL when it changes
  useEffect(() => {
    try {
      if (unitUrl) {
        const parts = unitUrl.split('/').filter(Boolean);
        const code = parts[parts.length - 1] || 'UNKNOWN_UNIT';
        setUnitCode(code);
        
        // Create a new validation session when unit URL changes
        const createSession = async () => {
          try {
            // Generate a proper UUID for the training unit
            const trainingUnitId = uuidv4();
            
            const session = await trainingValidationAPI.createValidationSession({
              name: `Validation for ${code}`,
              description: `Validation session for unit ${code}`,
              training_unit_id: trainingUnitId, // Use the generated UUID
              configuration: {
                source_url: unitUrl,
                original_code: code
              },
              created_by: 'system' // TODO: Replace with actual user ID
            });
            
            setSessionId(session.id);
            console.log('Created new validation session:', session);
            toast.success('Validation session created successfully');
          } catch (error) {
            console.error('Failed to create validation session:', error);
            const errorMsg = error.response?.data?.detail || error.message || 'Failed to create validation session';
            toast.error(`Failed to create session: ${errorMsg}`);
          }
        };
        
        createSession();
      }
    } catch (error) {
      console.error('Error processing unit URL:', error);
      setUnitCode('UNKNOWN_UNIT');
      toast.error(`Error processing URL: ${error.message}`);
    }
  }, [unitUrl]);

  const createNewSession = async () => {
    try {
      const code = unitCode || 'DEFAULT_UNIT';
      // Generate a proper UUID for the training unit
      const trainingUnitId = uuidv4();
      
      const session = await trainingValidationAPI.createValidationSession({
        name: `Validation for ${code}`,
        description: `Validation session for unit ${code}`,
        training_unit_id: trainingUnitId, // Use the generated UUID
        configuration: {
          source_url: unitUrl,
          original_code: code
        },
        created_by: 'system' // TODO: Replace with actual user ID
      });
      
      setSessionId(session.id);
      toast.success('Created new validation session');
      return session.id;
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to create validation session';
      console.error('Failed to create validation session:', error);
      toast.error(`Failed to create session: ${errorMsg}`);
      throw new Error(errorMsg);
    }
  };

  const handleFiles = async (files) => {
    let currentSessionId = sessionId;
    
    // If no session exists, create one
    if (!currentSessionId) {
      try {
        currentSessionId = await createNewSession();
      } catch (error) {
        console.error('Failed to create validation session:', error);
        toast.error(`Failed to start validation session: ${error.message}`);
        return;
      }
    }

    for (const file of files) {
      const uploadItem = { 
        file, 
        progress: 0, 
        status: 'uploading', 
        id: Date.now() + file.name 
      };
      
      setUploads((u) => [...u, uploadItem]);
      
      try {
        // Check file size (limit to 10MB)
        const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
        if (file.size > MAX_FILE_SIZE) {
          throw new Error('File size exceeds 10MB limit');
        }

        // Check file type
        const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
        if (!validTypes.includes(file.type)) {
          throw new Error('Invalid file type. Please upload a PDF, Word document, or text file.');
        }
        
        // Upload the document
        toast.info(`Uploading ${file.name}...`);
        const response = await trainingValidationAPI.uploadDocument(currentSessionId, file);
        
        setUploads((prev) => 
          prev.map((it) => 
            it.id === uploadItem.id 
              ? { ...it, status: 'uploaded', documentId: response.id } 
              : it
          )
        );
        
        // Start validation
        setValidationStatus('running');
        toast.info('Validating document...');
        
        // Execute validation
        const validationResult = await trainingValidationAPI.executeValidation(currentSessionId);
        setValidationStatus(validationResult.status);
        
        if (validationResult.status === 'approved') {
          toast.success('Document validated successfully!');
        } else if (validationResult.status === 'rejected') {
          toast.warning('Document validation completed with issues');
        } else {
          toast.info(`Validation status: ${validationResult.status}`);
        }
        
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Upload failed';
        console.error('Upload or validation failed:', error);
        
        setUploads((prev) => 
          prev.map((it) => 
            it.id === uploadItem.id 
              ? { ...it, status: 'error', error: errorMsg } 
              : it
          )
        );
        
        toast.error(`Upload failed: ${errorMsg}`);
      }
    }
  };

  // Poll validation status periodically
  useEffect(() => {
    if (validationStatus !== 'running' || !sessionId) return;
    
    const interval = setInterval(async () => {
      try {
        const session = await trainingValidationAPI.getValidationSession(sessionId);
        
        if (session.status && session.status !== 'running') {
          setValidationStatus(session.status); // approved, rejected, or needs_review
          
          // If validation is complete, get the report URL if available
          if (session.report_url) {
            setReportUrl(session.report_url);
          }
          
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Status poll failed', error);
        // Don't stop polling on error, just log it
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [validationStatus, sessionId]);

  const handleDownload = async () => {
    if (!sessionId) {
      console.error('No session ID available for report download');
      return;
    }
    
    try {
      // Get the report URL from the session
      const session = await trainingValidationAPI.getValidationSession(sessionId);
      
      if (!session.report_url) {
        throw new Error('No report available for this session');
      }
      
      // Create a temporary link to trigger the download
      const link = document.createElement('a');
      link.href = session.report_url;
      link.setAttribute('download', `validation_report_${unitCode || 'report'}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
    } catch (error) {
      console.error('Report download failed:', error);
      alert(`Failed to download report: ${error.message}`);
    }
  };

  return (
    <div className="space-y-8">
      <ToastContainer 
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
      />
      <h1 className="text-2xl font-bold">Training Validation</h1>

      {/* Unit URL & scrape */}
      {/* URL input only */}
      <div>
        <div className="mt-4">
          <label className="block mb-2 font-medium">Training.gov or custom source URL</label>
          <input
            type="url"
            value={unitUrl}
            onChange={(e) => setUnitUrl(e.target.value)}
            placeholder="https://training.gov.au/..."
            className="border rounded px-3 py-2 w-full"
          />
          <div className="flex items-center gap-2">
            <button
              className={`mt-2 px-4 py-2 rounded flex items-center gap-2 ${isScraping ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700 text-white'}`}
              onClick={async () => {
                if (!unitUrl) {
                  toast.error('Please enter a URL');
                  return;
                }
                
                setIsScraping(true);
                const toastId = toast.loading('Starting web scraping process...');
                
                try {
                  // Show initial progress
                  toast.update(toastId, {
                    render: 'Connecting to web intelligence service...',
                    type: 'info',
                    isLoading: true
                  });
                  
                  // Start the scraping process
                  const response = await axios.post('http://localhost:8033/api/v1/training-units/retrieve', {
                    'unit_code': deriveUnitCode(unitUrl),
                    url: unitUrl,
                    session_id: sessionId
                  });
                  
                  // Show success message with details
                  toast.update(toastId, {
                    render: `Successfully scraped unit: ${response.data.unit?.code || 'Unknown'}`,
                    type: 'success',
                    isLoading: false,
                    autoClose: 5000,
                  });
                  
                  // Show additional toast with next steps
                  toast.info('The training unit has been processed and is ready for document validation.', {
                    autoClose: 8000
                  });
                  
                } catch (err) {
                  console.error('Scraping error:', err);
                  const errorMessage = err.response?.data?.detail || 'An unknown error occurred';
                  
                  toast.update(toastId, {
                    render: `Failed to scrape unit: ${errorMessage}`,
                    type: 'error',
                    isLoading: false,
                    autoClose: 5000,
                  });
                  
                  // Show more detailed error message if available
                  if (err.response?.data?.detail?.includes('connection')) {
                    toast.error('Please check your internet connection and try again.', {
                      autoClose: 5000
                    });
                  } else if (err.response?.status === 404) {
                    toast.error('The specified training unit could not be found. Please check the URL and try again.', {
                      autoClose: 5000
                    });
                  }
                } finally {
                  setIsScraping(false);
                }
              }}
              disabled={isScraping}
            >
              {isScraping ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Scraping...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  Scrape & Save Unit
                </>
              )}
            </button>
            
            {isScraping && (
              <button
                className="mt-2 px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                onClick={() => {
                  // This would need to be implemented with proper request cancellation
                  toast.info('Cancellation requested. Cleaning up...');
                  // Note: In a real implementation, you would need to cancel the axios request
                  // using an AbortController or similar mechanism
                }}
              >
                Cancel
              </button>
            )}
          </div>
          
          <p className="mt-2 text-sm text-gray-500">
            Enter a Training.gov.au URL to automatically retrieve unit information
          </p>
        </div>
      </div>

      {/* Upload docs */}
      <div>
        <h2 className="font-semibold mb-2">Upload documents</h2>
        <Dropzone onFiles={handleFiles} />
        <ul className="mt-4 space-y-2">
          {uploads.map((u) => (
            <li key={u.id} className="flex items-center gap-4">
              <span className="flex-1 truncate">{u.file.name}{u.total_pages ? ` (pages: ${u.total_pages})` : ''}</span>
              <Progress value={u.progress} className="w-40" />
              <span className="text-sm capitalize">{u.status}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Validation status */}
      {validationStatus && (
        <div className="p-4 border rounded bg-gray-50">
          <p className="font-medium mb-2">Validation status: {validationStatus}</p>
          {validationStatus === 'approved' && (
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded"
              onClick={handleDownload}
            >
              Download Report
            </button>
          )}
        </div>
      )}

      {/* Chat/Airlock */}
      <div>
        <h2 className="font-semibold mb-2">Review & Chat</h2>
        <div className="h-96"><ChatInterface itemId={deriveUnitCode(unitUrl) || 'temp'} /></div>
      </div>
    </div>
  );
}

