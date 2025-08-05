import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Input } from './components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  MessageSquare, 
  Users, 
  Filter,
  Search,
  Eye,
  Edit,
  MoreHorizontal,
  Calendar,
  ArrowUp
} from 'lucide-react';

const AirlockDashboard = ({ onItemSelect }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: 'all',
    priority: 'all',
    contentType: 'all',
    search: ''
  });
  const [stats, setStats] = useState({
    by_status: {},
    by_priority: {},
    by_content_type: {},
    overdue_count: 0
  });

  // Mock data for demonstration
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setItems([
        {
          id: '1',
          title: 'Training Validation Report - BSBWHS311',
          description: 'Comprehensive validation report for workplace health and safety unit',
          content_type: 'training_validation',
          source_service: 'training_validation',
          status: 'pending_review',
          priority: 'high',
          assigned_reviewer_id: 'reviewer1',
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          review_deadline: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
          revision_count: 0
        },
        {
          id: '2',
          title: 'Creative Asset - Marketing Campaign',
          description: 'New product launch campaign materials',
          content_type: 'creative_asset',
          source_service: 'ideation',
          status: 'requires_changes',
          priority: 'medium',
          assigned_reviewer_id: 'reviewer2',
          created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          review_deadline: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
          revision_count: 2
        },
        {
          id: '3',
          title: 'Design System Documentation',
          description: 'Updated design system guidelines and components',
          content_type: 'document',
          source_service: 'design',
          status: 'approved',
          priority: 'low',
          assigned_reviewer_id: 'reviewer1',
          created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          reviewed_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          revision_count: 1
        }
      ]);
      
      setStats({
        by_status: {
          pending_review: 1,
          requires_changes: 1,
          approved: 1,
          rejected: 0
        },
        by_priority: {
          high: 1,
          medium: 1,
          low: 1,
          urgent: 0
        },
        by_content_type: {
          training_validation: 1,
          creative_asset: 1,
          document: 1
        },
        overdue_count: 0
      });
      
      setLoading(false);
    }, 1000);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending_review':
        return <Clock className="h-4 w-4" />;
      case 'approved':
        return <CheckCircle className="h-4 w-4" />;
      case 'rejected':
        return <XCircle className="h-4 w-4" />;
      case 'requires_changes':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending_review':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'requires_changes':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-500';
      case 'high':
        return 'bg-orange-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const filteredItems = items.filter(item => {
    if (filters.status !== 'all' && item.status !== filters.status) return false;
    if (filters.priority !== 'all' && item.priority !== filters.priority) return false;
    if (filters.contentType !== 'all' && item.content_type !== filters.contentType) return false;
    if (filters.search && !item.title.toLowerCase().includes(filters.search.toLowerCase()) && 
        !item.description.toLowerCase().includes(filters.search.toLowerCase())) return false;
    return true;
  });

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isOverdue = (deadline) => {
    return new Date(deadline) < new Date();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_status.pending_review || 0}</div>
              <p className="text-xs text-muted-foreground">
                Items awaiting review
              </p>
            </CardContent>
          </Card>
        </div>

        <div
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Approved</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_status.approved || 0}</div>
              <p className="text-xs text-muted-foreground">
                Successfully approved
              </p>
            </CardContent>
          </Card>
        </div>

        <div
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Needs Changes</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_status.requires_changes || 0}</div>
              <p className="text-xs text-muted-foreground">
                Requiring revisions
              </p>
            </CardContent>
          </Card>
        </div>

        <div
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Overdue</CardTitle>
              <XCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.overdue_count || 0}</div>
              <p className="text-xs text-muted-foreground">
                Past deadline
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search items..."
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <Select value={filters.status} onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="pending_review">Pending Review</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="requires_changes">Requires Changes</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Priority</label>
              <Select value={filters.priority} onValueChange={(value) => setFilters(prev => ({ ...prev, priority: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="All priorities" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priorities</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Content Type</label>
              <Select value={filters.contentType} onValueChange={(value) => setFilters(prev => ({ ...prev, contentType: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="training_validation">Training Validation</SelectItem>
                  <SelectItem value="creative_asset">Creative Asset</SelectItem>
                  <SelectItem value="document">Document</SelectItem>
                  <SelectItem value="design">Design</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Items List */}
      <Card>
        <CardHeader>
          <CardTitle>Airlock Items ({filteredItems.length})</CardTitle>
          <CardDescription>
            Items currently in the review process
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <>
              {filteredItems.map((item, index) => (
                <div
                  key={item.id}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onItemSelect && onItemSelect(item)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${getPriorityColor(item.priority)}`} />
                        <h3 className="font-semibold text-lg">{item.title}</h3>
                        <Badge variant="outline" className={getStatusColor(item.status)}>
                          <div className="flex items-center gap-1">
                            {getStatusIcon(item.status)}
                            {item.status.replace('_', ' ')}
                          </div>
                        </Badge>
                        {item.revision_count > 0 && (
                          <Badge variant="secondary">
                            Rev {item.revision_count}
                          </Badge>
                        )}
                      </div>
                      
                      <p className="text-muted-foreground">{item.description}</p>
                      
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          Created {formatDate(item.created_at)}
                        </div>
                        {item.review_deadline && (
                          <div className={`flex items-center gap-1 ${isOverdue(item.review_deadline) ? 'text-red-600' : ''}`}>
                            <Clock className="h-4 w-4" />
                            Due {formatDate(item.review_deadline)}
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <Users className="h-4 w-4" />
                          {item.assigned_reviewer_id || 'Unassigned'}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm">
                        <MessageSquare className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </>
            
            {filteredItems.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No items match your current filters.
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AirlockDashboard;

