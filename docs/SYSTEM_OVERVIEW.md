# PupilTree Agents - System Overview & API Documentation

## 🏗️ System Architecture

PupilTree Agents is an AI-powered educational content generation platform built with FastAPI, MongoDB, and LangGraph. The system uses multiple specialized agents to generate personalized educational content, assessments, and remediation plans.

### Core Components

1. **API Layer** (`core/api/`)

   - FastAPI-based REST API with modular route structure
   - Controllers handle business logic
   - Schemas define request/response models

2. **Agent System** (`core/agents/`)

   - Content Agent: Generates educational content
   - Assessment Agent: Creates assessments and questions
   - Remedy Agent: Handles learning gap remediation

3. **Graph Workflows** (`core/graphs/`)

   - LangGraph-based state machines
   - Orchestrate complex multi-step processes
   - Handle content generation workflows

4. **Learning Modes** (`core/nodes/learning_mode_nodes/`)

   - 8 different learning modalities
   - Each mode generates specific content types
   - Coordinated through orchestration logic

5. **Database Layer** (`core/services/db_operations/`)
   - MongoDB collections for different data types
   - Async operations with Motor
   - Structured data models

## 📊 Database Structure

### Three MongoDB Databases

#### 1. **Pupil_teach** (Main Application Database)

**Core Educational Data:**

- **`lesson_script`** - Curriculum structure with grades/sections/subjects/chapters/periods
- **`sessions`** - Class sessions with lesson scripts, in-class questions, and after-hour content
- **`question_bank`** - Question repository with statistics, usage history, and student solutions
- **`student_reports`** - Comprehensive student performance tracking (inclass, after-hour, daily, assessment, remedy reports)
- **`class_reports`** - Class-level aggregated performance analytics
- **`teacher_reports`** - Teacher performance tracking
- **`subject_reports`** - Subject-wise analytics

**User Management:**

- **`users`** - User accounts with roles, profiles, gamification stats, and authentication
- **`teacher_class_data`** - Teacher-class associations with curriculum, sessions, and uploaded content
- **`institutions`** - School data with classes, teachers, and admin information
- **`invitations`** - User invitation management with permissions
- **`teacher_invitations`** - Teacher-specific invitations
- **`classes`** - Class structure with student-teacher relationships

**Assessment & Content:**

- **`templates`** - Assessment templates with detailed schemes and instructions
- **`assessments`** - Assessment data with performance metrics and student results
- **`assessment_review`** - Assessment review workflows with dean approval
- **`content_oversight`** - Content moderation and approval system

**Timetable & Scheduling:**

- **`timetable`** - Schedule management with events, holidays, and lesson planning
- **`pdf_timetable`** - Timetable PDF storage with encoded files
- **`transfers`** - Student transfer records

**Administrative:**

- **`dean_dashboard`** - Administrative oversight with attendance and performance metrics

#### 2. **Pupil_learn** (Learning Analytics Database)

**Learning Gap Management:**

- **`gaps`** - Learning gap tracking with history and resolution status
- **`Student_gaps`** - Student-specific gap management (open/closed/current/historic)

#### 3. **Pupil-Amigo** (AI Components Database)

**AI-Generated Content:**

- **`questions_new`** - AI-generated questions
- **`tutor_chat_history`** - Chat interaction logs
- **`Assesment_questions`** - Assessment question bank

**File Storage:**

- **`fs.files`** & **`fs.chunks`** - GridFS for file storage (PDFs, images, etc.)

## 🚀 API Endpoints

### Base URL: `/api`

### 1. Content Generation APIs

#### After Hour Session (AHS) Content

```http
POST /api/v1/contentGenerationForAHS
```

**Purpose**: Generate comprehensive after-hour learning content
**Request Body**:

```json
{
  "teacher_class_id": "string",
  "session_id": "string",
  "duration_minutes": 60,
  "grade_level": "10",
  "curriculum_goal": "string",
  "topic": "Physics - Newton's Laws",
  "context_refs": {
    "lesson_script_id": "string",
    "in_class_question_ids": ["string"],
    "recent_session_ids": ["string"],
    "recent_performance": {}
  },
  "learning_gaps": ["string"],
  "modes": ["learn_by_reading", "learn_by_watching", "learn_by_solving"],
  "options": {}
}
```

#### Remediation Content

```http
POST /api/v1/contentGenerationForRemedies
```

**Purpose**: Generate personalized remediation content for learning gaps
**Request Body**:

