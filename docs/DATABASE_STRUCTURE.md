# PupilTree Agents - Database Structure Documentation

## 🗄️ Overview

The PupilTree Agents system uses **three MongoDB databases** to organize different aspects of the educational platform:

1. **Pupil_teach** - Main application database
2. **Pupil_learn** - Learning analytics and gap tracking
3. **Pupil-Amigo** - AI components and generated content

---

## 📊 Database 1: Pupil_teach (Main Application)

### Core Educational Data Collections

#### `lesson_script`

**Purpose**: Curriculum structure and educational content organization

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

#### `sessions`

**Purpose**: Class session data with generated content

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
    "mcqs": [
      {
        "question": "str",
        "options": ["str"],
        "answer": "str"
      }
    ],
    "shortAnswer": [
      {
        "question": "str"
      }
    ]
  },
  "lessonScript": {
    "scriptId": "str",
    "creationMethod": "str",
    "estimatedReadingTimeInMinutes": "int",
    "scriptContent": "str"
  },
  "afterHourSession": {
    "texts": [
      {
        "title": "str",
        "url": "str"
      }
    ],
    "videos": [
      {
        "title": "str",
        "url": "str"
      }
    ],
    "games": [
      {
        "title": "str",
        "url": "str"
      }
    ],
    "practiceQuestions": {
      "questions": [
        {
          "question": "str",
          "options": ["str"],
          "answer": "str"
        }
      ]
    },
    "assessmentQuestions": {
      "questions": [
        {
          "question": "str",
          "answerGuide": "str",
          "questionType": "str"
        }
      ]
    },
    "status": "str"
  }
}
```

#### `question_bank`

**Purpose**: Question repository with comprehensive metadata

```json
{
  "_id": "ObjectId",
  "questionText": "str",
  "questionType": "str",
  "origin": "str",
  "options": [
    {
      "key": "str",
      "text": "str"
    }
  ],
  "answer": {
    "key": "str",
    "explanation": "str"
  },
  "difficulty": "str",
  "grade": "str",
  "topics": ["str"],
  "learningOutcomes": ["str"],
  "usageHistory": [
    {
      "setId": "str",
      "setType": "str",
      "dateUsed": "str"
    }
  ],
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

### User Management Collections

#### `users`

**Purpose**: User accounts with comprehensive profiles

```json
{
  "_id": "ObjectId",
  "name": "str",
  "email": "str",
  "password_hash": "str",
  "role": "str",
  "institution_id": "str",
  "auth_tokens": [],
  "profile": {
    "current_class_id": "str",
    "parent_details": [
      {
        "name": "str",
        "email": "str",
        "phone_number": "str"
      }
    ],
    "gamification_stats": {
      "points": "int",
      "streaks": "int",
      "badges": ["str"]
    },
    "specialized_subjects": "NoneType",
    "assigned_classes": "NoneType"
  },
  "created_at": "datetime"
}
```

#### `teacher_class_data`

**Purpose**: Teacher-class relationships with curriculum

```json
{
  "_id": "ObjectId",
  "className": "str",
  "subject": "str",
  "academicYear": "str",
  "school": {
    "schoolId": "str",
    "name": "str"
  },
  "board": "str",
  "teacherId": "str",
  "teacherName": "str",
  "sessions": {
    "completed": ["str"],
    "upcoming": ["str"]
  },
  "curriculum": {
    "indexPdfUrl": "str",
    "chapters": [
      {
        "chapterId": "str",
        "title": "str",
        "status": "str",
        "chapterSessions": ["str"],
        "uploadedContent": {
          "pdfs": ["str"],
          "question_bank": {
            "1": "str",
            "2": "str"
          }
        }
      }
    ]
  },
  "classId": "str",
  "uploadedContent": {
    "chapterMaterial": [
      {
        "contentId": "str",
        "title": "str",
        "url": "str"
      }
    ]
  }
}
```

### Reporting Collections

#### `student_reports`

**Purpose**: Comprehensive student performance tracking

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

#### `class_reports`

**Purpose**: Class-level aggregated performance analytics

```json
{
  "_id": "ObjectId",
  "subject": "str",
  "teacher_id": "ObjectId",
  "hod_id": "ObjectId",
  "class_id": "ObjectId",
  "total_assessment": "int",
  "average_grade": "float",
  "pass_rate": "float",
  "difficulty": "str",
  "schoolId": "str",
  "reportType": "str"
}
```

### Assessment Collections

#### `templates`

**Purpose**: Assessment templates with detailed schemes

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
          "Integer": {
            "single_digit": "int"
          }
        }
      }
    ]
  },
  "instructions": ["str"]
}
```

#### `assessments`

**Purpose**: Assessment data with performance metrics

```json
{
  "_id": "ObjectId",
  "school_id": "str",
  "class_id": "str",
  "assigned_teachers": [
    {
      "id": "str",
      "name": "str",
      "subject": "str"
    }
  ],
  "subject": "str",
  "duration": "int",
  "datetime": "datetime",
  "marks": "int",
  "performance": {
    "average_score": "int",
    "completion_rate": "int",
    "pass_rate": "int",
    "detailed_results": []
  },
  "question_ids": ["str"],
  "student_list": [
    {
      "student_id": "str",
      "performance": {
        "score": "int",
        "completed": "bool",
        "passed": "bool"
      }
    }
  ]
}
```

### Timetable Collections

#### `timetable`

**Purpose**: Schedule management with events and holidays

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

#### `pdf_timetable`

**Purpose**: Timetable PDF storage

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
  "teachers": [
    {
      "teacher_id": "str",
      "name": "str"
    }
  ],
  "encoded_file": "str"
}
```

