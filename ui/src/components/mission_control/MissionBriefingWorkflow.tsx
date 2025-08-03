import React, { useState } from 'react';
import { CheckCircle, AlertCircle, Clock, Users, Zap, ArrowRight, ArrowLeft } from 'lucide-react';
import { ApiService } from '../../services/api';

interface MissionBriefingWorkflowProps {
  initialCommand?: string;
  onComplete?: (taskId: string) => void;
  onCancel?: () => void;
}

interface BriefingData {
  objective: string;
  taskType: string;
  priority: string;
  targetAudience: string;
  deliverables: string[];
  timeline: string;
  budget: string;
  constraints: string;
  additionalContext: string;
}

const MissionBriefingWorkflow: React.FC<MissionBriefingWorkflowProps> = ({
  initialCommand = '',
  onComplete,
  onCancel
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [briefingData, setBriefingData] = useState<BriefingData>({
    objective: initialCommand || '',
    taskType: '',
    priority: 'medium',
    targetAudience: '',
    deliverables: [],
    timeline: '',
    budget: '',
    constraints: '',
    additionalContext: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const steps = [
    {
      title: 'Mission Objective',
      description: 'Define what you want to accomplish',
      icon: <Zap className="w-5 h-5" />
    },
    {
      title: 'Task Configuration',
      description: 'Specify task type and requirements',
      icon: <Users className="w-5 h-5" />
    },
    {
      title: 'Timeline & Resources',
      description: 'Set deadlines and budget constraints',
      icon: <Clock className="w-5 h-5" />
    },
    {
      title: 'Review & Submit',
      description: 'Confirm details and launch mission',
      icon: <CheckCircle className="w-5 h-5" />
    }
  ];

  const taskTypes = [
    { value: 'content_creation', label: 'Content Creation' },
    { value: 'design_project', label: 'Design Project' },
    { value: 'video_production', label: 'Video Production' },
    { value: 'social_media_campaign', label: 'Social Media Campaign' },
    { value: 'market_research', label: 'Market Research' },
    { value: 'brand_development', label: 'Brand Development' }
  ];

  const priorities = [
    { value: 'low', label: 'Low Priority', color: 'bg-gray-100 text-gray-800' },
    { value: 'medium', label: 'Medium Priority', color: 'bg-blue-100 text-blue-800' },
    { value: 'high', label: 'High Priority', color: 'bg-orange-100 text-orange-800' },
    { value: 'urgent', label: 'Urgent', color: 'bg-red-100 text-red-800' }
  ];

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    switch (step) {
      case 0:
        if (!briefingData.objective.trim()) {
          newErrors.objective = 'Mission objective is required';
        }
        break;
      case 1:
        if (!briefingData.taskType) {
          newErrors.taskType = 'Task type is required';
        }
        if (!briefingData.targetAudience.trim()) {
          newErrors.targetAudience = 'Target audience is required';
        }
        break;
      case 2:
        if (!briefingData.timeline.trim()) {
          newErrors.timeline = 'Timeline is required';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, steps.length - 1));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setIsSubmitting(true);
    try {
      const apiService = new ApiService();
      const task = await apiService.createTask({
        title: briefingData.objective,
        description: `${briefingData.additionalContext}\n\nTarget Audience: ${briefingData.targetAudience}\nDeliverables: ${briefingData.deliverables.join(', ')}\nTimeline: ${briefingData.timeline}\nBudget: ${briefingData.budget}\nConstraints: ${briefingData.constraints}`,
        type: briefingData.taskType,
        priority: briefingData.priority,
        requester_id: 'user-001',
        input_data: {
          target_audience: briefingData.targetAudience,
          deliverables: briefingData.deliverables,
          timeline: briefingData.timeline,
          budget: briefingData.budget,
          constraints: briefingData.constraints
        },
        metadata: {
          created_via: 'mission_briefing_workflow',
          workflow_version: '1.0'
        }
      });

      if (onComplete) {
        onComplete(task.id);
      }
    } catch (error) {
      console.error('Failed to create task:', error);
      setErrors({ submit: 'Failed to create mission. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const addDeliverable = () => {
    setBriefingData(prev => ({
      ...prev,
      deliverables: [...prev.deliverables, '']
    }));
  };

  const updateDeliverable = (index: number, value: string) => {
    setBriefingData(prev => ({
      ...prev,
      deliverables: prev.deliverables.map((item, i) => i === index ? value : item)
    }));
  };

  const removeDeliverable = (index: number) => {
    setBriefingData(prev => ({
      ...prev,
      deliverables: prev.deliverables.filter((_, i) => i !== index)
    }));
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            <div>
              <label htmlFor="objective" className="block text-sm font-medium text-gray-700 mb-1">Mission Objective *</label>
              <textarea
                id="objective"
                placeholder="Describe what you want to accomplish..."
                value={briefingData.objective}
                onChange={(e) => setBriefingData(prev => ({ ...prev, objective: e.target.value }))}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.objective ? 'border-red-500' : 'border-gray-300'}`}
                rows={4}
              />
              {errors.objective && (
                <p className="text-sm text-red-500 mt-1">{errors.objective}</p>
              )}
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label htmlFor="taskType" className="block text-sm font-medium text-gray-700 mb-1">Task Type *</label>
              <select
                id="taskType"
                value={briefingData.taskType}
                onChange={(e) => setBriefingData(prev => ({ ...prev, taskType: e.target.value }))}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.taskType ? 'border-red-500' : 'border-gray-300'}`}
              >
                <option value="">Select task type</option>
                {taskTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              {errors.taskType && (
                <p className="text-sm text-red-500 mt-1">{errors.taskType}</p>
              )}
            </div>

            <div>
              <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">Priority Level</label>
              <select
                id="priority"
                value={briefingData.priority}
                onChange={(e) => setBriefingData(prev => ({ ...prev, priority: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {priorities.map((priority) => (
                  <option key={priority.value} value={priority.value}>
                    {priority.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="targetAudience" className="block text-sm font-medium text-gray-700 mb-1">Target Audience *</label>
              <input
                id="targetAudience"
                type="text"
                placeholder="Who is this for?"
                value={briefingData.targetAudience}
                onChange={(e) => setBriefingData(prev => ({ ...prev, targetAudience: e.target.value }))}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.targetAudience ? 'border-red-500' : 'border-gray-300'}`}
              />
              {errors.targetAudience && (
                <p className="text-sm text-red-500 mt-1">{errors.targetAudience}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Deliverables</label>
              <div className="space-y-2">
                {briefingData.deliverables.map((deliverable, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Expected deliverable"
                      value={deliverable}
                      onChange={(e) => updateDeliverable(index, e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      type="button"
                      className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                      onClick={() => removeDeliverable(index)}
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                  onClick={addDeliverable}
                >
                  Add Deliverable
                </button>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <label htmlFor="timeline" className="block text-sm font-medium text-gray-700 mb-1">Timeline *</label>
              <input
                id="timeline"
                type="text"
                placeholder="e.g., 2 weeks, by Friday, ASAP"
                value={briefingData.timeline}
                onChange={(e) => setBriefingData(prev => ({ ...prev, timeline: e.target.value }))}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.timeline ? 'border-red-500' : 'border-gray-300'}`}
              />
              {errors.timeline && (
                <p className="text-sm text-red-500 mt-1">{errors.timeline}</p>
              )}
            </div>

            <div>
              <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-1">Budget</label>
              <input
                id="budget"
                type="text"
                placeholder="Budget constraints or range"
                value={briefingData.budget}
                onChange={(e) => setBriefingData(prev => ({ ...prev, budget: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="constraints" className="block text-sm font-medium text-gray-700 mb-1">Constraints</label>
              <textarea
                id="constraints"
                placeholder="Any limitations, requirements, or restrictions..."
                value={briefingData.constraints}
                onChange={(e) => setBriefingData(prev => ({ ...prev, constraints: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="additionalContext" className="block text-sm font-medium text-gray-700 mb-1">Additional Context</label>
              <textarea
                id="additionalContext"
                placeholder="Any other relevant information..."
                value={briefingData.additionalContext}
                onChange={(e) => setBriefingData(prev => ({ ...prev, additionalContext: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-3">Mission Summary</h3>
              <div className="space-y-2 text-sm">
                <div><strong>Objective:</strong> {briefingData.objective}</div>
                <div><strong>Type:</strong> {taskTypes.find(t => t.value === briefingData.taskType)?.label}</div>
                <div><strong>Priority:</strong> {priorities.find(p => p.value === briefingData.priority)?.label}</div>
                <div><strong>Target Audience:</strong> {briefingData.targetAudience}</div>
                <div><strong>Timeline:</strong> {briefingData.timeline}</div>
                {briefingData.deliverables.length > 0 && (
                  <div><strong>Deliverables:</strong> {briefingData.deliverables.filter(d => d.trim()).join(', ')}</div>
                )}
                {briefingData.budget && <div><strong>Budget:</strong> {briefingData.budget}</div>}
                {briefingData.constraints && <div><strong>Constraints:</strong> {briefingData.constraints}</div>}
              </div>
            </div>

            {errors.submit && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-center gap-2 text-red-800">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm">{errors.submit}</span>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white rounded-lg shadow-lg">
      <div className="p-6 border-b">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Zap className="w-6 h-6" />
          Mission Briefing Workflow
        </h2>
        <div className="flex items-center gap-4 mt-4">
          {steps.map((step, index) => (
            <div key={index} className="flex items-center gap-2">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
                index <= currentStep ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
              }`}>
                {index < currentStep ? <CheckCircle className="w-4 h-4" /> : step.icon}
              </div>
              <div className="hidden sm:block">
                <div className={`text-sm font-medium ${index <= currentStep ? 'text-blue-600' : 'text-gray-600'}`}>
                  {step.title}
                </div>
                <div className="text-xs text-gray-500">{step.description}</div>
              </div>
              {index < steps.length - 1 && (
                <ArrowRight className="w-4 h-4 text-gray-400 mx-2" />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="p-6">
        {renderStepContent()}

        <hr className="my-6" />

        <div className="flex justify-between">
          <div className="flex gap-2">
            {currentStep > 0 && (
              <button 
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                onClick={handlePrevious}
              >
                <ArrowLeft className="w-4 h-4 mr-2 inline" />
                Previous
              </button>
            )}
            {onCancel && (
              <button 
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                onClick={onCancel}
              >
                Cancel
              </button>
            )}
          </div>

          <div className="flex gap-2">
            {currentStep < steps.length - 1 ? (
              <button 
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                onClick={handleNext}
              >
                Next
                <ArrowRight className="w-4 h-4 ml-2 inline" />
              </button>
            ) : (
              <button 
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                onClick={handleSubmit} 
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Launching Mission...' : 'Launch Mission'}
                <Zap className="w-4 h-4 ml-2 inline" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MissionBriefingWorkflow;
