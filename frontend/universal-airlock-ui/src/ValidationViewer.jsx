import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Progress from './progress.jsx';
import Textarea from './textarea.jsx';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  FileText, 
  Download, 
  Edit,
  Eye,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  RefreshCw,
  Target,
  BookOpen,
  Award,
  Users,
  Settings
} from 'lucide-react';
import { motion } from 'framer-motion';

const ValidationViewer = ({ item, onApprove, onReject, onRequestChanges, onAddFeedback }) => {
  const [validationResults, setValidationResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSection, setSelectedSection] = useState('overview');
  const [feedbackText, setFeedbackText] = useState('');

  // Mock validation results
  useEffect(() => {
    setTimeout(() => {
      setValidationResults({
        overall_score: 85,
        status: 'requires_changes',
        validations: {
          assessment_conditions: {
            status: 'passed',
            score: 90,
            gaps: [],
            recommendations: ['Consider adding more specific workplace scenarios']
          },
          elements_performance_criteria: {
            status: 'failed',
            score: 70,
            gaps: [
              'Element 1.2 - Performance criteria not fully addressed',
              'Element 2.1 - Missing specific assessment methods'
            ],
            recommendations: [
              'Add detailed assessment methods for each performance criteria',
              'Ensure all elements are explicitly covered'
            ]
          },
          performance_evidence: {
            status: 'passed',
            score: 95,
            gaps: [],
            recommendations: ['Excellent coverage of performance evidence requirements']
          },
          knowledge_evidence: {
            status: 'warning',
            score: 80,
            gaps: ['Some knowledge areas could be more detailed'],
            recommendations: ['Expand on workplace safety regulations section']
          },
          foundation_skills: {
            status: 'passed',
            score: 88,
            gaps: [],
            recommendations: ['Good integration of foundation skills']
          }
        },
        generated_questions: [
          {
            id: 'q1',
            question: 'Describe the process for conducting a workplace hazard identification.',
            baseline_answer: 'A systematic approach involving visual inspection, consultation with workers, review of incident reports, and documentation of findings.',
            element: '1.1',
            performance_criteria: ['1.1.1', '1.1.2']
          },
          {
            id: 'q2',
            question: 'What are the key components of a risk assessment matrix?',
            baseline_answer: 'Likelihood, consequence, risk rating, and control measures.',
            element: '2.1',
            performance_criteria: ['2.1.1', '2.1.3']
          }
        ],
        document_analysis: {
          total_pages: 45,
          sections_analyzed: 12,
          compliance_percentage: 85,
          missing_sections: ['Reasonable adjustment strategies', 'Industry-specific examples']
        }
      });
      setLoading(false);
    }, 1000);
  }, [item]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'passed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'passed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleApprove = () => {
    onApprove && onApprove(item.id, feedbackText);
    setFeedbackText('');
  };

  const handleReject = () => {
    onReject && onReject(item.id, feedbackText);
    setFeedbackText('');
  };

  const handleRequestChanges = () => {
    onRequestChanges && onRequestChanges(item.id, feedbackText);
    setFeedbackText('');
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
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <CardTitle className="text-2xl">{item.title}</CardTitle>
              <CardDescription>{item.description}</CardDescription>
              <div className="flex items-center gap-4">
                <Badge variant="outline" className={getStatusColor(item.status)}>
                  {item.status.replace('_', ' ')}
                </Badge>
                <Badge variant="secondary">
                  {item.content_type.replace('_', ' ')}
                </Badge>
                <Badge variant="outline">
                  Priority: {item.priority}
                </Badge>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Re-validate
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Overall Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Overall Validation Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">{validationResults.overall_score}%</span>
              <Badge className={getStatusColor(validationResults.status)}>
                {validationResults.status.replace('_', ' ')}
              </Badge>
            </div>
            <Progress value={validationResults.overall_score} className="h-3" />
            <p className="text-sm text-muted-foreground">
              Based on comprehensive analysis of all validation criteria
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Validation Details */}
      <Tabs value={selectedSection} onValueChange={setSelectedSection}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="validations">Validations</TabsTrigger>
          <TabsTrigger value="questions">Questions</TabsTrigger>
          <TabsTrigger value="document">Document</TabsTrigger>
          <TabsTrigger value="actions">Actions</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(validationResults.validations).map(([key, validation]) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-medium">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </CardTitle>
                      {getStatusIcon(validation.status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-2xl font-bold">{validation.score}%</span>
                        <Badge variant="outline" className={getStatusColor(validation.status)}>
                          {validation.status}
                        </Badge>
                      </div>
                      <Progress value={validation.score} className="h-2" />
                      {validation.gaps.length > 0 && (
                        <p className="text-xs text-red-600">
                          {validation.gaps.length} gap(s) identified
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="validations" className="space-y-4">
          {Object.entries(validationResults.validations).map(([key, validation]) => (
            <Card key={key}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    {getStatusIcon(validation.status)}
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-semibold">{validation.score}%</span>
                    <Badge className={getStatusColor(validation.status)}>
                      {validation.status}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <Progress value={validation.score} className="h-2" />
                
                {validation.gaps.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-red-600">Identified Gaps:</h4>
                    <ul className="space-y-1">
                      {validation.gaps.map((gap, index) => (
                        <li key={index} className="text-sm text-red-600 flex items-start gap-2">
                          <XCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          {gap}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {validation.recommendations.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-blue-600">Recommendations:</h4>
                    <ul className="space-y-1">
                      {validation.recommendations.map((rec, index) => (
                        <li key={index} className="text-sm text-blue-600 flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="questions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Generated SMART Questions
              </CardTitle>
              <CardDescription>
                AI-generated questions based on the training unit requirements
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {validationResults.generated_questions.map((question, index) => (
                  <Card key={question.id} className="border-l-4 border-l-blue-500">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-base">Question {index + 1}</CardTitle>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">Element {question.element}</Badge>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div>
                        <h4 className="font-medium mb-2">Question:</h4>
                        <p className="text-sm">{question.question}</p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-2">Baseline Answer:</h4>
                        <p className="text-sm text-muted-foreground">{question.baseline_answer}</p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-2">Performance Criteria:</h4>
                        <div className="flex gap-2">
                          {question.performance_criteria.map(pc => (
                            <Badge key={pc} variant="secondary" className="text-xs">
                              {pc}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="document" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Document Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Document Statistics</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Total Pages:</span>
                        <span className="font-medium">{validationResults.document_analysis.total_pages}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Sections Analyzed:</span>
                        <span className="font-medium">{validationResults.document_analysis.sections_analyzed}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Compliance:</span>
                        <span className="font-medium">{validationResults.document_analysis.compliance_percentage}%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <Progress value={validationResults.document_analysis.compliance_percentage} className="h-3" />
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Missing Sections</h4>
                    <ul className="space-y-1">
                      {validationResults.document_analysis.missing_sections.map((section, index) => (
                        <li key={index} className="text-sm text-red-600 flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          {section}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="actions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Review Actions
              </CardTitle>
              <CardDescription>
                Provide feedback and make decisions on this validation
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Feedback Comments</label>
                <Textarea
                  placeholder="Add your feedback, suggestions, or comments..."
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  className="min-h-[100px]"
                />
              </div>

              <div className="flex items-center gap-3">
                <Button onClick={handleApprove} className="bg-green-600 hover:bg-green-700">
                  <ThumbsUp className="h-4 w-4 mr-2" />
                  Approve
                </Button>
                <Button onClick={handleRequestChanges} variant="outline">
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Request Changes
                </Button>
                <Button onClick={handleReject} variant="destructive">
                  <ThumbsDown className="h-4 w-4 mr-2" />
                  Reject
                </Button>
              </div>

              <div className="text-xs text-muted-foreground">
                Your decision will be recorded and the appropriate stakeholders will be notified.
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ValidationViewer;

