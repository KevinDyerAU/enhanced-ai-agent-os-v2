import React, { useState, useEffect } from 'react';

interface ValidationSession {
  id: string;
  name: string;
  description?: string;
  training_unit_id: string;
  unit_code: string;
  unit_title: string;
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface TrainingUnit {
  id: string;
  unit_code: string;
  title: string;
  description: string;
  cached: boolean;
}

const TrainingValidationDashboard: React.FC = () => {
  const [sessions, setSessions] = useState<ValidationSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateSession, setShowCreateSession] = useState(false);
  const [newSessionData, setNewSessionData] = useState({
    name: '',
    description: '',
    unit_code: ''
  });

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await fetch('http://localhost:8033/api/v1/validation-sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async () => {
    try {
      const unitResponse = await fetch('http://localhost:8033/api/v1/training-units/retrieve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ unit_code: newSessionData.unit_code })
      });

      if (!unitResponse.ok) {
        throw new Error('Failed to retrieve training unit');
      }

      const unit: TrainingUnit = await unitResponse.json();

      const sessionResponse = await fetch('http://localhost:8033/api/v1/validation-sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newSessionData.name,
          description: newSessionData.description,
          training_unit_id: unit.id,
          created_by: 'current_user'
        })
      });

      if (sessionResponse.ok) {
        setShowCreateSession(false);
        setNewSessionData({ name: '', description: '', unit_code: '' });
        fetchSessions();
      }
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  if (loading) {
    return <div className="p-6">Loading validation sessions...</div>;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Training Validation Dashboard</h1>
        <button
          onClick={() => setShowCreateSession(true)}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          New Validation Session
        </button>
      </div>

      {showCreateSession && (
        <div className="mb-6 p-4 border rounded-lg bg-gray-50">
          <h2 className="text-lg font-semibold mb-4">Create New Validation Session</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Session Name</label>
              <input
                type="text"
                value={newSessionData.name}
                onChange={(e) => setNewSessionData({...newSessionData, name: e.target.value})}
                className="w-full p-2 border rounded"
                placeholder="Enter session name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Unit Code</label>
              <input
                type="text"
                value={newSessionData.unit_code}
                onChange={(e) => setNewSessionData({...newSessionData, unit_code: e.target.value})}
                className="w-full p-2 border rounded"
                placeholder="e.g., BSBCMM411"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={newSessionData.description}
                onChange={(e) => setNewSessionData({...newSessionData, description: e.target.value})}
                className="w-full p-2 border rounded"
                rows={3}
                placeholder="Optional description"
              />
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleCreateSession}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
              >
                Create Session
              </button>
              <button
                onClick={() => setShowCreateSession(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-4">
        {sessions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No validation sessions found. Create your first session to get started.
          </div>
        ) : (
          sessions.map((session) => (
            <div key={session.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold">{session.name}</h3>
                  <p className="text-sm text-gray-600">
                    Unit: {session.unit_code} - {session.unit_title}
                  </p>
                  {session.description && (
                    <p className="text-sm text-gray-700 mt-1">{session.description}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-2">
                    Created: {new Date(session.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    session.status === 'completed' ? 'bg-green-100 text-green-800' :
                    session.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {session.status}
                  </span>
                  <button className="text-blue-500 hover:text-blue-700 text-sm">
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default TrainingValidationDashboard;
