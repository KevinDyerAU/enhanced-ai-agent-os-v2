import { useState, useEffect } from 'react';
import axios from 'axios';
import Dropzone from '../components/Dropzone.jsx';
import Progress from '../progress.jsx';
import ChatInterface from '../ChatInterface.jsx';

// Unit list removed


export default function ValidationPage() {
    // Unit selection removed – derive unit code from URL
  const deriveUnitCode = (url) => {
    try {
      const parts = url.split('/').filter(Boolean);
      return parts[parts.length - 1] || 'UNKNOWN_UNIT';
    } catch {
      return 'UNKNOWN_UNIT';
    }
  };
  const [uploads, setUploads] = useState([]); // {file, progress, status, id}
  const [validationStatus, setValidationStatus] = useState(null); // pending, running, approved, rejected
  const [sessionId, setSessionId] = useState(null);
  const [unitUrl, setUnitUrl] = useState('');
  const [reportUrl, setReportUrl] = useState('');

  const handleFiles = async (files) => {
    for (const file of files) {
      const form = new FormData();
      form.append('file', file);
      
      const uploadItem = { file, progress: 0, status: 'uploading', id: Date.now() + file.name };
      setUploads((u) => [...u, uploadItem]);
      try {
        const res = await axios.post('http://localhost:8033/documents/upload', form, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            const pct = Math.round((e.loaded * 100) / e.total);
            setUploads((prev) => prev.map((it) => (it.id === uploadItem.id ? { ...it, progress: pct } : it)));
          }
        });
        setUploads((prev) => prev.map((it) => (it.id === uploadItem.id ? { ...it, status: 'uploaded' } : it)));
        // Start validation session (simplified)
        const startRes = await axios.post('http://localhost:8033/validation/start', { documentId: res.data.id });
        setSessionId(startRes.data.sessionId);
        setValidationStatus('running');
      } catch (err) {
        console.error(err);
        setUploads((prev) => prev.map((it) => (it.id === uploadItem.id ? { ...it, status: 'error' } : it)));
      }
    }
  };

  // Poll validation status periodically
  useEffect(() => {
    if (validationStatus !== 'running' || !sessionId) return;
    const interval = setInterval(async () => {
      try {
        const statusRes = await axios.get(`http://localhost:8033/validation/${sessionId}/status`);
        if (statusRes.data.status && statusRes.data.status !== 'running') {
          setValidationStatus(statusRes.data.status); // approved or rejected
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Status poll failed', err);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [validationStatus, sessionId]);

  const handleDownload = async () => {
    try {
      const res = await axios.get(`http://localhost:8033/reports/${sessionId}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'validation_report.pdf');
      document.body.appendChild(link);
      link.click();
    } catch (err) {
      console.error(err);
      alert('Report download failed');
    }
  };

  return (
    <div className="space-y-8">
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
          <button
            className="mt-2 px-4 py-2 bg-green-600 text-white rounded"
            onClick={async () => {
              if (!unitUrl) {
                alert('Please enter a URL');
                return;
              }
              try {
                await axios.post('http://localhost:8033/api/v1/training-units/retrieve', {
                  'unit_code': deriveUnitCode(unitUrl),
                  url: unitUrl,
                  session_id: sessionId
                });
                alert('Unit scraped and stored');
              } catch (err) {
                console.error(err);
                alert('Failed to scrape or store unit');
              }
            }}
          >
            Scrape & Save Unit
          </button>
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

