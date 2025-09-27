# PupilTree Agents - Comprehensive System Guide

## 🎯 Overview

PupilTree Agents is an advanced AI-powered educational platform that generates personalized learning content, assessments, and remediation plans. The system uses multiple specialized agents working together to create comprehensive educational experiences.

## 🏗️ System Architecture

### Core Components

1. **API Layer** - FastAPI-based REST API with modular structure
2. **Agent System** - Three main agents (Content, Assessment, Remedy)
3. **Graph Workflows** - LangGraph-based state machines
4. **Learning Modes** - 8 different content generation modalities
5. **Database Layer** - MongoDB with structured collections
6. **RAG System** - Vector search and prerequisite discovery
7. **Real-time Processing** - Background job system with WebSocket support

### Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: MongoDB with Motor (async driver)
- **AI/ML**: LangGraph, Google Gemini, Pinecone
- **Vector Search**: Pinecone for semantic search
- **Real-time**: Socket.IO for live updates
- **File Storage**: Google Cloud Storage
- **Task Processing**: Async background jobs

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

## 🚀 API Endpoints Summary

### Content Generation

- `POST /api/v1/contentGenerationForAHS` - Generate after-hour session content
- `POST /api/v1/contentGenerationForRemedies` - Generate remediation content

### Job Management

- `GET /api/v1/jobs/{job_id}` - Get job status
- `GET /api/v1/jobs/{job_id}/content` - Get generated content
- `GET /api/v1/remedyJobs/{job_id}/plans` - Get remediation plans
- `GET /api/v1/jobs/{job_id}/aggregate` - Get aggregated results

### Assessments

- `POST /api/assessments/generate` - Generate assessments
- `GET /api/assessments/status/{job_id}` - Get assessment status
- `GET /api/assessments/{assessment_id}` - Get assessment details

### User Management

- `POST /api/user/register` - Register user
- `POST /api/user/login` - Login user
- `GET /api/user/current` - Get current user
- `GET /api/user/` - List users
- `PUT /api/user/{user_id}` - Update user
- `DELETE /api/user/{user_id}` - Delete user

### Curriculum

- `GET /api/grades` - Get all grades
- `GET /api/grades/{grade_id}/sections` - Get sections for grade
- `GET /api/grades/{grade_id}/sections/{section_name}` - Get subjects
- `GET /api/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}` - Get chapters
- `GET /api/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}/chapters/{chapter_name}/periods` - Get periods

### Timetable

- `POST /api/timetable/upload-pdf` - Upload timetable PDF
- `POST /api/timetable/ingest-from-db` - Ingest timetable from database
- `POST /api/timetable/pair-lessons` - Pair lessons for teacher
- `GET /api/timetable/daily-schedule` - Get daily schedule
- `POST /api/timetable/event/{event_id}/complete` - Complete timetable event

### RAG System

- `POST /api/rag/ncert/ingest` - Ingest NCERT content
- `GET /api/rag/ncert/status` - Get ingestion status
- `POST /api/rag/ncert/qa` - Query NCERT content
- `POST /api/rag/ncert/prerequisites` - Discover prerequisites

### Teacher Management

- `POST /api/teacher/` - Create teacher
- `POST /api/teacher/{teacher_id}/lecture` - Add lecture
- `DELETE /api/teacher/{teacher_id}/lecture` - Delete lecture
- `GET /api/teacher_class_data/{class_id}/chapters` - Get chapters
- `PUT /api/teacher_class_data/{class_id}/chapters` - Update chapters

## 🧠 Learning Modes

The system supports 8 different learning modalities:

### 1. Learn by Reading

- Structured reading materials
- Summaries and key points
- Glossary and memory hacks
- Visual questions and assets

### 2. Learn by Writing

- Writing prompts for assessment
- Open-ended questions
- Reflection exercises

### 3. Learn by Watching

- Curated video content
- Video summaries
- Educational video links

### 4. Learn by Playing

- Educational games and activities
- Interactive learning objectives
- Gamified content

### 5. Learn by Doing

- Hands-on experiments
- Safe home activities
- Step-by-step instructions
- Safety notes and evaluation criteria

### 6. Learn by Solving

- Practice problems with progressive difficulty
- Multiple question types (MCQ, FITB, Short)
- Solution explanations

### 7. Learn by Questioning & Debating

- Debate scenarios and personas
- Critical thinking prompts
- Discussion frameworks

### 8. Learn by Listening & Speaking

- Audio scripts and verbal interactions
- Speaking exercises
- Listening comprehension

### 9. Learning by Assessment

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

### 1. Personalized Content Generation

- Adapts content based on learning gaps
- Considers student performance history
- Tailors difficulty and approach

### 2. Multi-Modal Learning

- 8 different learning approaches
- Coordinated content delivery
- Progressive difficulty scaling

### 3. Intelligent Remediation

- Gap classification and analysis
- Prerequisite discovery
- Multi-cycle remediation support

### 4. Assessment Generation

- Automated question creation
- Multiple question types
- Performance tracking

### 5. RAG Integration

- NCERT content ingestion
- Semantic search capabilities
- Prerequisite discovery

### 6. Real-time Processing

- Background job processing
- Progress tracking
- WebSocket support for real-time updates

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

### Installation

```bash
pip install -r requirements.txt
python main.py
```

### API Access

- **Base URL**: `http://localhost:8080/api`
- **Documentation**: `http://localhost:8080/docs`
- **WebSocket**: `ws://localhost:8080/ws`

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

## 🔧 Development

### Project Structure

```
core/
├── agents/          # Agent implementations
├── api/            # API routes and controllers
├── graphs/         # LangGraph workflows
├── models/         # Data models
├── nodes/          # Learning mode nodes
└── services/       # Business logic and database operations
```

### Testing

- Unit tests in `tests/` directory
- Integration tests for API endpoints
- Performance tests for RAG system
- Agent workflow tests

### Scripts

- `scripts/` directory contains utility scripts
- Database setup and migration scripts
- Performance testing scripts
- Debug and monitoring tools

## 📚 Documentation

- **System Overview**: `docs/SYSTEM_OVERVIEW.md`
- **API Documentation**: `docs/API_DOCUMENTATION.md`
- **Developer Onboarding**: `docs/DEVELOPER_ONBOARDING.md`
- **Migration Guides**: `docs/migration/`
- **Agent Documentation**: `docs/REMEDY_AGENT_README.md`

## 🎯 Use Cases

### 1. After Hour Session Content

Generate comprehensive learning content for students to study after class hours, including reading materials, videos, games, and practice questions.

### 2. Learning Gap Remediation

Identify and address specific learning gaps through personalized content and multi-modal learning approaches.

### 3. Assessment Generation

Create educational assessments with questions tailored to specific topics, difficulty levels, and learning objectives.

### 4. Curriculum Management

Manage educational content structure with grades, sections, subjects, and chapters.

### 5. Timetable Management

Upload and process timetable PDFs, create lesson plans, and manage class schedules.

### 6. RAG-Powered Learning

Use semantic search to find relevant educational content and discover prerequisite knowledge.

## 🔮 Future Enhancements

- Advanced analytics and reporting
- Multi-language support
- Integration with external LMS systems
- Enhanced personalization algorithms
- Mobile app development
- Collaborative learning features

---

This comprehensive guide provides a complete overview of the PupilTree Agents system, covering architecture, APIs, workflows, and usage scenarios. The system represents a sophisticated approach to AI-powered educational content generation with real-time processing and personalized learning experiences.
