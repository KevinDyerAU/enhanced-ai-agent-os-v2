import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Plus, FileText, BarChart3, BookOpen } from 'lucide-react';

interface ValidationSession {
  id: string;
  name: string;
  description?: string;
  training_unit_id: string;
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface TrainingUnit {
  unit_code: string;
  title: string;
  description: string;
  elements: any[];
  performance_criteria: any[];
  knowledge_evidence: any[];
  foundation_skills: any[];
}

const TrainingValidationDashboard: React.FC = () => {
  const [sessions, setSessions] = useState<ValidationSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
      setLoading(true);
      const response = await fetch('http://localhost:8033/api/v1/validation-sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
        setError(null);
      } else {
        throw new Error(`Failed to fetch sessions: ${response.status}`);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
      setError(error instanceof Error ? error.message : 'Failed to load sessions');
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async () => {
    try {
      // First, retrieve the training unit
      const unitResponse = await fetch('http://localhost:8033/api/v1/training-units/retrieve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ unit_code: newSessionData.unit_code })
      });

      if (!unitResponse.ok) {
        throw new Error('Failed to retrieve training unit');
      }

      const unit: TrainingUnit = await unitResponse.json();

      // Create the validation session
      const sessionResponse = await fetch('http://localhost:8033/api/v1/validation-sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newSessionData.name,
          description: newSessionData.description,
          training_unit_id: unit.unit_code,
          created_by: 'current_user'
        })
      });

      if (sessionResponse.ok) {
        setShowCreateSession(false);
        setNewSessionData({ name: '', description: '', unit_code: '' });
        fetchSessions();
      } else {
        throw new Error('Failed to create session');
      }
    } catch (error) {
      console.error('Error creating session:', error);
      setError(error instanceof Error ? error.message : 'Failed to create session');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2">Loading validation sessions...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Training Validation System</h1>
          <p className="text-gray-600 mt-2">Manage training validation sessions and compliance reporting</p>
        </div>
        <Button onClick={() => setShowCreateSession(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          New Session
        </Button>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <p className="text-red-600">{error}</p>
            <Button onClick={fetchSessions} variant="outline" size="sm" className="mt-2">
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="sessions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="sessions">Validation Sessions</TabsTrigger>
          <TabsTrigger value="questions">Question Library</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="sessions" className="space-y-4">
          {showCreateSession && (
            <Card>
              <CardHeader>
                <CardTitle>Create New Validation Session</CardTitle>
                <CardDescription>
                  Start a new training validation session by specifying a training unit code
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Session Name</Label>
                    <Input
                      id="name"
                      value={newSessionData.name}
                      onChange={(e) => setNewSessionData({...newSessionData, name: e.target.value})}
                      placeholder="e.g., BSBCRT511 Validation"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="unit_code">Training Unit Code</Label>
                    <Input
                      id="unit_code"
                      value={newSessionData.unit_code}
                      onChange={(e) => setNewSessionData({...newSessionData, unit_code: e.target.value})}
                      placeholder="e.g., BSBCRT511"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (Optional)</Label>
                  <Textarea
                    id="description"
                    value={newSessionData.description}
                    onChange={(e) => setNewSessionData({...newSessionData, description: e.target.value})}
                    placeholder="Brief description of this validation session"
                  />
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleCreateSession}>Create Session</Button>
                  <Button variant="outline" onClick={() => setShowCreateSession(false)}>Cancel</Button>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid gap-4">
            {sessions.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No validation sessions yet</h3>
                  <p className="text-gray-600 mb-4">Create your first validation session to get started</p>
                  <Button onClick={() => setShowCreateSession(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Session
                  </Button>
                </CardContent>
              </Card>
            ) : (
              sessions.map((session) => (
                <Card key={session.id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle>{session.name}</CardTitle>
                        <CardDescription>{session.description}</CardDescription>
                      </div>
                      <Badge className={getStatusColor(session.status)}>
                        {session.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex justify-between items-center">
                      <div className="text-sm text-gray-600">
                        Created: {new Date(session.created_at).toLocaleDateString()}
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          <FileText className="h-4 w-4 mr-2" />
                          View Details
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="questions">
          <Card>
            <CardHeader>
              <CardTitle>Question Library</CardTitle>
              <CardDescription>Manage generated questions and assessment criteria</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">Question library functionality will be available here.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports">
          <Card>
            <CardHeader>
              <CardTitle>Validation Reports</CardTitle>
              <CardDescription>View and manage compliance reports</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">Report management functionality will be available here.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <Card>
            <CardHeader>
              <CardTitle>Analytics Dashboard</CardTitle>
              <CardDescription>View validation trends and insights</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">Analytics dashboard will be available here.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TrainingValidationDashboard;
