import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

interface AnalyticsData {
  totalSessions: number;
  totalQuestions: number;
  totalReports: number;
  averageScore: number;
  trendsData: {
    period: string;
    sessions: number;
    avgScore: number;
  }[];
  topUnits: {
    unitCode: string;
    sessions: number;
    avgScore: number;
  }[];
  validationTrends: {
    category: string;
    avgScore: number;
    trend: 'up' | 'down' | 'stable';
  }[];
}

export const AnalyticsDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [timeRange, setTimeRange] = useState('30d');

  const mockAnalytics: AnalyticsData = {
    totalSessions: 156,
    totalQuestions: 1247,
    totalReports: 89,
    averageScore: 76.8,
    trendsData: [
      { period: 'Week 1', sessions: 12, avgScore: 74.2 },
      { period: 'Week 2', sessions: 18, avgScore: 76.1 },
      { period: 'Week 3', sessions: 22, avgScore: 78.5 },
      { period: 'Week 4', sessions: 19, avgScore: 77.3 }
    ],
    topUnits: [
      { unitCode: 'BSBCMM411', sessions: 34, avgScore: 82.1 },
      { unitCode: 'BSBLDR411', sessions: 28, avgScore: 79.4 },
      { unitCode: 'BSBWHS411', sessions: 25, avgScore: 75.8 },
      { unitCode: 'BSBMGT411', sessions: 22, avgScore: 73.2 },
      { unitCode: 'BSBFIN401', sessions: 18, avgScore: 71.6 }
    ],
    validationTrends: [
      { category: 'Assessment Conditions', avgScore: 78.5, trend: 'up' },
      { category: 'Knowledge Evidence', avgScore: 74.2, trend: 'stable' },
      { category: 'Performance Evidence', avgScore: 79.1, trend: 'up' },
      { category: 'Foundation Skills', avgScore: 75.8, trend: 'down' }
    ]
  };

  useEffect(() => {
    setAnalytics(mockAnalytics);
  }, [timeRange]);

  if (!analytics) {
    return <div>Loading analytics...</div>;
  }

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return '↗️';
      case 'down': return '↘️';
      case 'stable': return '→';
    }
  };

  const getTrendColor = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      case 'stable': return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Analytics Dashboard</h2>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-3 py-2 border rounded-md"
        >
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
          <option value="1y">Last year</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.totalSessions}</div>
            <p className="text-xs text-gray-500">Validation sessions completed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Questions Generated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.totalQuestions}</div>
            <p className="text-xs text-gray-500">SMART questions created</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Reports Generated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.totalReports}</div>
            <p className="text-xs text-gray-500">Comprehensive reports</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Average Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.averageScore}%</div>
            <p className="text-xs text-gray-500">Across all validations</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="trends" className="w-full">
        <TabsList>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="units">Top Units</TabsTrigger>
          <TabsTrigger value="validation">Validation Categories</TabsTrigger>
          <TabsTrigger value="usage">Usage Patterns</TabsTrigger>
        </TabsList>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Session Trends</CardTitle>
              <CardDescription>Validation sessions and average scores over time</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.trendsData.map((trend, index) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <div>
                      <span className="font-medium">{trend.period}</span>
                      <p className="text-sm text-gray-600">{trend.sessions} sessions</p>
                    </div>
                    <div className="text-right">
                      <span className="font-medium">{trend.avgScore}%</span>
                      <p className="text-sm text-gray-600">avg score</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="units" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Most Validated Units</CardTitle>
              <CardDescription>Units with the highest validation activity</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.topUnits.map((unit, index) => (
                  <div key={unit.unitCode} className="flex justify-between items-center p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm font-medium text-blue-600">
                        {index + 1}
                      </div>
                      <div>
                        <span className="font-medium">{unit.unitCode}</span>
                        <p className="text-sm text-gray-600">{unit.sessions} sessions</p>
                      </div>
                    </div>
                    <Badge variant="outline">{unit.avgScore}% avg</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="validation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Validation Category Performance</CardTitle>
              <CardDescription>Average scores and trends by validation category</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.validationTrends.map((category) => (
                  <div key={category.category} className="flex justify-between items-center p-3 border rounded-lg">
                    <div>
                      <span className="font-medium">{category.category}</span>
                      <p className="text-sm text-gray-600">Average performance</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{category.avgScore}%</span>
                      <span className={getTrendColor(category.trend)}>
                        {getTrendIcon(category.trend)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Usage Patterns</CardTitle>
              <CardDescription>Insights into how the system is being used</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-medium text-blue-900">Peak Usage Hours</h4>
                    <p className="text-sm text-blue-700 mt-1">9 AM - 11 AM, 2 PM - 4 PM</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-900">Most Active Day</h4>
                    <p className="text-sm text-green-700 mt-1">Tuesday (28% of sessions)</p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <h4 className="font-medium text-purple-900">Avg Session Duration</h4>
                    <p className="text-sm text-purple-700 mt-1">24 minutes</p>
                  </div>
                  <div className="p-4 bg-orange-50 rounded-lg">
                    <h4 className="font-medium text-orange-900">Question Export Rate</h4>
                    <p className="text-sm text-orange-700 mt-1">67% of generated questions</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