### Administrative Collections

#### `institutions`

**Purpose**: School and organization data

```json
{
  "_id": "ObjectId",
  "name": "str",
  "address": {
    "street": "str",
    "city": "str",
    "country": "str"
  },
  "boards": ["str"],
  "admin_ids": [
    {
      "name": "str",
      "designation": "str",
      "adminId": "ObjectId"
    }
  ],
  "classes": [
    {
      "name": "str",
      "student_list": ["ObjectId"],
      "classId": "str"
    }
  ],
  "teachers": [
    {
      "name": "str",
      "id": "str"
    }
  ],
  "created_at": "datetime"
}
```

#### `dean_dashboard`

**Purpose**: Administrative oversight with metrics

```json
{
  "_id": "ObjectId",
  "student_attendance_rate": "float",
  "teacher_attendance_rate": "float",
  "total_faculty": "int",
  "students_attendance_boost": "float",
  "teacher_attendance_overall": {
    "present_today": "int",
    "absent_today": "int",
    "on_leave": "int",
    "week_average": "float",
    "absent_teachers": {
      "teacher_name": "str",
      "subject": "str",
      "leave_reason": "str"
    }
  },
  "institution_id": "str",
  "performance": "str"
}
```

---

## 📊 Database 2: Pupil_learn (Learning Analytics)

### Learning Gap Management

#### `gaps`

**Purpose**: Learning gap tracking with history

```json
{
  "_id": "ObjectId",
  "date_created": "str",
  "gap_type": "str",
  "created_by": "str",
  "resolved_on": "str",
  "feedback": "str",
  "gap_history": [
    {
      "id": "str",
      "gap_id": "str",
      "first_attempt": "str",
      "what_made": "str",
      "when": "str",
      "status": "str",
      "type": "str"
    }
  ]
}
```

#### `Student_gaps`

**Purpose**: Student-specific gap management

```json
{
  "_id": "ObjectId",
  "studentId": "str",
  "open_gaps": "str",
  "closed_gaps": "str",
  "current_gaps": {
    "open": [
      {
        "gap_id": "str"
      }
    ],
    "closed": [
      {
        "gap_id": "str"
      }
    ]
  },
  "historic_gaps": {
    "open": [
      {
        "gap_id": "str"
      }
    ],
    "closed": [
      {
        "gap_id": "str"
      }
    ]
  }
}
```

---

## 📊 Database 3: Pupil-Amigo (AI Components)

### AI-Generated Content

#### `questions_new`

**Purpose**: AI-generated questions (empty collection)

#### `tutor_chat_history`

**Purpose**: Chat interaction logs (empty collection)

#### `Assesment_questions`

**Purpose**: Assessment question bank (empty collection)

### File Storage

#### `fs.files` & `fs.chunks`

**Purpose**: GridFS for file storage (PDFs, images, etc.)

```json
{
  "_id": "ObjectId",
  "filename": "str",
  "contentType": "str",
  "chunkSize": "int",
  "length": "Int64",
  "uploadDate": "datetime"
}
```

---

## 🔗 Database Relationships

### Key Relationships

1. **Users ↔ Teacher Class Data**: One-to-many relationship through `teacherId`
2. **Sessions ↔ Teacher Class Data**: Linked through `teacherClassDataId`
3. **Student Reports ↔ Users**: Linked through `studentId` and `teacherId`
4. **Assessments ↔ Question Bank**: Linked through `question_ids`
5. **Timetable ↔ Classes**: Linked through `class_id`
6. **Institutions ↔ Users**: Linked through `institution_id`

### Data Flow

1. **Content Generation**: Sessions → Question Bank → Assessments
2. **Performance Tracking**: Student Reports → Class Reports → Dean Dashboard
3. **Learning Analytics**: Gaps → Student Gaps → Remediation Plans
4. **Administrative**: Users → Institutions → Classes → Timetable

---

## 📈 Performance Considerations

### Indexing Strategy

1. **User Queries**: Index on `email`, `role`, `institution_id`
2. **Session Queries**: Index on `teacherClassDataId`, `sessionDate`
3. **Report Queries**: Index on `studentId`, `classId`, `date`
4. **Assessment Queries**: Index on `class_id`, `subject`, `datetime`
5. **Timetable Queries**: Index on `class_id`, `teacher_id`, `scheduled_date`

### Data Archival

1. **Old Sessions**: Archive sessions older than 2 years
2. **Completed Assessments**: Archive after 1 year
3. **Resolved Gaps**: Archive after 6 months
4. **Old Reports**: Archive reports older than 3 years

---

## 🔧 Maintenance Scripts

### Database Cleanup

```bash
# Archive old sessions
python scripts/archive_old_sessions.py

# Clean up orphaned records
python scripts/cleanup_orphaned_data.py

# Optimize indexes
python scripts/optimize_indexes.py
```

### Data Migration

```bash
# Migrate user data
python scripts/migrate_users.py

# Update question bank
python scripts/update_question_bank.py

# Sync timetable data
python scripts/sync_timetable.py
```

---

This comprehensive database structure supports the full educational platform with proper data organization, relationships, and performance optimization.
