'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { LearningMode } from '@/types';
import { FaBook, FaPencilAlt, FaVideo, FaGamepad, FaFlask, FaCalculator, FaQuestionCircle, FaHeadphones, FaClipboardCheck, FaRobot } from 'react-icons/fa';

export const dynamic = 'force-dynamic';

export default function ContentGenerationPage() {
  const [step, setStep] = useState(1);
  const [contentMode, setContentMode] = useState<'after-hour' | 'remedy'>('after-hour');
  const [classes, setClasses] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  
  const [formData, setFormData] = useState({
    teacher_class_id: '',
    session_id: '',
    student_id: '',
    duration_minutes: 60,
    grade_level: '',
    topic: '',
    curriculum_goal: '',
    learning_gaps: [] as string[],
    modes: [] as LearningMode[],
    difficulty: 'medium' as 'easy' | 'medium' | 'hard',
    problem_count: 5,
  });

  useEffect(() => {
    loadClasses();
  }, []);

  const loadClasses = async () => {
    try {
      const data = await apiClient.getTeacherClasses();
      setClasses(data);
    } catch (error) {
      console.error('Failed to load classes:', error);
    }
  };

  const learningModes = [
    { id: 'learn_by_reading', name: 'Learn by Reading', icon: FaBook, color: 'blue', description: 'Structured notes with visuals' },
    { id: 'learn_by_writing', name: 'Learn by Writing', icon: FaPencilAlt, color: 'purple', description: 'Writing prompts & essays' },
    { id: 'learn_by_watching', name: 'Learn by Watching', icon: FaVideo, color: 'red', description: 'Curated YouTube videos' },
    { id: 'learn_by_playing', name: 'Learn by Playing', icon: FaGamepad, color: 'green', description: 'Educational games' },
    { id: 'learn_by_doing', name: 'Learn by Doing', icon: FaFlask, color: 'yellow', description: 'Hands-on experiments' },
    { id: 'learn_by_solving', name: 'Learn by Solving', icon: FaCalculator, color: 'indigo', description: 'Problem sets & practice' },
    { id: 'learn_by_questioning', name: 'Learn by Questioning', icon: FaQuestionCircle, color: 'pink', description: 'Debate & Socratic method' },
    { id: 'learn_by_listening', name: 'Learn by Listening', icon: FaHeadphones, color: 'cyan', description: 'Audio content & podcasts' },
    { id: 'learn_by_assessment', name: 'Learn by Assessment', icon: FaClipboardCheck, color: 'orange', description: 'Quizzes & tests' },
  ];

  const toggleMode = (modeId: LearningMode) => {
    setFormData(prev => ({
      ...prev,
      modes: prev.modes.includes(modeId)
        ? prev.modes.filter(m => m !== modeId)
        : [...prev.modes, modeId]
    }));
  };

  const handleGenerate = async () => {
    if (!formData.teacher_class_id || formData.modes.length === 0) {
      alert('Please select a class and at least one learning mode');
      return;
    }

    setIsLoading(true);
    setProgress(0);

    try {
      const requestData = {
        teacher_class_id: formData.teacher_class_id,
        duration_minutes: formData.duration_minutes,
        modes: formData.modes,
        options: {
          problems: {
            count: formData.problem_count,
            difficulty: formData.difficulty,
          }
        },
        ...(contentMode === 'after-hour' ? {
          topic: formData.topic,
          grade_level: formData.grade_level,
          curriculum_goal: formData.curriculum_goal,
          learning_gaps: formData.learning_gaps.length > 0 ? formData.learning_gaps : undefined,
        } : {
          student_id: formData.student_id,
          learning_gaps: formData.learning_gaps.map(gap => ({
            code: gap,
            type: 'conceptual_gap',
            type_label: 'Learning Gap',
            evidence: ['Identified from assessment']
          })),
        }),
      };

      const response = contentMode === 'after-hour'
        ? await apiClient.generateAfterHourContent(requestData)
        : await apiClient.generateRemediationContent(requestData);

      setJobId(response.job_id);
      
      // Poll for job status
      await pollJobStatus(response.job_id);
      
      alert('Content generated successfully!');
      // Reset form
      setFormData({ ...formData, modes: [], topic: '', learning_gaps: [] });
      setStep(1);
    } catch (error: any) {
      console.error('Content generation failed:', error);
      alert(error.response?.data?.message || 'Failed to generate content');
    } finally {
      setIsLoading(false);
      setJobId(null);
      setProgress(0);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    return new Promise((resolve, reject) => {
      const interval = setInterval(async () => {
        try {
          const status = await apiClient.getJobStatus(jobId);
          setProgress(status.progress);

          if (status.status === 'completed') {
            clearInterval(interval);
            resolve(status);
          } else if (status.status === 'failed') {
            clearInterval(interval);
            reject(new Error(status.error || 'Job failed'));
          }
        } catch (error) {
          clearInterval(interval);
          reject(error);
        }
      }, 2000);
    });
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Generate Learning Content</h1>
        <p className="text-gray-600 mt-2">Create personalized, multi-modal content for your students</p>
      </div>

      {/* Mode Selection */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Select Content Type</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <button
            onClick={() => setContentMode('after-hour')}
            className={`p-6 rounded-lg border-2 transition ${
              contentMode === 'after-hour'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300'
            }`}
          >
            <h3 className="text-lg font-bold text-gray-900 mb-2">After-Hour Session</h3>
            <p className="text-sm text-gray-600">Generate content for homework, revision, or new topics</p>
          </button>

          <button
            onClick={() => setContentMode('remedy')}
            className={`p-6 rounded-lg border-2 transition ${
              contentMode === 'remedy'
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-200 hover:border-purple-300'
            }`}
          >
            <h3 className="text-lg font-bold text-gray-900 mb-2">Remediation Session</h3>
            <p className="text-sm text-gray-600">Personalized content to address learning gaps</p>
          </button>
        </div>
      </div>

      {/* Form Steps */}
      <div className="bg-white rounded-xl shadow-md p-6">
        {/* Step 1: Basic Info */}
        {step === 1 && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-gray-900">Step 1: Basic Information</h2>

            {/* Class Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Class *
              </label>
              <select
                value={formData.teacher_class_id}
                onChange={(e) => setFormData({ ...formData, teacher_class_id: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Choose a class...</option>
                {classes.map(cls => (
                  <option key={cls._id} value={cls._id}>
                    {cls.subject} - Grade {cls.grade} {cls.section}
                  </option>
                ))}
              </select>
            </div>

            {contentMode === 'after-hour' ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Topic / Chapter *
                  </label>
                  <input
                    type="text"
                    value={formData.topic}
                    onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Newton's Laws of Motion"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Curriculum Goal
                  </label>
                  <textarea
                    value={formData.curriculum_goal}
                    onChange={(e) => setFormData({ ...formData, curriculum_goal: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="What should students learn? e.g., Understand force, mass, and acceleration relationships"
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Student ID *
                  </label>
                  <input
                    type="text"
                    value={formData.student_id}
                    onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter student ID"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Learning Gaps (comma-separated) *
                  </label>
                  <textarea
                    value={formData.learning_gaps.join(', ')}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      learning_gaps: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                    })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="e.g., force_calculation, momentum_concepts"
                  />
                </div>
              </>
            )}

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Duration (minutes)
                </label>
                <input
                  type="number"
                  value={formData.duration_minutes}
                  onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  min="15"
                  max="180"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Difficulty Level
                </label>
                <select
                  value={formData.difficulty}
                  onChange={(e) => setFormData({ ...formData, difficulty: e.target.value as any })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
            </div>

            <button
              onClick={() => setStep(2)}
              disabled={!formData.teacher_class_id || (contentMode === 'after-hour' ? !formData.topic : !formData.student_id)}
              className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
            >
              Next: Select Learning Modes
            </button>
          </div>
        )}

        {/* Step 2: Learning Modes */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">Step 2: Select Learning Modes</h2>
              <span className="text-sm text-gray-600">
                Selected: {formData.modes.length}/9
              </span>
            </div>

            <p className="text-gray-600">Choose one or more learning modes to generate content</p>

            <div className="grid md:grid-cols-3 gap-4">
              {learningModes.map((mode) => (
                <button
                  key={mode.id}
                  onClick={() => toggleMode(mode.id as LearningMode)}
                  className={`p-4 rounded-lg border-2 transition text-left ${
                    formData.modes.includes(mode.id as LearningMode)
                      ? `border-${mode.color}-500 bg-${mode.color}-50`
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <mode.icon className={`text-2xl mb-2 text-${mode.color}-600`} />
                  <h3 className="font-bold text-gray-900 mb-1">{mode.name}</h3>
                  <p className="text-xs text-gray-600">{mode.description}</p>
                </button>
              ))}
            </div>

            <div className="flex space-x-4">
              <button
                onClick={() => setStep(1)}
                className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-semibold"
              >
                Back
              </button>
              <button
                onClick={handleGenerate}
                disabled={formData.modes.length === 0 || isLoading}
                className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
              >
                {isLoading ? 'Generating...' : 'Generate Content'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {isLoading && jobId && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="font-bold text-gray-900 mb-4">Generating Content...</h3>
          <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 text-center">{progress}% Complete</p>
          <p className="text-xs text-gray-500 text-center mt-2">Job ID: {jobId}</p>
        </div>
      )}
    </div>
  );
}
