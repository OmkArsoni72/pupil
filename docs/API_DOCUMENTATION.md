# PupilTree Agents - API Documentation

## 🚀 Quick Start

**Base URL**: `http://localhost:8080/api`

**Authentication**: Bearer token in Authorization header (for protected endpoints)

## 📋 Table of Contents

1. [Content Generation APIs](#content-generation-apis)
2. [Job Management APIs](#job-management-apis)
3. [Assessment APIs](#assessment-apis)
4. [User Management APIs](#user-management-apis)
5. [Curriculum APIs](#curriculum-apis)
6. [Timetable APIs](#timetable-apis)
7. [RAG System APIs](#rag-system-apis)
8. [Teacher Management APIs](#teacher-management-apis)
9. [Error Handling](#error-handling)
10. [Response Formats](#response-formats)

---

## Content Generation APIs

### Generate After Hour Session Content

**Endpoint**: `POST /api/v1/contentGenerationForAHS`

**Description**: Generates comprehensive after-hour learning content including reading materials, videos, games, practice questions, and assessments.

**Request Body**:

```json
{
  "teacher_class_id": "class_123",
  "session_id": "session_456",
  "duration_minutes": 60,
  "grade_level": "10",
  "curriculum_goal": "Master Newton's Laws of Motion",
  "topic": "Physics - Newton's Laws",
  "context_refs": {
    "lesson_script_id": "script_789",
    "in_class_question_ids": ["q1", "q2", "q3"],
    "recent_session_ids": ["session_1", "session_2"],
    "recent_performance": {
      "average_score": 75,
      "completion_rate": 0.8
    }
  },
  "learning_gaps": ["force_calculation", "momentum_concepts"],
  "modes": ["learn_by_reading", "learn_by_watching", "learn_by_solving"],
  "options": {
    "problems": {
      "count": 5,
      "difficulty": "medium"
    },
    "videos": {
      "max_duration": 10
    }
  }
}
```

**Response** (202 Accepted):

```json
{
  "job_id": "JOB_AHS_a1b2c3d4",
  "status": "pending",
  "progress": 0,
  "error": null,
  "result_doc_id": null
}
```

### Generate Remediation Content

**Endpoint**: `POST /api/v1/contentGenerationForRemedies`

**Description**: Generates personalized remediation content for specific learning gaps.

**Request Body**:

```json
{
  "teacher_class_id": "class_123",
  "student_id": "student_456",
  "duration_minutes": 30,
  "request_meta": {
    "test_run": false,
    "request_origin": "reports_agent"
  },
  "learning_gaps": [
    {
      "code": "PHY_001",
      "type": "conceptual_gap",
      "type_label": "Conceptual Gap",
      "evidence": [
        "struggled with force calculations",
        "confused about vector components"
      ]
    },
    {
      "code": "PHY_002",
      "type": "application_gap",
      "type_label": "Application Gap",
      "evidence": [
        "cannot solve multi-step problems",
        "difficulty with free body diagrams"
      ]
    }
  ],
  "context_refs": {
    "lesson_script_id": "script_789",
    "recent_performance": {
      "physics_score": 45,
      "attempts": 3
    }
  },
  "modes": ["learn_by_reading", "learn_by_doing"],
  "options": {
    "problems": {
      "count": 5,
      "progressive_difficulty": true
    },
    "max_remediation_cycles": 3
  }
}
```

**Response** (202 Accepted):

```json
{
  "job_id": "JOB_REM_e5f6g7h8",
  "status": "pending",
  "progress": 0,
  "error": null,
  "result_doc_id": null
}
```

---

## Job Management APIs

### Get Job Status

**Endpoint**: `GET /api/v1/jobs/{job_id}`

**Description**: Check the status of a background job.

**Response**:

```json
{
  "job_id": "JOB_AHS_a1b2c3d4",
  "status": "completed",
  "progress": 100,
  "error": null,
  "result_doc_id": "sessions/session_456"
}
```

**Status Values**:

- `pending`: Job is queued
- `in_progress`: Job is running
- `completed`: Job finished successfully
- `failed`: Job encountered an error

### Get Generated Content

**Endpoint**: `GET /api/v1/jobs/{job_id}/content`

**Description**: Retrieve the generated content after job completion.

**Response** (200 OK):

```json
{
  "job_id": "JOB_AHS_a1b2c3d4",
  "route": "AHS",
  "session_id": "session_456",
  "content": {
    "texts": [
      {
        "contentId": "text_1",
        "title": "Newton's First Law Explained",
        "source": "ai_generated",
        "content": "Newton's first law states that..."
      }
    ],
    "videos": [
      {
        "contentId": "video_1",
        "title": "Understanding Inertia",
        "source": "youtube",
        "url": "https://youtube.com/watch?v=...",
        "durationInSeconds": 300
      }
    ],
    "games": [
      {
        "contentId": "game_1",
        "title": "Force and Motion Simulator",
        "type": "interactive",
        "url": "https://phet.colorado.edu/...",
        "estimatedPlayTimeInMinutes": 15
      }
    ],
    "practiceQuestions": {
      "setId": "pq_1",
      "title": "Newton's Laws Practice",
      "numberOfQuestions": 5,
      "questionIds": ["q1", "q2", "q3", "q4", "q5"]
    },
    "assessmentQuestions": {
      "assessmentId": "assess_1",
      "title": "Newton's Laws Assessment",
      "numberOfQuestions": 3,
      "timeLimitInMinutes": 20,
      "questionIds": ["aq1", "aq2", "aq3"]
    }
  }
}
```

**Response** (202 Accepted - Job not completed):

```json
{
  "job_id": "JOB_AHS_a1b2c3d4",
  "status": "in_progress",
  "progress": 45,
  "message": "Job not completed yet"
}
```

### Get Remediation Plans

**Endpoint**: `GET /api/v1/remedyJobs/{job_id}/plans`

**Description**: Get detailed remediation strategies and plans.

**Response**:

```json
{
  "job_id": "JOB_REM_e5f6g7h8",
  "status": "completed",
  "remedy_plan_id": "remedy_plan_123",
  "strategy": {
    "classified_gaps": [
      {
        "code": "PHY_001",
        "type": "conceptual_gap",
        "evidence": ["struggled with force calculations"]
      }
    ],
    "plans": [
      {
        "gap_type": "conceptual",
        "selected_modes": ["learn_by_reading", "learn_by_doing"],
        "content_specifications": {
          "reading": {
            "focus_areas": ["force concepts", "vector mathematics"],
            "difficulty": "foundational"
          },
          "doing": {
            "experiments": ["force measurement", "vector addition"],
            "safety_notes": ["use appropriate equipment"]
          }
        },
        "priority": 1,
        "estimated_duration_minutes": 30
      }
    ]
  },
  "orchestration": {
    "child_jobs": ["JOB_CONTENT_1", "JOB_CONTENT_2"]
  },
  "prerequisite_discoveries": {
    "PHY_001": [
      {
        "topic": "Basic Vector Mathematics",
        "grade_level": "9",
        "priority": 1,
        "estimated_duration_hours": 2
      }
    ]
  }
}
```

### Get Aggregated Results

**Endpoint**: `GET /api/v1/jobs/{job_id}/aggregate`

**Description**: Get comprehensive view of job results including child jobs and content.

**Response**:

```json
{
  "job": {
    "job_id": "JOB_REM_e5f6g7h8",
    "status": "completed",
    "progress": 100,
    "error": null,
    "remedy_plan_id": "remedy_plan_123"
  },
  "strategy": {
    "classified_gaps": [...],
    "plans": [...]
  },
  "orchestration": {
    "child_jobs": ["JOB_CONTENT_1", "JOB_CONTENT_2"]
  },
  "prerequisite_discoveries": {...},
  "content_specs": [
    {
      "content_job_id": "JOB_CONTENT_1",
      "content": {
        "learn_by_reading": {
          "five_min_summary": "Newton's laws summary...",
          "sections": [...],
          "glossary": {...}
        }
      }
    }
  ],
  "validation_summaries": [
    {
      "mode": "learn_by_reading",
      "is_valid": true,
      "timestamp": "2024-01-15T10:30:00Z",
      "metadata": {...}
    }
  ]
}
```

---

## Assessment APIs

### Generate Assessment

**Endpoint**: `POST /api/assessments/generate`

**Description**: Generate educational assessments with questions.

**Request Body**:

```json
{
  "target_exam": "CBSE_Grade10_Physics_Monthly",
  "exam_type": "monthly",
  "self_assessment_mode": "random",
  "difficulty": "medium",
  "subject": "Physics",
  "class": "10A",
  "teacher_id": "teacher_123",
  "previous_topics": ["Motion", "Forces"],
  "learning_gaps": ["vector_math", "problem_solving"],
  "file_url": "https://example.com/uploaded_file.pdf"
}
```

**Response** (202 Accepted):

```json
{
  "job_id": "JOB_ASSESS_123",
  "status": "pending"
}
```

### Get Assessment Status

**Endpoint**: `GET /api/assessments/status/{job_id}`

**Response**:

```json
{
  "job_id": "JOB_ASSESS_123",
  "status": "completed",
  "assessment_id": "assessment_456",
  "error": null
}
```

### Get Assessment Details

**Endpoint**: `GET /api/assessments/{assessment_id}`

**Response**:

```json
{
  "_id": "assessment_456",
  "target_exam": "CBSE_Grade10_Physics_Monthly",
  "subject": "Physics",
  "class": "10A",
  "difficulty": "medium",
  "questions": [
    {
      "questionText": "What is Newton's first law?",
      "questionType": "MCQ",
      "options": [
        "An object at rest stays at rest",
        "Force equals mass times acceleration",
        "Every action has an equal reaction",
        "Energy cannot be created or destroyed"
      ],
      "answer": {
        "correct": "An object at rest stays at rest",
        "explanation": "Newton's first law describes inertia..."
      },
      "difficulty": "medium",
      "topics": ["Newton's Laws"],
      "learningOutcomes": ["Understand inertia concept"]
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## User Management APIs

### Register User

**Endpoint**: `POST /api/user/register`

**Request Body**:

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password_hash": "hashed_password",
  "role": "teacher",
  "institution_id": "school_123",
  "profile": {
    "current_class_id": "class_456",
    "assigned_classes": [
      {
        "classId": "class_456",
        "className": "Grade 10 Physics"
      }
    ]
  }
}
```

**Response**:

```json
{
  "id": "user_789",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "teacher",
  "profile": {...},
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Login User

**Endpoint**: `POST /api/user/login`

**Request Body**:

```json
{
  "email": "john@example.com"
}
```

**Response**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_789",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "teacher"
  }
}
```

### Get Current User

**Endpoint**: `GET /api/user/current`

**Headers**: `Authorization: Bearer {token}`

**Response**:

```json
{
  "id": "user_789",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "teacher",
  "profile": {...}
}
```

---

## Curriculum APIs

### Get Grades

**Endpoint**: `GET /api/grades`

**Response**:

```json
[
  {
    "id": "grade_1",
    "grade": "Grade 1"
  },
  {
    "id": "grade_2",
    "grade": "Grade 2"
  }
]
```

### Get Sections for Grade

**Endpoint**: `GET /api/grades/{grade_id}/sections`

**Response**:

```json
[
  {
    "sectionName": "A"
  },
  {
    "sectionName": "B"
  }
]
```

### Get Subjects for Section

**Endpoint**: `GET /api/grades/{grade_id}/sections/{section_name}`

**Response**:

```json
[
  {
    "subjectName": "Physics",
    "board": "CBSE"
  },
  {
    "subjectName": "Chemistry",
    "board": "CBSE"
  }
]
```

### Get Chapters for Subject

**Endpoint**: `GET /api/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}`

**Response**:

```json
[
  {
    "name": "Motion in a Straight Line",
    "periods": 8
  },
  {
    "name": "Laws of Motion",
    "periods": 10
  }
]
```

### Get Periods for Chapter

**Endpoint**: `GET /api/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}/chapters/{chapter_name}/periods`

**Response**:

```json
[
  {
    "period": 1,
    "title": "Introduction to Motion",
    "duration": 45
  },
  {
    "period": 2,
    "title": "Distance and Displacement",
    "duration": 45
  }
]
```

---

## Timetable APIs

### Upload Timetable PDF

**Endpoint**: `POST /api/timetable/upload-pdf`

**Content-Type**: `multipart/form-data`

**Form Data**:

- `file`: PDF file
- `class_id`: string
- `school_id`: string
- `academic_year`: string
- `generated_by_user_id`: string

**Response**:

```json
{
  "message": "Timetable uploaded successfully",
  "timetable_id": "timetable_123",
  "file_name": "grade_10_schedule.pdf"
}
```

### Ingest Timetable from Database

**Endpoint**: `POST /api/timetable/ingest-from-db`

**Request Body**:

```json
{
  "class_id": "class_123",
  "school_id": "school_456",
  "academic_year": "2024-25"
}
```

**Response**:

```json
{
  "message": "Timetable ingestion started",
  "job_id": "timetable_job_789",
  "events_created": 45
}
```

### Get Daily Schedule

**Endpoint**: `GET /api/timetable/daily-schedule`

**Query Parameters**:

- `teacher_id`: string
- `class_id`: string
- `day`: date (YYYY-MM-DD)

**Response**:

```json
[
  {
    "id": "event_123",
    "class_id": "class_456",
    "teacher_id": "teacher_789",
    "scheduled_date": "2024-01-15T09:00:00Z",
    "duration_minutes": 45,
    "event_type": "class_session",
    "status": "scheduled",
    "planned_lesson_id": "lesson_123"
  }
]
```

---

## RAG System APIs

### Ingest NCERT Content

**Endpoint**: `POST /api/rag/ncert/ingest`

**Request Body**:

```json
{
  "paths": ["CBSE/grade_10/ch (1).pdf", "CBSE/grade_10/ch (2).pdf"]
}
```

**Response**:

```json
{
  "message": "NCERT ingestion started",
  "job_id": "ingest_job_123",
  "files_to_process": 2
}
```

### Get NCERT Ingestion Status

**Endpoint**: `GET /api/rag/ncert/status`

**Response**:

```json
{
  "status": "completed",
  "total_files": 15,
  "processed_files": 15,
  "total_chunks": 1250,
  "vectors_created": 1250,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### Query NCERT Content

**Endpoint**: `POST /api/rag/ncert/qa`

**Request Body**:

```json
{
  "query": "What is Newton's first law of motion?",
  "grade": "10",
  "subject": "Physics",
  "top_k": 8
}
```

**Response**:

```json
{
  "query": "What is Newton's first law of motion?",
  "top_k": 8,
  "citations": [
    {
      "text": "Newton's first law states that an object at rest stays at rest...",
      "source": "CBSE Grade 10 Physics Chapter 5",
      "page": 45,
      "relevance_score": 0.95
    }
  ]
}
```

### Discover Prerequisites

**Endpoint**: `POST /api/rag/ncert/prerequisites`

**Request Body**:

```json
{
  "topic": "Quadratic Equations",
  "grade": "10",
  "subject": "Mathematics",
  "top_k": 12
}
```

**Response**:

```json
{
  "topic": "Quadratic Equations",
  "current_grade": "10",
  "subject": "Mathematics",
  "prerequisite_floors": [
    {
      "grade_level": "9",
      "topics": [
        {
          "topic": "Linear Equations",
          "priority": 1,
          "description": "Understanding basic equation solving"
        },
        {
          "topic": "Algebraic Manipulation",
          "priority": 2,
          "description": "Skills in algebraic operations"
        }
      ],
      "estimated_duration_hours": 4,
      "mastery_threshold": 0.8
    }
  ],
  "discovery_method": "vector_search"
}
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request

```json
{
  "detail": "Invalid request parameters",
  "error_code": "INVALID_PARAMS"
}
```

#### 404 Not Found

```json
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND"
}
```

#### 500 Internal Server Error

```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR"
}
```

### Job Error Response

```json
{
  "job_id": "JOB_123",
  "status": "failed",
  "progress": 0,
  "error": "Database connection failed",
  "result_doc_id": null
}
```

---

## Response Formats

### Standard Success Response

```json
{
  "status": "success",
  "data": {...},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Paginated Response

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "has_next": true,
  "has_prev": false
}
```

### Job Status Response

```json
{
  "job_id": "string",
  "status": "pending|in_progress|completed|failed",
  "progress": 0-100,
  "error": "string|null",
  "result_doc_id": "string|null"
}
```

---

## Authentication

Most endpoints require authentication via Bearer token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Getting a Token

1. Register a user: `POST /api/user/register`
2. Login: `POST /api/user/login`
3. Use the returned `access_token` in subsequent requests

---

## Rate Limiting

- **Content Generation**: 10 requests per minute per user
- **Assessment Generation**: 5 requests per minute per user
- **RAG Queries**: 20 requests per minute per user
- **General APIs**: 100 requests per minute per user

---

## WebSocket Support

Real-time updates are available via WebSocket at `/ws`:

```javascript
const socket = io("http://localhost:8080/ws");

socket.on("job_update", (data) => {
  console.log("Job status:", data);
});

socket.on("content_ready", (data) => {
  console.log("Content generated:", data);
});
```

---

## Testing

### Health Check

```http
GET /
```

**Response**:

```json
{
  "message": "API is running!"
}
```

### Debug Endpoints

#### Get All Jobs

```http
GET /api/v1/debug/jobs
```

#### Get Job Debug Info

```http
GET /api/v1/debug/jobs/{job_id}
```

---

This comprehensive API documentation covers all available endpoints with detailed request/response examples. The system provides a robust platform for AI-powered educational content generation with real-time processing and monitoring capabilities.
