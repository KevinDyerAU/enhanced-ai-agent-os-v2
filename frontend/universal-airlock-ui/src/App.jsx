import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Shield, 
  MessageSquare, 
  Eye, 
  BarChart3, 
  Settings,
  ArrowLeft,
  Bell,
  User
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import AirlockDashboard from './AirlockDashboard';
import ValidationViewer from './ValidationViewer';
import ChatInterface from './ChatInterface';
import './App.css';

function App() {
  const [selectedItem, setSelectedItem] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [notifications, setNotifications] = useState(3);

  const handleItemSelect = (item) => {
    setSelectedItem(item);
    setActiveTab('viewer');
  };

  const handleBackToDashboard = () => {
    setSelectedItem(null);
    setActiveTab('dashboard');
  };

  const handleApprove = (itemId, feedback) => {
    console.log('Approving item:', itemId, 'with feedback:', feedback);
    // Handle approval logic
  };

  const handleReject = (itemId, feedback) => {
    console.log('Rejecting item:', itemId, 'with feedback:', feedback);
    // Handle rejection logic
  };

  const handleRequestChanges = (itemId, feedback) => {
    console.log('Requesting changes for item:', itemId, 'with feedback:', feedback);
    // Handle request changes logic
  };

  const handleAddFeedback = (itemId, feedback) => {
    console.log('Adding feedback to item:', itemId, 'feedback:', feedback);
    // Handle add feedback logic
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Shield className="h-8 w-8 text-primary" />
                <div>
                  <h1 className="text-2xl font-bold">Universal Airlock System</h1>
                  <p className="text-sm text-muted-foreground">AI Agent Operating System</p>
                </div>
              </div>
              
              {selectedItem && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-2"
                >
                  <Button variant="ghost" size="sm" onClick={handleBackToDashboard}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Dashboard
                  </Button>
                  <div className="h-6 w-px bg-border" />
                  <Badge variant="outline">{selectedItem.title}</Badge>
                </motion.div>
              )}
            </div>

            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" className="relative">
                <Bell className="h-5 w-5" />
                {notifications > 0 && (
                  <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 text-xs">
                    {notifications}
                  </Badge>
                )}
              </Button>
              <Button variant="ghost" size="sm">
                <User className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <AnimatePresence mode="wait">
          {!selectedItem ? (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-4 max-w-md">
                  <TabsTrigger value="dashboard" className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Dashboard
                  </TabsTrigger>
                  <TabsTrigger value="chat" className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    Chat
                  </TabsTrigger>
                  <TabsTrigger value="analytics" className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Analytics
                  </TabsTrigger>
                  <TabsTrigger value="settings" className="flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    Settings
                  </TabsTrigger>
                </TabsList>

                <div className="mt-6">
                  <TabsContent value="dashboard">
                    <AirlockDashboard onItemSelect={handleItemSelect} />
                  </TabsContent>

                  <TabsContent value="chat">
                    <Card>
                      <CardHeader>
                        <CardTitle>Global Chat</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-muted-foreground">
                          Select an item from the dashboard to start a conversation.
                        </p>
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="analytics">
                    <Card>
                      <CardHeader>
                        <CardTitle>Analytics & Reporting</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-muted-foreground">
                          Analytics dashboard coming soon...
                        </p>
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="settings">
                    <Card>
                      <CardHeader>
                        <CardTitle>System Settings</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-muted-foreground">
                          Configuration options coming soon...
                        </p>
                      </CardContent>
                    </Card>
                  </TabsContent>
                </div>
              </Tabs>
            </motion.div>
          ) : (
            <motion.div
              key="item-view"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-2 max-w-md">
                  <TabsTrigger value="viewer" className="flex items-center gap-2">
                    <Eye className="h-4 w-4" />
                    Validation
                  </TabsTrigger>
                  <TabsTrigger value="chat" className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    Chat & Feedback
                  </TabsTrigger>
                </TabsList>

                <div className="mt-6">
                  <TabsContent value="viewer">
                    <ValidationViewer
                      item={selectedItem}
                      onApprove={handleApprove}
                      onReject={handleReject}
                      onRequestChanges={handleRequestChanges}
                      onAddFeedback={handleAddFeedback}
                    />
                  </TabsContent>

                  <TabsContent value="chat">
                    <Card className="h-[800px]">
                      <ChatInterface
                        itemId={selectedItem.id}
                        currentUser={{ id: 'user1', name: 'John Doe' }}
                      />
                    </Card>
                  </TabsContent>
                </div>
              </Tabs>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="border-t bg-card mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div>
              © 2024 Universal Airlock System - AI Agent Operating System
            </div>
            <div className="flex items-center gap-4">
              <span>Version 1.0.0</span>
              <Badge variant="outline" className="text-green-600 border-green-200">
                System Healthy
              </Badge>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