```json
{
  "teacher_class_id": "string",
  "student_id": "string",
  "duration_minutes": 30,
  "learning_gaps": [
    {
      "code": "PHY_001",
      "type": "conceptual_gap",
      "type_label": "Conceptual Gap",
      "evidence": ["struggled with force calculations"]
    }
  ],
  "context_refs": {
    "lesson_script_id": "string",
    "recent_performance": {}
  },
  "modes": ["learn_by_reading", "learn_by_doing"],
  "options": {
    "problems": { "count": 5 },
    "max_remediation_cycles": 3
  }
}
```

### 2. Job Management APIs

#### Get Job Status

```http
GET /api/v1/jobs/{job_id}
```

**Response**:

```json
{
  "job_id": "string",
  "status": "completed|pending|failed",
  "progress": 100,
  "error": null,
  "result_doc_id": "string"
}
```

#### Get Generated Content

```http
GET /api/v1/jobs/{job_id}/content
```

**Purpose**: Retrieve generated content after job completion

#### Get Remediation Plans

```http
GET /api/v1/remedyJobs/{job_id}/plans
```

**Purpose**: Get detailed remediation strategies and plans

#### Get Aggregated Results

```http
GET /api/v1/jobs/{job_id}/aggregate
```

**Purpose**: Get comprehensive view of job results with child jobs and content

### 3. Assessment APIs

#### Generate Assessment

```http
POST /api/assessments/generate
```

**Request Body**:

```json
{
  "target_exam": "CBSE_Grade10_Physics_Monthly",
  "exam_type": "monthly",
  "subject": "Physics",
  "class": "10A",
  "difficulty": "medium",
  "teacher_id": "string",
  "previous_topics": ["string"],
  "learning_gaps": ["string"],
  "file_url": "string"
}
```

#### Get Assessment Status

```http
GET /api/assessments/status/{job_id}
```

#### Get Assessment Details

```http
GET /api/assessments/{assessment_id}
```

### 4. User Management APIs

#### Authentication

```http
POST /api/user/register
POST /api/user/login
GET /api/user/current
```

#### User CRUD

```http
GET /api/user/
GET /api/user/{user_id}
PUT /api/user/{user_id}
DELETE /api/user/{user_id}
```

#### Role Management

```http
PUT /api/user/{user_id}/role
```

### 5. Curriculum & Details APIs

#### Get Educational Structure

```http
GET /api/grades
GET /api/grades/{grade_id}/sections
GET /api/grades/{grade_id}/sections/{section_name}
GET /api/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}
GET /api/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}/chapters/{chapter_name}/periods
```

#### Reports

```http
GET /api/student_report/{class_id}/{student_id}
GET /api/class_report/board/{board}/grade/{grade}/section/{section}
```

### 6. Timetable Management APIs

#### Upload Timetable

```http
POST /api/timetable/upload-pdf
```

**Form Data**:

- `file`: PDF file
- `class_id`: string
- `school_id`: string
- `academic_year`: string
- `generated_by_user_id`: string

#### Process Timetable

```http
POST /api/timetable/ingest-from-db
POST /api/timetable/pair-lessons
```

#### Schedule Management

```http
GET /api/timetable/daily-schedule?teacher_id={id}&class_id={id}&day={date}
POST /api/timetable/event/{event_id}/complete
```

### 7. RAG System APIs

#### NCERT Content Ingestion

```http
POST /api/rag/ncert/ingest
GET /api/rag/ncert/status
```

#### Query NCERT Content

```http
POST /api/rag/ncert/qa
```

**Request Body**:

```json
{
  "query": "What is Newton's first law?",
  "grade": "10",
  "subject": "Physics",
  "top_k": 8
}
```

#### Prerequisite Discovery

```http
POST /api/rag/ncert/prerequisites
```

**Request Body**:

```json
{
  "topic": "Quadratic Equations",
  "grade": "10",
  "subject": "Mathematics",
  "top_k": 12
}
```

### 8. Teacher Management APIs

#### Teacher Operations

```http
POST /api/teacher/
POST /api/teacher/{teacher_id}/lecture
DELETE /api/teacher/{teacher_id}/lecture
```

#### Class Data Management

```http
GET /api/teacher_class_data/{class_id}/chapters
PUT /api/teacher_class_data/{class_id}/chapters
```

### 9. After Hours Content APIs

#### Mock Content Generation

```http
POST /api/createContentForAfterhours
POST /api/createContentForRemedies
```

## 🧠 Learning Modes

