import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { QuestionLibrary } from './QuestionLibrary';
import { ReportViewer } from './ReportViewer';
import { AnalyticsDashboard } from './AnalyticsDashboard';

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
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Training Validation Dashboard</h1>
          <p className="text-gray-600 mt-2">Validate training materials against official unit requirements</p>
        </div>

        <Tabs defaultValue="sessions" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="sessions">Validation Sessions</TabsTrigger>
            <TabsTrigger value="questions">Question Library</TabsTrigger>
            <TabsTrigger value="reports">Reports</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="sessions" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Validation Sessions</h2>
              <Button onClick={() => setShowCreateSession(true)}>
                New Validation Session
              </Button>
            </div>

            {showCreateSession && (
              <Card>
                <CardHeader>
                  <CardTitle>Create New Validation Session</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="sessionName">Session Name</Label>
                    <Input
                      id="sessionName"
                      placeholder="Enter session name"
                      value={newSessionData.name}
                      onChange={(e) => setNewSessionData({...newSessionData, name: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="unitCode">Unit Code</Label>
                    <Input
                      id="unitCode"
                      placeholder="e.g., BSBCMM411"
                      value={newSessionData.unit_code}
                      onChange={(e) => setNewSessionData({...newSessionData, unit_code: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      placeholder="Optional description"
                      value={newSessionData.description}
                      onChange={(e) => setNewSessionData({...newSessionData, description: e.target.value})}
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleCreateSession}>Create Session</Button>
                    <Button variant="outline" onClick={() => setShowCreateSession(false)}>Cancel</Button>
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="grid gap-6">
              {sessions.length === 0 ? (
                <Card>
                  <CardContent className="p-8 text-center">
                    <p className="text-gray-500">No validation sessions found. Create your first session to get started.</p>
                  </CardContent>
                </Card>
              ) : (
                sessions.map((session) => (
                  <Card key={session.id} className="hover:shadow-md transition-shadow">
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle>{session.name}</CardTitle>
                          <CardDescription>
                            Unit: {session.unit_code} - {session.unit_title}
                          </CardDescription>
                        </div>
                        <span className={`px-2 py-1 rounded text-sm ${
                          session.status === 'completed' ? 'bg-green-100 text-green-800' :
                          session.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {session.status}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {session.description && (
                        <p className="text-gray-600 mb-4">{session.description}</p>
                      )}
                      <p className="text-sm text-gray-500 mb-4">
                        Created: {new Date(session.created_at).toLocaleDateString()}
                      </p>
                      <div className="flex gap-2">
                        <Button size="sm">View Details</Button>
                        <Button size="sm" variant="outline">Upload Documents</Button>
                        <Button size="sm" variant="outline">Run Validation</Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          <TabsContent value="questions">
            <QuestionLibrary />
          </TabsContent>

          <TabsContent value="reports">
            <ReportViewer reportId="1" />
          </TabsContent>

          <TabsContent value="analytics">
            <AnalyticsDashboard />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default TrainingValidationDashboard;
