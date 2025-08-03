import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

interface Question {
  id: string;
  question_text: string;
  question_type: string;
  difficulty_level: string;
  unit_code: string;
  performance_criteria: string[];
  knowledge_evidence: string[];
  benchmark_answer: string;
  assessment_guidance: string;
  created_at: string;
  status: string;
}

export const QuestionLibrary: React.FC = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [loading, setLoading] = useState(false);

  const filteredQuestions = questions.filter(question => {
    const matchesSearch = question.question_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         question.unit_code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || question.question_type === filterType;
    return matchesSearch && matchesType;
  });

  const questionTypes = ['all', 'multiple_choice', 'open_ended', 'scenario_based', 'practical'];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Question Library</h2>
        <Button>Generate New Questions</Button>
      </div>

      <div className="flex gap-4 items-center">
        <Input
          placeholder="Search questions or unit codes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-md"
        />
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-2 border rounded-md"
        >
          {questionTypes.map(type => (
            <option key={type} value={type}>
              {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </option>
          ))}
        </select>
      </div>

      <Tabs defaultValue="grid" className="w-full">
        <TabsList>
          <TabsTrigger value="grid">Grid View</TabsTrigger>
          <TabsTrigger value="list">List View</TabsTrigger>
        </TabsList>
        
        <TabsContent value="grid" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredQuestions.map((question) => (
              <Card key={question.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-sm">{question.unit_code}</CardTitle>
                    <Badge variant={question.status === 'approved' ? 'default' : 'outline'}>
                      {question.status}
                    </Badge>
                  </div>
                  <CardDescription className="line-clamp-2">
                    {question.question_text}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <Badge variant="outline">{question.question_type}</Badge>
                      <Badge variant="outline">{question.difficulty_level}</Badge>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline">Edit</Button>
                      <Button size="sm" variant="outline">Export</Button>
                      <Button size="sm" variant="outline">Preview</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        
        <TabsContent value="list" className="space-y-2">
          {filteredQuestions.map((question) => (
            <Card key={question.id}>
              <CardContent className="p-4">
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium">{question.unit_code}</span>
                      <Badge variant="outline">{question.question_type}</Badge>
                      <Badge variant="outline">{question.difficulty_level}</Badge>
                      <Badge variant={question.status === 'approved' ? 'default' : 'outline'}>
                        {question.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-1">{question.question_text}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline">Edit</Button>
                    <Button size="sm" variant="outline">Export</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>

      {filteredQuestions.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-gray-500">No questions found matching your criteria.</p>
            <Button className="mt-4">Generate Your First Questions</Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