The system supports 8 different learning modalities, each generating specific content types:

### 1. **Learn by Reading** (`learn_by_reading`)

- Structured reading materials
- Summaries and key points
- Glossary and memory hacks
- Visual questions and assets

### 2. **Learn by Writing** (`learn_by_writing`)

- Writing prompts for assessment
- Open-ended questions
- Reflection exercises

### 3. **Learn by Watching** (`learn_by_watching`)

- Curated video content
- Video summaries
- Educational video links

### 4. **Learn by Playing** (`learn_by_playing`)

- Educational games and activities
- Interactive learning objectives
- Gamified content

### 5. **Learn by Doing** (`learn_by_doing`)

- Hands-on experiments
- Safe home activities
- Step-by-step instructions
- Safety notes and evaluation criteria

### 6. **Learn by Solving** (`learn_by_solving`)

- Practice problems with progressive difficulty
- Multiple question types (MCQ, FITB, Short)
- Solution explanations

### 7. **Learn by Questioning & Debating** (`learn_by_questioning_debating`)

- Debate scenarios and personas
- Critical thinking prompts
- Discussion frameworks

### 8. **Learn by Listening & Speaking** (`learn_by_listening_speaking`)

- Audio scripts and verbal interactions
- Speaking exercises
- Listening comprehension

### 9. **Learning by Assessment** (`learning_by_assessment`)

- Formative assessments
- Progress tracking
- Performance evaluation

## 🔄 Agent Workflows

### Content Agent Workflow

1. **Orchestrator Node**: Analyzes requirements and selects learning modes
2. **Mode Execution**: Runs selected learning mode nodes in parallel
3. **Collector Node**: Aggregates content from all modes
4. **Persistence**: Saves content to appropriate database collections

### Remedy Agent Workflow

1. **Gap Classification**: Analyzes learning gaps and categorizes them
2. **Strategy Planning**: Determines remediation strategies
3. **Prerequisite Discovery**: Finds foundational knowledge gaps
4. **Content Integration**: Orchestrates content generation
5. **Finalization**: Creates comprehensive remediation plans

### Assessment Agent Workflow

1. **Schema Fetching**: Retrieves assessment templates
2. **Context Gathering**: Collects relevant educational content
3. **Question Generation**: Creates assessment questions
4. **Result Saving**: Stores questions and assessment metadata

## 🎯 Key Features

### 1. **Personalized Content Generation**

- Adapts content based on learning gaps
- Considers student performance history
- Tailors difficulty and approach

### 2. **Multi-Modal Learning**

- 8 different learning approaches
- Coordinated content delivery
- Progressive difficulty scaling

### 3. **Intelligent Remediation**

- Gap classification and analysis
- Prerequisite discovery
- Multi-cycle remediation support

### 4. **Assessment Generation**

- Automated question creation
- Multiple question types
- Performance tracking

### 5. **RAG Integration**

- NCERT content ingestion
- Semantic search capabilities
- Prerequisite discovery

### 6. **Real-time Processing**

- Background job processing
- Progress tracking
- WebSocket support for real-time updates

## 🔧 Technical Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: MongoDB with Motor (async driver)
- **AI/ML**: LangGraph, Google Gemini, Pinecone
- **Task Queue**: Async background processing
- **Real-time**: Socket.IO
- **Vector DB**: Pinecone for semantic search
- **File Storage**: Google Cloud Storage

## 📈 Performance & Monitoring

### Performance Dashboard

- System health monitoring
- Vector database statistics
- Performance metrics and recommendations
- A/B testing capabilities

### Job Tracking

- Real-time job status
- Progress monitoring
- Error handling and reporting
- Completion notifications

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- MongoDB instance
- Google Gemini API key
- Pinecone API key (optional)

### Environment Variables

```bash
MONGO_URI=mongodb://localhost:27017
GEMINI_API_KEY=your_gemini_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_environment
```

### Running the System

```bash
pip install -r requirements.txt
python main.py
```

The API will be available at `http://localhost:8080` with automatic documentation at `http://localhost:8080/docs`.

## 📚 Additional Resources

- **Developer Onboarding**: `docs/DEVELOPER_ONBOARDING.md`
- **Migration Guides**: `docs/migration/`
- **Agent Documentation**: `docs/REMEDY_AGENT_README.md`
- **Test Scripts**: `scripts/` directory
- **Performance Tests**: `tests/` directory

This system provides a comprehensive platform for AI-powered educational content generation, assessment creation, and personalized learning remediation.
