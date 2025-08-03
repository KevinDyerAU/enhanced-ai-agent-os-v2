import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Clock, 
  User, 
  Zap, 
  CheckCircle, 
  AlertCircle,
  Search,
  Filter,
  Maximize,
  Brain,
  TrendingUp
} from 'lucide-react';

interface ActivityItem {
  id: string;
  agent_name: string;
  action: string;
  description: string;
  timestamp: string;
  status: 'completed' | 'failed' | 'in_progress';
  type: 'ideation' | 'design' | 'video' | 'validation' | 'approval';
  metadata?: Record<string, any>;
  details?: string;
}

interface AgentActivityStreamProps {
  agentId?: string;
  taskId?: string;
  timeRange?: string;
}

const AgentActivityStream: React.FC<AgentActivityStreamProps> = ({ 
  agentId, 
  taskId, 
  timeRange = '24h' 
}) => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [filteredActivities, setFilteredActivities] = useState<ActivityItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [expandedActivity, setExpandedActivity] = useState<string | null>(null);
  const [realTimeEnabled, setRealTimeEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const streamRef = useRef<EventSource | null>(null);

  useEffect(() => {
    fetchActivities();
    
    if (realTimeEnabled) {
      const params = new URLSearchParams();
      if (agentId) params.append('agent_id', agentId);
      if (taskId) params.append('task_id', taskId);
      
      const eventSource = new EventSource(`/api/activities/stream?${params}`);
      streamRef.current = eventSource;
      
      eventSource.onmessage = (event) => {
        try {
          const newActivity = JSON.parse(event.data);
          setActivities(prev => [newActivity, ...prev]);
        } catch (error) {
          console.error('Error parsing activity stream data:', error);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('Activity stream error:', error);
      };
      
      return () => {
        eventSource.close();
      };
    }
  }, [agentId, taskId, timeRange, realTimeEnabled]);

  useEffect(() => {
    filterActivities();
  }, [activities, searchTerm, selectedFilters]);

  const fetchActivities = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        time_range: timeRange,
        ...(agentId && { agent_id: agentId }),
        ...(taskId && { task_id: taskId })
      });
      
      const response = await fetch(`/api/audit-logs?${params}`);
      if (response.ok) {
        const data = await response.json();
        const transformedActivities = data.logs?.map((log: any) => ({
          id: log.id,
          agent_name: log.agent_name || 'System',
          action: log.action,
          description: log.details,
          timestamp: log.timestamp,
          status: 'completed',
          type: getActivityType(log.action),
          metadata: log.metadata,
          details: log.details
        })) || [];
        
        setActivities(transformedActivities);
      }
    } catch (error) {
      console.error('Error fetching activities:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActivityType = (action: string): ActivityItem['type'] => {
    if (action.includes('idea')) return 'ideation';
    if (action.includes('design')) return 'design';
    if (action.includes('video')) return 'video';
    if (action.includes('approved') || action.includes('rejected')) return 'approval';
    return 'validation';
  };

  const filterActivities = () => {
    let filtered = activities;
    
    if (searchTerm) {
      filtered = filtered.filter(activity => 
        activity.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        activity.agent_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        activity.action.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    if (selectedFilters.length > 0) {
      filtered = filtered.filter(activity => 
        selectedFilters.includes(activity.type) || 
        selectedFilters.includes(activity.status)
      );
    }
    
    setFilteredActivities(filtered);
  };

  const toggleFilter = (filter: string) => {
    setSelectedFilters(prev => 
      prev.includes(filter) 
        ? prev.filter(f => f !== filter)
        : [...prev, filter]
    );
  };

  const getStatusIcon = (status: ActivityItem['status']) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'in_progress': return <Clock className="h-4 w-4 text-blue-500" />;
      default: return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTypeColor = (type: ActivityItem['type']) => {
    const colors = {
      'ideation': 'bg-purple-100 text-purple-800',
      'design': 'bg-blue-100 text-blue-800',
      'video': 'bg-green-100 text-green-800',
      'validation': 'bg-yellow-100 text-yellow-800',
      'approval': 'bg-red-100 text-red-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getTypeIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'ideation': return <Brain className="h-4 w-4" />;
      case 'design': return <Zap className="h-4 w-4" />;
      case 'video': return <Activity className="h-4 w-4" />;
      case 'validation': return <CheckCircle className="h-4 w-4" />;
      case 'approval': return <User className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const ActivityItemComponent = ({ activity, isExpanded, onToggle }: {
    activity: ActivityItem;
    isExpanded: boolean;
    onToggle: () => void;
  }) => (
    <div className="border-l-2 border-gray-200 pl-4 pb-4 relative">
      <div className="absolute -left-2 top-0 w-4 h-4 bg-white border-2 border-gray-300 rounded-full" />
      
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {getStatusIcon(activity.status)}
            <span className="font-medium">{activity.description}</span>
            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(activity.type)}`}>
              {getTypeIcon(activity.type)}
              {activity.type}
            </span>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
            <span className="flex items-center gap-1">
              <User className="h-3 w-3" />
              {activity.agent_name}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {new Date(activity.timestamp).toLocaleString()}
            </span>
          </div>
          
          {isExpanded && activity.metadata && (
            <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
              <strong>Details:</strong>
              <pre className="mt-1 whitespace-pre-wrap">
                {JSON.stringify(activity.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
        
        <button
          className="ml-2 p-1 text-gray-400 hover:text-gray-600"
          onClick={onToggle}
        >
          <Maximize className="h-4 w-4" />
        </button>
      </div>
    </div>
  );

  const filterOptions = [
    { value: 'ideation', label: 'Ideation', color: 'purple' },
    { value: 'design', label: 'Design', color: 'blue' },
    { value: 'video', label: 'Video', color: 'green' },
    { value: 'validation', label: 'Validation', color: 'yellow' },
    { value: 'approval', label: 'Approval', color: 'red' },
    { value: 'completed', label: 'Completed', color: 'green' },
    { value: 'failed', label: 'Failed', color: 'red' },
    { value: 'in_progress', label: 'In Progress', color: 'blue' }
  ];

  return (
    <div className="w-full bg-white rounded-lg shadow-md">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Agent Activity Stream
          </h3>
          <div className="flex items-center gap-2">
            <button
              className={`px-3 py-1 rounded text-sm ${
                realTimeEnabled 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
              onClick={() => setRealTimeEnabled(!realTimeEnabled)}
            >
              {realTimeEnabled ? 'Live' : 'Paused'}
            </button>
            <button 
              className="px-3 py-1 rounded text-sm bg-gray-200 text-gray-700 hover:bg-gray-300"
              onClick={fetchActivities}
            >
              Refresh
            </button>
          </div>
        </div>
      </div>
      
      <div className="p-6">
        <div className="space-y-4">
          {/* Search and Filters */}
          <div className="flex flex-col gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search activities..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex flex-wrap gap-2">
              <span className="text-sm font-medium text-gray-700 flex items-center gap-1">
                <Filter className="h-4 w-4" />
                Filters:
              </span>
              {filterOptions.map((option) => (
                <button
                  key={option.value}
                  className={`px-2 py-1 rounded text-xs ${
                    selectedFilters.includes(option.value)
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                  onClick={() => toggleFilter(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Activity Timeline */}
          <div className="space-y-4">
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading activities...</p>
              </div>
            ) : filteredActivities.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No activities found</p>
                {searchTerm && (
                  <p className="text-sm">Try adjusting your search or filters</p>
                )}
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {filteredActivities.map((activity) => (
                  <ActivityItemComponent
                    key={activity.id}
                    activity={activity}
                    isExpanded={expandedActivity === activity.id}
                    onToggle={() => setExpandedActivity(
                      expandedActivity === activity.id ? null : activity.id
                    )}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {filteredActivities.length}
              </div>
              <div className="text-sm text-gray-600">Total Activities</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {filteredActivities.filter(a => a.status === 'completed').length}
              </div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {filteredActivities.filter(a => a.status === 'failed').length}
              </div>
              <div className="text-sm text-gray-600">Failed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {filteredActivities.filter(a => a.status === 'in_progress').length}
              </div>
              <div className="text-sm text-gray-600">In Progress</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentActivityStream;
