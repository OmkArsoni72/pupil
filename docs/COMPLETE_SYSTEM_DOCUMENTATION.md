# PupilTree Agents - Complete System Documentation

## 🎯 Executive Summary

PupilTree Agents is a comprehensive AI-powered educational platform that generates personalized learning content, assessments, and remediation plans. The system uses three specialized agents working with multiple learning modalities to create tailored educational experiences.

## 📋 Documentation Overview

This complete documentation package includes:

1. **[System Overview](SYSTEM_OVERVIEW.md)** - High-level architecture and API endpoints
2. **[API Documentation](API_DOCUMENTATION.md)** - Detailed API reference with examples
3. **[Database Structure](DATABASE_STRUCTURE.md)** - Complete database schema and relationships
4. **[Comprehensive Guide](COMPREHENSIVE_SYSTEM_GUIDE.md)** - Full system guide with use cases
5. **[Developer Onboarding](DEVELOPER_ONBOARDING.md)** - Setup and development guide

## 🏗️ System Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Agent System    │    │  Database Layer │
│   (FastAPI)     │◄──►│  (LangGraph)     │◄──►│   (MongoDB)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Controllers   │    │  Learning Modes │    │  Single Database │
│   Routes        │    │  (8 Modalities) │    │  Pupil_teach    │
│   Schemas       │    │  Workflows      │    │  (Main DB)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: MongoDB (1 database, 25+ collections)
- **AI/ML**: LangGraph, Google Gemini, Pinecone
- **Real-time**: Socket.IO, WebSocket support
- **File Storage**: GridFS, Google Cloud Storage
- **Vector Search**: Pinecone for semantic search

## 🗄️ Database Architecture

### Single MongoDB Database

#### **Pupil_teach** (Main Application Database - 25+ Collections)

- **Educational Data**: `lesson_script`, `sessions`, `question_bank`, `student_reports`
- **User Management**: `users`, `teacher_class_data`, `institutions`, `invitations`
- **Assessment**: `templates`, `assessments`, `assessment_review`
- **Timetable**: `timetable`, `pdf_timetable`, `transfers`
- **Job Management**: `jobs`, `remedy_plans`
- **RAG System**: `prerequisite_cache`, `remediation_logs`, `validation_logs`, `session_progress`
- **Administrative**: `dean_dashboard`, `content_oversight`

## 🚀 API Endpoints (50+ Endpoints)

### Content Generation APIs

- `POST /api/v1/contentGenerationForAHS` - After-hour session content
- `POST /api/v1/contentGenerationForRemedies` - Remediation content
- `GET /api/v1/jobs/{job_id}` - Job status tracking
- `GET /api/v1/jobs/{job_id}/content` - Generated content retrieval

### Assessment APIs

- `POST /api/assessments/generate` - Generate assessments
- `GET /api/assessments/status/{job_id}` - Assessment status
- `GET /api/assessments/{assessment_id}` - Assessment details

### User Management APIs

- `POST /api/user/register` - User registration
- `POST /api/user/login` - User authentication
- `GET /api/user/current` - Current user info
- `PUT /api/user/{user_id}` - Update user details

### Curriculum APIs

- `GET /api/grades` - Get all grades
- `GET /api/grades/{grade_id}/sections` - Get sections
- `GET /api/grades/{grade_id}/sections/{section_name}` - Get subjects
- `GET /api/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}` - Get chapters

### Timetable APIs

- `POST /api/timetable/upload-pdf` - Upload timetable PDF
- `POST /api/timetable/ingest-from-db` - Process timetable
- `GET /api/timetable/daily-schedule` - Get daily schedule

### RAG System APIs

- `POST /api/rag/ncert/ingest` - Ingest NCERT content
- `POST /api/rag/ncert/qa` - Query content
- `POST /api/rag/ncert/prerequisites` - Discover prerequisites

## 🧠 Learning Modes (8 Modalities)

### 1. **Learn by Reading** (`learn_by_reading`)

- Structured reading materials with summaries
- Key points and glossary
- Visual questions and memory hacks

### 2. **Learn by Writing** (`learn_by_writing`)

- Writing prompts and assessments
- Open-ended questions
- Reflection exercises

### 3. **Learn by Watching** (`learn_by_watching`)

- Curated video content
- Video summaries and educational links
- YouTube integration

### 4. **Learn by Playing** (`learn_by_playing`)

- Educational games and activities
- Interactive learning objectives
- Gamified content

### 5. **Learn by Doing** (`learn_by_doing`)

- Hands-on experiments
- Safe home activities
- Step-by-step instructions with safety notes

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

## 🔄 Agent Workflows

### Content Agent Workflow

1. **Orchestrator Node**: Analyzes requirements and selects learning modes
2. **Mode Execution**: Runs selected learning mode nodes in parallel
3. **Collector Node**: Aggregates content from all modes
4. **Persistence**: Saves content to database collections

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

## 📊 Data Flow

```
User Request → API Layer → Agent System → Learning Modes → Content Generation
     ↓              ↓           ↓            ↓              ↓
Database ← Persistence ← Collector ← Orchestrator ← Context Analysis
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- MongoDB instance
- Google Gemini API key
- Pinecone API key (optional)

### Environment Setup

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

## 📚 Use Cases

### 1. **After Hour Session Content**

Generate comprehensive learning content for students to study after class hours, including reading materials, videos, games, and practice questions.

### 2. **Learning Gap Remediation**

Identify and address specific learning gaps through personalized content and multi-modal learning approaches.

### 3. **Assessment Generation**

Create educational assessments with questions tailored to specific topics, difficulty levels, and learning objectives.

### 4. **Curriculum Management**

Manage educational content structure with grades, sections, subjects, and chapters.

### 5. **Timetable Management**

Upload and process timetable PDFs, create lesson plans, and manage class schedules.

### 6. **RAG-Powered Learning**

Use semantic search to find relevant educational content and discover prerequisite knowledge.

## 🔮 Future Enhancements

- Advanced analytics and reporting
- Multi-language support
- Integration with external LMS systems
- Enhanced personalization algorithms
- Mobile app development
- Collaborative learning features

## 📞 Support & Resources

### Documentation Files

- **System Overview**: `docs/SYSTEM_OVERVIEW.md`
- **API Documentation**: `docs/API_DOCUMENTATION.md`
- **Database Structure**: `docs/DATABASE_STRUCTURE.md`
- **Comprehensive Guide**: `docs/COMPREHENSIVE_SYSTEM_GUIDE.md`
- **Developer Onboarding**: `docs/DEVELOPER_ONBOARDING.md`

### Scripts & Tools

- **Setup Scripts**: `scripts/` directory
- **Test Scripts**: `tests/` directory
- **Migration Tools**: `docs/migration/` directory

---

## 🎯 Summary

PupilTree Agents represents a sophisticated approach to AI-powered educational content generation with:

- **3 MongoDB databases** with 25+ collections
- **50+ API endpoints** for comprehensive functionality
- **8 learning modalities** for diverse content generation
- **3 specialized agents** for different educational tasks
- **Real-time processing** with WebSocket support
- **RAG integration** for intelligent content discovery
- **Comprehensive reporting** and analytics

The system provides a complete platform for personalized educational content generation, assessment creation, and learning gap remediation, making it a powerful tool for modern educational institutions.

---

_This documentation package provides everything needed to understand, deploy, and maintain the PupilTree Agents system._
