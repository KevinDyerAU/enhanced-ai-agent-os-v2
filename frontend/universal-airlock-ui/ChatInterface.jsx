import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Send, 
  Smile, 
  Paperclip, 
  MoreVertical, 
  ThumbsUp, 
  ThumbsDown,
  MessageSquare,
  User,
  Bot,
  Clock,
  CheckCircle2,
  AlertCircle,
  Users
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ChatInterface = ({ itemId, currentUser = { id: 'user1', name: 'John Doe' } }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [messageType, setMessageType] = useState('text');
  const [participants, setParticipants] = useState([]);
  const [typingUsers, setTypingUsers] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [ws, setWs] = useState(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Mock data for demonstration
  useEffect(() => {
    // Simulate initial messages
    setMessages([
      {
        id: '1',
        sender_type: 'system',
        sender_id: 'system',
        sender_name: 'System',
        message_type: 'system',
        content: 'Airlock item created for review: Training Validation Report - BSBWHS311',
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
      },
      {
        id: '2',
        sender_type: 'human',
        sender_id: 'reviewer1',
        sender_name: 'Sarah Wilson',
        message_type: 'text',
        content: 'I\'ve started reviewing this training validation report. The overall structure looks good.',
        created_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString()
      },
      {
        id: '3',
        sender_type: 'human',
        sender_id: 'reviewer1',
        sender_name: 'Sarah Wilson',
        message_type: 'feedback',
        content: 'Feedback: suggestion',
        metadata: {
          feedback_type: 'suggestion',
          feedback_data: {
            section: 'Assessment Conditions',
            suggestion: 'Consider adding more specific workplace scenarios'
          },
          severity: 'medium'
        },
        created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString()
      },
      {
        id: '4',
        sender_type: 'agent',
        sender_id: 'validation_agent',
        sender_name: 'Validation Agent',
        message_type: 'text',
        content: 'Thank you for the feedback. I\'ll incorporate more specific workplace scenarios in the Assessment Conditions section.',
        created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString()
      }
    ]);

    setParticipants([
      { user_id: 'reviewer1', name: 'Sarah Wilson', last_seen: new Date().toISOString() },
      { user_id: 'validation_agent', name: 'Validation Agent', last_seen: new Date().toISOString() },
      { user_id: currentUser.id, name: currentUser.name, last_seen: new Date().toISOString() }
    ]);

    // Simulate WebSocket connection
    setIsConnected(true);
  }, [itemId, currentUser]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = () => {
    if (!newMessage.trim()) return;

    const message = {
      id: Date.now().toString(),
      sender_type: 'human',
      sender_id: currentUser.id,
      sender_name: currentUser.name,
      message_type: messageType,
      content: newMessage,
      created_at: new Date().toISOString(),
      metadata: messageType === 'feedback' ? {
        feedback_type: 'comment',
        feedback_data: { comment: newMessage }
      } : {}
    };

    setMessages(prev => [...prev, message]);
    setNewMessage('');
    setMessageType('text');

    // Simulate sending via WebSocket
    console.log('Sending message:', message);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTyping = () => {
    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Simulate typing indicator
    if (!typingUsers.includes(currentUser.id)) {
      setTypingUsers(prev => [...prev, currentUser.id]);
    }

    // Set timeout to remove typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      setTypingUsers(prev => prev.filter(id => id !== currentUser.id));
    }, 3000);
  };

  const addReaction = (messageId, reaction) => {
    // Simulate adding reaction
    console.log('Adding reaction:', { messageId, reaction, userId: currentUser.id });
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getMessageIcon = (senderType, messageType) => {
    if (messageType === 'system') return <AlertCircle className="h-4 w-4" />;
    if (senderType === 'agent') return <Bot className="h-4 w-4" />;
    return <User className="h-4 w-4" />;
  };

  const getMessageBubbleClass = (senderType, senderId) => {
    if (senderType === 'system') {
      return 'bg-muted text-muted-foreground border border-border';
    }
    if (senderId === currentUser.id) {
      return 'bg-primary text-primary-foreground ml-auto';
    }
    return 'bg-card text-card-foreground border border-border';
  };

  const renderFeedbackMessage = (message) => {
    const { feedback_type, feedback_data, severity } = message.metadata;
    
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Badge variant={severity === 'high' ? 'destructive' : severity === 'medium' ? 'default' : 'secondary'}>
            {feedback_type}
          </Badge>
          {severity && (
            <Badge variant="outline" className="text-xs">
              {severity} priority
            </Badge>
          )}
        </div>
        {feedback_data.section && (
          <p className="text-sm font-medium">Section: {feedback_data.section}</p>
        )}
        {feedback_data.suggestion && (
          <p className="text-sm">{feedback_data.suggestion}</p>
        )}
        {feedback_data.comment && (
          <p className="text-sm">{feedback_data.comment}</p>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Chat & Feedback
            {isConnected ? (
              <Badge variant="outline" className="text-green-600 border-green-200">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Connected
              </Badge>
            ) : (
              <Badge variant="outline" className="text-red-600 border-red-200">
                <AlertCircle className="h-3 w-3 mr-1" />
                Disconnected
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{participants.length} participants</span>
          </div>
        </div>
      </CardHeader>

      {/* Participants */}
      <div className="px-6 py-2 border-b bg-muted/50">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Participants:</span>
          {participants.map((participant, index) => (
            <Badge key={participant.user_id} variant="secondary" className="text-xs">
              {participant.name}
            </Badge>
          ))}
        </div>
      </div>

      {/* Messages */}
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex ${message.sender_id === currentUser.id ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[70%] rounded-lg p-3 ${getMessageBubbleClass(message.sender_type, message.sender_id)}`}>
                {message.sender_id !== currentUser.id && (
                  <div className="flex items-center gap-2 mb-2">
                    {getMessageIcon(message.sender_type, message.message_type)}
                    <span className="text-sm font-medium">{message.sender_name}</span>
                    <span className="text-xs opacity-70">{formatTime(message.created_at)}</span>
                  </div>
                )}
                
                <div className="space-y-2">
                  {message.message_type === 'feedback' ? (
                    renderFeedbackMessage(message)
                  ) : (
                    <p className="text-sm">{message.content}</p>
                  )}
                </div>

                {message.sender_id === currentUser.id && (
                  <div className="flex justify-end mt-2">
                    <span className="text-xs opacity-70">{formatTime(message.created_at)}</span>
                  </div>
                )}

                {/* Reaction buttons */}
                <div className="flex items-center gap-1 mt-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2"
                    onClick={() => addReaction(message.id, '👍')}
                  >
                    <ThumbsUp className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2"
                    onClick={() => addReaction(message.id, '👎')}
                  >
                    <ThumbsDown className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicators */}
        {typingUsers.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-2 text-sm text-muted-foreground"
          >
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span>
              {typingUsers.length === 1 ? 'Someone is' : `${typingUsers.length} people are`} typing...
            </span>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </CardContent>

      {/* Message Input */}
      <div className="border-t p-4 space-y-3">
        {/* Message Type Selector */}
        <div className="flex items-center gap-2">
          <Select value={messageType} onValueChange={setMessageType}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="text">💬 Message</SelectItem>
              <SelectItem value="feedback">📝 Feedback</SelectItem>
              <SelectItem value="suggestion">💡 Suggestion</SelectItem>
              <SelectItem value="approval">✅ Approval</SelectItem>
              <SelectItem value="rejection">❌ Rejection</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Input Area */}
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Textarea
              placeholder={`Type a ${messageType}...`}
              value={newMessage}
              onChange={(e) => {
                setNewMessage(e.target.value);
                handleTyping();
              }}
              onKeyPress={handleKeyPress}
              className="min-h-[60px] resize-none"
              rows={2}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Button variant="ghost" size="sm">
              <Paperclip className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm">
              <Smile className="h-4 w-4" />
            </Button>
            <Button 
              onClick={handleSendMessage}
              disabled={!newMessage.trim()}
              size="sm"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

