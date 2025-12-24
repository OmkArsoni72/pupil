// User & Authentication Types
export interface User {
  _id: string;
  email: string;
  name: string;
  role: 'teacher' | 'student' | 'admin' | 'hod' | 'dean';
  profile?: {
    avatar?: string;
    phone?: string;
    grade?: string;
    section?: string;
  };
  institution_id?: string;
  gamification?: {
    points: number;
    level: number;
    badges: string[];
  };
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  role: string;
  institution_id?: string;
}

// Content Generation Types
export interface ContentGenerationRequest {
  teacher_class_id: string;
  session_id?: string;
  student_id?: string;
  duration_minutes: number;
  grade_level?: string;
  curriculum_goal?: string;
  topic?: string;
  context_refs?: {
    lesson_script_id?: string;
    in_class_question_ids?: string[];
    recent_session_ids?: string[];
    recent_performance?: {
      average_score: number;
      completion_rate: number;
    };
  };
  learning_gaps?: Array<{
    code: string;
    type: string;
    type_label: string;
    evidence: string[];
  }> | string[];
  modes: LearningMode[];
  options?: {
    problems?: {
      count: number;
      difficulty?: 'easy' | 'medium' | 'hard';
      progressive_difficulty?: boolean;
    };
    videos?: {
      max_duration: number;
    };
    max_remediation_cycles?: number;
  };
  request_meta?: {
    test_run: boolean;
    request_origin: string;
  };
}

export type LearningMode = 
  | 'learn_by_reading'
  | 'learn_by_writing'
  | 'learn_by_watching'
  | 'learn_by_playing'
  | 'learn_by_doing'
  | 'learn_by_solving'
  | 'learn_by_questioning'
  | 'learn_by_listening'
  | 'learn_by_assessment';

export interface JobResponse {
  job_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  error: string | null;
  result_doc_id: string | null;
}

// Assessment Types
export interface AssessmentGenerationRequest {
  target_exam: string;
  exam_type: 'weekly' | 'monthly' | 'quarterly' | 'self_assessment';
  self_assessment_mode?: 'random' | 'weekly' | 'monthly';
  difficulty?: 'easy' | 'medium' | 'hard';
  subject: string;
  class: string;
  teacher_id?: string;
  previous_topics?: string[];
  learning_gaps?: string[];
  file_url?: string;
}

export interface Question {
  _id: string;
  question_text: string;
  question_type: 'MCQ' | 'Integer' | 'Short Answer' | 'Long Answer' | 'True/False';
  options?: string[];
  correct_answer: string | number;
  explanation?: string;
  difficulty: 'easy' | 'medium' | 'hard';
  marks: number;
  topic: string;
  subject: string;
  grade: string;
  learning_outcome?: string;
}

export interface Assessment {
  _id: string;
  job_id: string;
  status: string;
  created_at: string;
  question_ids: string[];
  questions?: Question[];
  request_params: AssessmentGenerationRequest;
  total_marks?: number;
}

// Session Types
export interface Session {
  _id: string;
  teacher_class_id: string;
  session_date: string;
  lesson_script_id?: string;
  topic: string;
  subject: string;
  grade: string;
  duration_minutes: number;
  status: 'scheduled' | 'live' | 'completed';
  in_class_questions?: string[];
  after_hour_content?: {
    job_id: string;
    content_modes: LearningMode[];
    generated_at: string;
  };
  attendance?: {
    student_id: string;
    present: boolean;
    timestamp: string;
  }[];
}

// Teacher Class Types
export interface TeacherClass {
  _id: string;
  teacher_id: string;
  institution_id: string;
  grade: string;
  section: string;
  subject: string;
  students: string[];
  curriculum?: {
    topics: string[];
    learning_outcomes: string[];
  };
  timetable?: {
    day: string;
    start_time: string;
    end_time: string;
  }[];
}

// Student Report Types
export interface StudentReport {
  _id: string;
  student_id: string;
  teacher_class_id: string;
  report_date: string;
  performance: {
    inclass?: {
      total_questions: number;
      correct_answers: number;
      accuracy: number;
    };
    after_hour?: {
      completion_rate: number;
      average_score: number;
    };
    assessment?: {
      score: number;
      max_score: number;
      percentage: number;
    };
  };
  learning_gaps: {
    code: string;
    type: string;
    severity: 'low' | 'medium' | 'high';
    identified_at: string;
  }[];
  remedy_sessions?: {
    session_id: string;
    status: 'pending' | 'in_progress' | 'completed';
    started_at?: string;
    completed_at?: string;
  }[];
}

// Timetable Types
export interface TimetableEvent {
  _id: string;
  institution_id: string;
  teacher_id?: string;
  class_id?: string;
  event_type: 'class' | 'assessment' | 'holiday' | 'meeting';
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  recurrence?: 'daily' | 'weekly' | 'monthly' | 'none';
  metadata?: Record<string, any>;
}

// Learning Content Types
export interface ReadingContent {
  type: 'reading';
  title: string;
  summary_5min: string;
  detailed_notes: string;
  key_terms: {
    term: string;
    definition: string;
  }[];
  visuals: {
    type: 'image' | 'chart' | 'diagram';
    url: string;
    caption: string;
    explanation: string;
  }[];
  memory_hacks: {
    type: 'mnemonic' | 'analogy' | 'chunking';
    content: string;
  }[];
  glossary: {
    term: string;
    definition: string;
  }[];
}

export interface VideoContent {
  type: 'video';
  videos: {
    url: string;
    title: string;
    duration: number;
    summary: string;
    relevance_score: number;
  }[];
}

export interface ProblemContent {
  type: 'problem';
  problems: {
    id: string;
    question: string;
    type: 'MCQ' | 'Integer' | 'Short Answer';
    difficulty: 'easy' | 'medium' | 'hard';
    options?: string[];
    correct_answer: string | number;
    explanation: string;
    hints: string[];
  }[];
}

export interface GameContent {
  type: 'game';
  game_url: string;
  game_title: string;
  target_gaps: string[];
  instructions: string;
}

export interface ExperimentContent {
  type: 'experiment';
  title: string;
  objective: string;
  materials: string[];
  instructions: {
    step: number;
    description: string;
    safety_note?: string;
  }[];
  questions: string[];
  expected_outcomes: string[];
}

export type LearningContent =
  | ReadingContent
  | VideoContent
  | ProblemContent
  | GameContent
  | ExperimentContent;

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// WebSocket Event Types
export interface LiveClassEvent {
  type: 'question_pushed' | 'student_answered' | 'session_started' | 'session_ended';
  session_id: string;
  data: any;
  timestamp: string;
}
