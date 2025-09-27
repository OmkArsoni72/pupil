# Database Collections, Routes & Agents Mapping Guide

## 🎯 Overview

This guide provides a comprehensive mapping of database collections to API routes and agents in the PupilTree Agents system. It's designed to help new developers understand which collections are used by which routes and agents, making it easier to create new GET routes and understand the system architecture.

## 🗄️ Database Structure

**Primary Database**: `Pupil_teach` (MongoDB Atlas)

**Note**: The system previously used three databases (`Pupil_teach`, `Pupil_learn`, `Pupil-Amigo`), but currently only uses `Pupil_teach` as the main database.

---

## 📊 Collection to Route/Agent Mapping

### 1. **User Management Collections**

#### `users` Collection

- **Purpose**: User accounts, authentication, and profiles
- **Used by Routes**:
  - `POST /api/user/register` - User registration
  - `POST /api/user/login` - User authentication
  - `GET /api/user/{user_id}` - Get user details
  - `PUT /api/user/{user_id}` - Update user details
  - `DELETE /api/user/{user_id}` - Delete user
  - `PUT /api/user/{user_id}/role` - Update user role
  - `POST /api/user/{user_id}/code` - Bind SmartBoard code
  - `GET /api/user/{user_id}/code` - Get SmartBoard code
- **Used by Agents**: None (direct controller operations)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "name": "str",
    "email": "str",
    "password_hash": "str",
    "role": "str", // "student", "teacher", "hod", "dean", "admin"
    "institution_id": "str",
    "auth_tokens": ["str"],
    "profile": {
      "current_class_id": "str",
      "parent_details": [
        { "name": "str", "email": "str", "phone_number": "str" }
      ],
      "gamification_stats": {
        "points": "int",
        "streaks": "int",
        "badges": ["str"]
      },
      "specialized_subjects": ["str"],
      "assigned_classes": [{ "classId": "str", "className": "str" }]
    },
    "created_at": "datetime"
  }
  ```

#### `institutions` Collection

- **Purpose**: School/institution data
- **Used by Routes**: Timetable-related routes
- **Used by Agents**: None (direct controller operations)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "name": "str",
    "address": { "street": "str", "city": "str", "country": "str" },
    "boards": ["str"],
    "admin_ids": [
      { "name": "str", "designation": "str", "adminId": "ObjectId" }
    ],
    "classes": [
      { "name": "str", "student_list": ["ObjectId"], "classId": "str" }
    ],
    "teachers": [{ "name": "str", "id": "str" }],
    "created_at": "datetime"
  }
  ```

### 2. **Educational Content Collections**

#### `lesson_script` Collection

