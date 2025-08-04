import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

interface ValidationReport {
  id: string;
  session_id: string;
  report_type: string;
  title: string;
  summary: string;
  overall_score: number;
  validation_results: any;
  recommendations: string[];
  generated_at: string;
  status: string;
}

interface ReportViewerProps {
  reportId?: string;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({ reportId }) => {
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [loading, setLoading] = useState(false);

  const mockReport: ValidationReport = {
    id: '1',
    session_id: 'session-1',
    report_type: 'comprehensive',
    title: 'BSBCMM411 Validation Report',
    summary: 'Comprehensive validation analysis of training materials for BSBCMM411 - Make presentations.',
    overall_score: 78.5,
    validation_results: {
      assessment_conditions: {
        score: 85,
        gaps: 3,
        status: 'good'
      },
      knowledge_evidence: {
        score: 72,
        gaps: 5,
        status: 'needs_improvement'
      },
      performance_evidence: {
        score: 80,
        gaps: 2,
        status: 'good'
      },
      foundation_skills: {
        score: 75,
        gaps: 4,
        status: 'satisfactory'
      }
    },
    recommendations: [
      'Add more specific assessment environment details',
      'Include additional knowledge evidence for digital presentation tools',
      'Clarify performance criteria for audience engagement',
      'Enhance foundation skills integration for numeracy components'
    ],
    generated_at: '2024-08-03T22:00:00Z',
    status: 'completed'
  };

  useEffect(() => {
    if (reportId) {
      setReport(mockReport);
    }
  }, [reportId]);

  if (!report) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-gray-500">Select a report to view details</p>
        </CardContent>
      </Card>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusBadge = (status: string) => {
    const variants: { [key: string]: 'default' | 'outline' } = {
      'good': 'default',
      'satisfactory': 'default',
      'needs_improvement': 'outline'
    };
    return variants[status] || 'outline';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold">{report.title}</h2>
          <p className="text-gray-600 mt-1">{report.summary}</p>
          <div className="flex items-center gap-4 mt-2">
            <Badge>{report.report_type}</Badge>
            <span className="text-sm text-gray-500">
              Generated: {new Date(report.generated_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-3xl font-bold ${getScoreColor(report.overall_score)}`}>
            {report.overall_score.toFixed(1)}%
          </div>
          <p className="text-sm text-gray-500">Overall Score</p>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="details">Detailed Results</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(report.validation_results).map(([key, result]: [string, any]) => (
              <Card key={key}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">
                    {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${getScoreColor(result.score)}`}>
                    {result.score}%
                  </div>
                  <div className="flex justify-between items-center mt-2">
                    <Badge variant={getStatusBadge(result.status)}>
                      {result.status.replace('_', ' ')}
                    </Badge>
                    <span className="text-sm text-gray-500">{result.gaps} gaps</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="details" className="space-y-4">
          {Object.entries(report.validation_results).map(([key, result]: [string, any]) => (
            <Card key={key}>
              <CardHeader>
                <CardTitle>
                  {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </CardTitle>
                <CardDescription>
                  Score: {result.score}% | Status: {result.status.replace('_', ' ')} | Gaps: {result.gaps}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Detailed analysis and findings for {key.replace('_', ' ')} validation would appear here.
                  This includes specific gaps identified, compliance status, and detailed scoring breakdown.
                </p>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Improvement Recommendations</CardTitle>
              <CardDescription>
                Actionable suggestions to improve your training materials
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {report.recommendations.map((recommendation, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                    <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-sm font-medium text-blue-600">
                      {index + 1}
                    </div>
                    <p className="text-sm">{recommendation}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="export" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Export Report</CardTitle>
              <CardDescription>
                Download this report in various formats
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button variant="outline" className="h-20 flex flex-col">
                  <span className="font-medium">PDF Report</span>
                  <span className="text-sm text-gray-500">Formatted document</span>
                </Button>
                <Button variant="outline" className="h-20 flex flex-col">
                  <span className="font-medium">Excel Export</span>
                  <span className="text-sm text-gray-500">Data analysis</span>
                </Button>
                <Button variant="outline" className="h-20 flex flex-col">
                  <span className="font-medium">JSON Data</span>
                  <span className="text-sm text-gray-500">Raw data export</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