- **Purpose**: Curriculum structure and educational content
- **Used by Routes**: Content generation routes
- **Used by Agents**: Content Agent, Assessment Agent
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "grade": "int",
    "sections": [
      {
        "section": "str",
        "subjects": [
          {
            "name": "str",
            "board": "str",
            "chapters": [
              {
                "name": "str",
                "periods": [
                  {
                    "period": "str",
                    "script": "str"
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
  ```

#### `sessions` Collection

- **Purpose**: Class session data with generated content
- **Used by Routes**:
  - `GET /api/v1/sessions/{session_id}/afterHourSession` - Get AHS content
  - `GET /api/v1/jobs/{job_id}/content` - Get generated content
- **Used by Agents**: Content Agent (AHS route)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "teacherClassDataId": "str",
    "chapterId": "str",
    "lessonNumber": "int",
    "sessionTitle": "str",
    "sessionDate": "datetime",
    "status": "str",
    "learningOutcomes": ["str"],
    "inClassQuestions": {
      "subjectCode": "str",
      "mcqs": [{ "question": "str", "options": ["str"], "answer": "str" }],
      "shortAnswer": [{ "question": "str" }]
    },
    "lessonScript": {
      "scriptId": "str",
      "creationMethod": "str",
      "estimatedReadingTimeInMinutes": "int",
      "scriptContent": "str"
    },
    "afterHourSession": {
      "texts": [{ "title": "str", "url": "str" }],
      "videos": [{ "title": "str", "url": "str" }],
      "games": [{ "title": "str", "url": "str" }],
      "practiceQuestions": {
        "questions": [
          { "question": "str", "options": ["str"], "answer": "str" }
        ]
      },
      "assessmentQuestions": {
        "questions": [
          { "question": "str", "answerGuide": "str", "questionType": "str" }
        ]
      },
      "status": "str"
    }
  }
  ```

#### `question_bank` Collection

- **Purpose**: Question repository with statistics and usage history
- **Used by Routes**:
  - Assessment generation routes
  - Content generation routes (for practice questions)
- **Used by Agents**: Assessment Agent, Content Agent
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "questionText": "str",
    "questionType": "str",
    "origin": "str",
    "options": [{ "key": "str", "text": "str" }],
    "answer": { "key": "str", "explanation": "str" },
    "difficulty": "str",
    "grade": "str",
    "topics": ["str"],
    "learningOutcomes": ["str"],
    "usageHistory": [{ "setId": "str", "setType": "str", "dateUsed": "str" }],
    "statistics": {
      "averageTimeSeconds": "int",
      "successRate": "float",
      "numberOfAttempts": "int"
    },
    "bestStudentSolution": {
      "studentId": "str",
      "solutionText": "str",
      "timeToSolveSeconds": "int",
      "submissionTime": "str"
    },
    "fastestStudentSolution": {
      "studentId": "str",
      "solutionText": "str",
      "timeToSolveSeconds": "int",
      "submissionTime": "str"
    },
    "setId": "str"
  }
  ```

### 3. **Assessment Collections**

#### `templates` Collection

- **Purpose**: Assessment templates and schemas
- **Used by Routes**:
  - `POST /api/assessments/generate` - Assessment generation
- **Used by Agents**: Assessment Agent (Schema Agent)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "target_exam": "str",
    "metadata": {
      "board": "str",
      "grade": "int",
      "subject": "str",
      "exam_type": "str",
      "duration_minutes": "int",
      "total_marks": "int"
    },
    "scheme": {
      "answer_types": {
        "MCQ": ["str"],
        "Integer": ["str"],
        "Descriptive": ["str"]
      },
      "question_formats": ["str"],
      "sections": [
        {
          "name": "str",
          "marks_per_question": {
            "single_correct": "int",
            "multiple_correct": "int",
            "true_false": "int",
            "single_digit": "int"
          },
          "negative_marking": {
            "single_correct": "float",
            "multiple_correct": "float"
          },
          "difficulty_distribution_percent": {
            "easy": "int",
            "medium": "int",
            "hard": "int"
          },
          "question_distribution": {
            "MCQ": {
              "single_correct": "int",
              "multiple_correct": "int",
              "true_false": "int"
            },
            "Integer": { "single_digit": "int" }
          }
        }
      ]
    },
    "instructions": ["str"]
  }
  ```

#### `assessments` Collection

- **Purpose**: Generated assessments and their metadata
- **Used by Routes**:
  - `GET /api/assessments/status/{job_id}` - Assessment status
  - `GET /api/assessments/{assessment_id}` - Get assessment details
- **Used by Agents**: Assessment Agent
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "job_id": "str",
    "status": "str", // "pending", "completed", "failed"
    "created_at": "datetime",
    "question_ids": ["str"],
    "request_params": "dict"
  }
  ```

### 4. **Reporting Collections**

#### `student_reports` Collection

- **Purpose**: Comprehensive student performance tracking
- **Used by Routes**:
  - `GET /api/details/student_report/{class_id}/{student_id}` - Get student report
  - Content generation routes (for context)
- **Used by Agents**: Content Agent, Remedy Agent (for context)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "classId": "str",
    "studentId": "str",
    "teacherId": "str",
    "schoolId": "str",
    "report": {
      "inclass_report": [
        {
          "reportId": "str",
          "date": "str",
          "time": "str",
          "chapterName": "str",
          "score": "str",
          "grade": "str",
          "notes": "str",
          "learning_gaps": "str",
          "remarks": "str",
          "report_url": "str"
        }
      ],
      "after_hour_session_report": [
        {
          "sessionId": "str",
          "date": "str",
          "time": "str",
          "worksheetId": "str",
          "status": "str",
          "score": "str",
          "feedback": "str",
          "learning_gaps": "str",
          "remarks": "str",
          "report_url": "str"
        }
      ],
      "daily_report": [
        {
          "reportId": "str",
          "date": "str",
          "time": "str",
          "attendance": "str",
          "behaviorNotes": "str",
          "activities": "str",
          "learning_gaps": "str",
          "remarks": "str",
          "report_url": "str"
        }
      ],
      "assessment_report": [
        {
          "assessmentId": "str",
          "date": "str",
          "time": "str",
          "chapterName": "str",
          "score": "str",
          "grade": "str",
          "comments": "str",
          "learning_gaps": "str",
          "remarks": "str",
          "report_url": "str"
        }
      ],
      "remedy_report": [
        {
          "remedyId": "str",
          "date": "str",
          "time": "str",
          "topic": "str",
          "actionTaken": "str",
          "outcome": "str",
          "learning_gaps": "str",
          "remarks": "str",
          "report_url": "str"
        }
      ]
    }
  }
  ```

#### `class_reports` Collection

- **Purpose**: Class-level aggregated performance analytics
- **Used by Routes**:
  - `GET /api/details/class_report/board/{board}/grade/{grade}/section/{section}` - Get class report
- **Used by Agents**: None (direct controller operations)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "teacherId": "str",
    "schoolId": "str",
    "board": "str",
    "grade": "str",
    "section": "str",
    "students": [{ "studentId": "str", "name": "str" }],
    "report": {
      "inclass_report": [
        {
          "reportId": "str",
          "date": "str",
          "time": "str",
          "chapterName": "str",
          "averageScore": "str",
          "participationRate": "str",
          "notes": "str",
          "learning_gaps": "str",
          "remarks": "str",
          "report_url": "str"
        }
      ],
      "after_hour_session_report": [
        {
          "sessionId": "str",
          "date": "str",
          "time": "str",
          "worksheetId": "str",
          "completionRate": "str",
          "averageScore": "str",
          "feedback": "str",
          "learning_gaps": "str",
          "remarks": "str",
          "report_url": "str"
        }
      ],
      "daily_report": [
        {
          "reportId": "str",
          "date": "str",
          "time": "str",
          "attendanceSummary": "dict",
          "classActivities": "str",
          "learning_gaps": "str",
          "remarks": "str",
          "report_url": "str"
        }
      ],
      "assessment_report": [
        {
          "assessmentId": "str",
          "date": "str",
          "time": "str",
          "chapterName": "str",
          "averageScore": "str",
          "gradeDistribution": "dict",
          "comments": "str",
          "learning_gaps": "str",
          "remarks": "str",
          "report_url": "str"
        }
      ],
      "remedy_report": [
        {
          "remedyId": "str",
          "date": "str",
          "time": "str",
          "topicsAddressed": "str",
          "actionsTaken": "str",
          "outcome": "str",
          "learning_gaps": "str",
          "remarks": "str",
          "report_url": "str"
        }
      ]
    }
  }
  ```

### 5. **Timetable Collections**

#### `timetable` Collection

- **Purpose**: Timetable events and scheduling
- **Used by Routes**:
  - `GET /api/timetable/daily-schedule` - Get daily schedule
  - `POST /api/timetable/event/{event_id}/complete` - Complete timetable event
- **Used by Agents**: None (direct controller operations)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "class_id": "str",
    "teacher_id": "str",
    "scheduled_date": "datetime",
    "duration_minutes": "int",
    "event_type": "str",
    "status": "str",
    "is_holiday": "bool",
    "school_id": "str",
    "created_at": "datetime",
    "updated_at": "datetime",
    "planned_lesson_id": "str"
  }
  ```

#### `pdf_timetable` Collection

- **Purpose**: PDF timetable storage and metadata
- **Used by Routes**:
  - `POST /api/timetable/upload-pdf` - Upload timetable PDF
- **Used by Agents**: None (direct controller operations)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "class_id": "str",
    "school_id": "str",
    "academic_year": "str",
    "generated_by_user_id": "str",
    "file_name": "str",
    "created_at": "datetime",
    "updated_at": "datetime",
    "teachers": [{ "teacher_id": "str", "name": "str" }],
    "encoded_file": "str"
  }
  ```

### 6. **Job Management Collections**

#### `jobs` Collection

- **Purpose**: Background job tracking and status
- **Used by Routes**:
  - `GET /api/v1/jobs/{job_id}` - Get job status
  - `GET /api/v1/debug/jobs` - Debug all jobs
  - `GET /api/v1/debug/jobs/{job_id}` - Debug specific job
- **Used by Agents**: All agents (Content, Assessment, Remedy)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "job_id": "str",
    "route": "str", // "AHS", "REMEDY", "ASSESSMENT"
    "status": "str", // "pending", "in_progress", "completed", "failed"
    "progress": "int",
    "error": "str",
    "result_doc_id": "str",
    "payload": "dict",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
  ```

#### `remedy_plans` Collection

- **Purpose**: Remediation plans and gap analysis
- **Used by Routes**:
  - `GET /api/v1/remedyJobs/{job_id}/plans` - Get remedy plans
  - `GET /api/v1/remedyJobs/{job_id}/content` - Get remedy content
- **Used by Agents**: Remedy Agent
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "remedy_id": "str",
    "student_id": "str",
    "teacher_class_id": "str",
    "classified_gaps": [{ "code": "str", "evidence": ["str"] }],
    "remediation_plans": [
      {
        "gap_type": "str",
        "selected_modes": ["str"],
        "content_specifications": "dict",
        "priority": "int",
        "estimated_duration_minutes": "int"
      }
    ],
    "context_refs": "dict",
    "prerequisite_discoveries": "dict",
    "status": "str",
    "created_at": "datetime",
    "updated_at": "datetime",
    "content_job_ids": ["str"],
    "completion_status": {
      "total_plans": "int",
      "completed_plans": "int",
      "failed_plans": "int"
    }
  }
  ```

### 7. **Teacher Management Collections**

#### `teacher_class_data` Collection

- **Purpose**: Teacher-class relationships and curriculum data
- **Used by Routes**:
  - `GET /api/teacher_class_data/{class_id}/chapters` - Get chapters
  - `PUT /api/teacher_class_data/{class_id}/chapters` - Update chapters
- **Used by Agents**: Content Agent, Assessment Agent (for context)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "className": "str",
    "subject": "str",
    "academicYear": "str",
    "school": { "schoolId": "str", "name": "str" },
    "board": "str",
    "teacherId": "str",
    "teacherName": "str",
    "sessions": { "completed": ["str"], "upcoming": ["str"] },
    "curriculum": {
      "indexPdfUrl": "str",
      "chapters": [
        {
          "chapterId": "str",
          "title": "str",
          "status": "str",
          "chapterSessions": ["str"],
          "uploadedContent": { "pdfs": ["str"], "question_bank": "dict" }
        }
      ]
    },
    "classId": "str",
    "uploadedContent": {
      "chapterMaterial": [{ "contentId": "str", "title": "str", "url": "str" }]
    }
  }
  ```

### 8. **RAG System Collections**

#### `prerequisite_cache` Collection

- **Purpose**: Cached prerequisite discoveries for performance
- **Used by Routes**: RAG routes
- **Used by Agents**: Remedy Agent (prerequisite discovery)
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "gap_code": "str",
    "grade_level": "str",
    "subject": "str",
    "prerequisites": [
      {
        "topic": "str",
        "grade_level": "str",
        "priority": "int",
        "description": "str",
        "learning_objectives": ["str"],
        "success_rate": "float",
        "source": "str"
      }
    ],
    "created_at": "datetime",
    "expires_at": "datetime"
  }
  ```

#### `remediation_logs` Collection

- **Purpose**: Logs of remediation activities and outcomes
- **Used by Routes**: None (internal logging)
- **Used by Agents**: Remedy Agent, Content Agent
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "plan_id": "str",
    "student_id": "str",
    "gap_type": "str",
    "cycle": "int",
    "result": "dict",
    "created_at": "datetime"
  }
  ```

#### `validation_logs` Collection

- **Purpose**: Validation results for learning modes
- **Used by Routes**: None (internal logging)
- **Used by Agents**: Content Agent
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "mode": "str",
    "is_valid": "bool",
    "errors": "dict",
    "metadata": "dict",
    "created_at": "datetime"
  }
  ```

#### `session_progress` Collection

- **Purpose**: Session progress tracking
- **Used by Routes**: None (internal tracking)
- **Used by Agents**: Content Agent
- **Key Fields**:
  ```json
  {
    "_id": "ObjectId",
    "session_id": "str",
    "progress": "dict",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
  ```

---

## 🤖 Agent to Collection Mapping

### **Content Agent**

- **Primary Collections**: `sessions`, `jobs`, `teacher_class_data`, `student_reports`
- **Secondary Collections**: `lesson_script`, `question_bank`, `validation_logs`, `session_progress`
- **Routes Used**:
  - `POST /api/v1/contentGenerationForAHS`
  - `POST /api/v1/contentGenerationForRemedies`
  - `GET /api/v1/jobs/{job_id}/content`

### **Assessment Agent**

- **Primary Collections**: `templates`, `assessments`, `question_bank`, `jobs`
- **Secondary Collections**: `lesson_script`, `teacher_class_data`
- **Routes Used**:
  - `POST /api/assessments/generate`
  - `GET /api/assessments/status/{job_id}`
  - `GET /api/assessments/{assessment_id}`

### **Remedy Agent**

- **Primary Collections**: `remedy_plans`, `jobs`, `student_reports`
- **Secondary Collections**: `prerequisite_cache`, `remediation_logs`
- **Routes Used**:
  - `POST /api/v1/contentGenerationForRemedies`
  - `GET /api/v1/remedyJobs/{job_id}/plans`
  - `GET /api/v1/remedyJobs/{job_id}/content`

---

## 🛠️ Creating New GET Routes

### **Step-by-Step Guide**

1. **Identify the Collection**: Determine which collection contains the data you need
2. **Check Existing Patterns**: Look at similar routes in the codebase
3. **Create Controller Method**: Add method to appropriate controller in `core/api/controllers/`
4. **Create Route**: Add route in `core/api/routes/`
5. **Add Schema**: Define request/response schemas in `core/api/schemas/`

### **Example: Creating a GET Route for Student Performance**

```python
# 1. Controller Method (core/api/controllers/student_controller.py)
@staticmethod
async def get_student_performance(student_id: str, class_id: str):
    """Get student performance data"""
    from core.services.db_operations.base import student_reports_collection

    report = await student_reports_collection.find_one({
        "studentId": student_id,
        "classId": class_id
    })

    if not report:
        raise HTTPException(404, "Student report not found")

    return report

# 2. Route (core/api/routes/student.py)
@router.get("/students/{student_id}/performance")
async def get_student_performance(student_id: str, class_id: str):
    return await StudentController.get_student_performance(student_id, class_id)

# 3. Schema (core/api/schemas/student_schemas.py)
class StudentPerformanceResponse(BaseModel):
    studentId: str
    classId: str
    report: Dict[str, Any]
```

### **Common Query Patterns**

```python
# Find by ID
await collection.find_one({"_id": ObjectId(id)})

# Find by multiple fields
await collection.find_one({"studentId": student_id, "classId": class_id})

# Find multiple documents
await collection.find({"status": "active"}).to_list(length=100)

# Find with projection
await collection.find_one({"_id": ObjectId(id)}, {"field1": 1, "field2": 1})

# Find with sorting
await collection.find({"teacherId": teacher_id}).sort("created_at", -1).to_list(length=10)
```

---

## 📝 Notes for Developers

1. **Always use async/await** for database operations
2. **Handle ObjectId conversion** properly (string to ObjectId and vice versa)
3. **Use proper error handling** with HTTPException
4. **Follow existing naming conventions** for routes and methods
5. **Add proper type hints** for better code maintainability
6. **Use the base.py collections** instead of creating new database connections
7. **Test your routes** with the existing test framework

---

## 🔍 Quick Reference

| Collection           | Primary Use          | Key Routes                      | Key Agents                  |
| -------------------- | -------------------- | ------------------------------- | --------------------------- |
| `users`              | User management      | `/api/user/*`                   | None                        |
| `sessions`           | Content storage      | `/api/v1/sessions/*`            | Content Agent               |
| `question_bank`      | Question repository  | Assessment routes               | Assessment Agent            |
| `student_reports`    | Performance tracking | `/api/details/student_report/*` | Content Agent, Remedy Agent |
| `jobs`               | Job tracking         | `/api/v1/jobs/*`                | All Agents                  |
| `remedy_plans`       | Remediation plans    | `/api/v1/remedyJobs/*`          | Remedy Agent                |
| `templates`          | Assessment templates | `/api/assessments/*`            | Assessment Agent            |
| `teacher_class_data` | Teacher-class data   | `/api/teacher_class_data/*`     | Content Agent               |

This mapping should help you quickly understand which collections to use for new routes and how the existing system is structured.
