# Google Technology Implementation Guide

## Overview
This document outlines all Google technologies implemented in PupilPrep for AI-powered personalized learning.

## 1. Google Gemini API (Generative AI)

### Purpose
- Generate personalized learning content
- Create adaptive assessments
- Generate remedial content based on student performance
- Provide intelligent tutoring responses

### Implementation Files
- `core/services/ai/llm_client.py` - Gemini model client
- `core/agents/content_agent.py` - Content generation agent
- `core/agents/assessment_agent.py` - Assessment generation agent
- `core/agents/remedy_agent.py` - Remedial content agent

### Key Features
```python
# Model: Gemini 2.5 Flash (latest)
- Fast response times
- Cost-effective
- Multimodal capabilities (text, images, PDFs)
- Context window: 100,000 tokens
```

### Setup
```bash
# Set API key
export GEMINI_API_KEY="your_api_key_here"

# Models available
- gemini-2.5-flash (recommended)
- gemini-2.0-flash
- gemini-1.5-pro
```

### Usage Example
```python
from core.services.ai.llm_client import LLMFactory

llm_factory = LLMFactory()
client = llm_factory.get_client("gemini_2.5_flash")

# Generate content
prompt = "Create a physics lesson on Newton's Laws for grade 10"
response = client.chat(prompt)
```

---

## 2. Google Cloud Storage (GCS)

### Purpose
- Store educational videos
- Archive student submissions
- Store PDF study materials
- Backup learning content

### Features
- Scalable blob storage
- Direct video streaming
- Cost-effective for large files
- Integration with other Google services

### Setup
```bash
# Initialize GCS client
from google.cloud import storage

# Configuration in .env
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
GCS_BUCKET_NAME=pupilprep-content
```

### Usage Paths
- `content/videos/` - Streaming educational videos
- `content/pdfs/` - Study materials and books
- `submissions/` - Student project submissions
- `assessments/` - Quiz files and answer keys

---

## 3. Google Calendar API

### Purpose
- Manage class schedules
- Create assignment deadlines
- Schedule assessments
- Send reminders to students and teachers

### Implementation Files
- `core/services/calendar.py` - Calendar service integration

### Features
- Sync with Google Calendar
- Automatic reminders
- Recurring events for classes
- Color-coded classes

### Setup
```bash
# Service Account Setup Required
1. Create Service Account in Google Cloud Console
2. Download credentials.json
3. Share calendar with service account email

# Enable APIs
- Google Calendar API
- Google Drive API (for file storage)
```

### Usage
```python
from core.services.calendar import CalendarService

calendar = CalendarService()

# Create class event
calendar.create_event(
    title="Math Class - Algebra",
    description="Chapter 5: Quadratic Equations",
    start_time="2025-01-15T10:00:00",
    end_time="2025-01-15T11:00:00",
    calendar_id="class_calendar_id"
)
```

---

## 4. Google Sheets API

### Purpose
- Store student progress data
- Create class attendance sheets
- Export analytics and reports
- Collaborative grading

### Benefits
- Real-time collaboration
- Easy data visualization
- Integration with Google Analytics
- Automatic backup

### Planned Implementation
```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

service = build('sheets', 'v4', credentials=credentials)

# Create student progress tracking sheet
spreadsheet = service.spreadsheets().create(
    body={
        'properties': {
            'title': 'Class Progress - Grade 10',
            'locale': 'en_US',
        }
    }
).execute()
```

---

## 5. Google Drive API

### Purpose
- Store and manage educational documents
- Create templates for assignments
- Share resources with students
- Backup content

### Features
- File versioning
- Permission management
- Full-text search
- Sharing with individuals/classes

---

## 6. Google Analytics (Frontend)

### Purpose
- Track user engagement
- Monitor learning patterns
- Identify struggling students
- Measure feature adoption

### Implementation
```javascript
// frontend/.env
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX

// Add to layout.tsx
import Script from 'next/script';

<Script
  strategy="afterInteractive"
  src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID}`}
/>
```

---

## 7. Google Cloud Vertex AI (Advanced)

### Purpose
- Custom ML models for student prediction
- Recommendation engine optimization
- Performance forecasting

### Potential Use Cases
- Predict student dropout risk
- Personalize learning paths
- Optimize content sequencing

---

## 8. Google Workspace Integration

### Planned Features
- Single Sign-On (SSO) with Google
- Gmail notifications for grades
- Google Classroom sync
- Google Meet for live tutoring

### Setup
```python
# OAuth 2.0 Configuration
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly']
```

---

## API Keys & Credentials Setup

### 1. Gemini API Key
```bash
# Get from: https://ai.google.dev
# Add to .env:
GEMINI_API_KEY=your_key_here
```

### 2. Google Cloud Service Account
```bash
# Create in Google Cloud Console
# Download JSON credentials
# Add to project root: credentials.json

# Add to .env:
GOOGLE_CLOUD_PROJECT=your_project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### 3. OAuth 2.0 Credentials (for user authentication)
```bash
# Download from Google Cloud Console
# client_id and client_secret
# Redirect URIs: http://localhost:3000/api/auth/google/callback
```

---

## Implemented Endpoints

### Content Generation
```
POST /api/v1/contentGenerationForAHS
- Uses Gemini 2.5 Flash
- Generates personalized learning content
- Supports multiple learning modes
```

### Assessment Generation
```
POST /api/v1/assessments/generate
- Creates adaptive assessments
- Difficulty scaling
- Multi-format questions
```

### Remedial Content
```
POST /api/v1/remedy/generate
- Targeted learning for gaps
- Prerequisite content
- Progressive difficulty
```

---

## Best Practices

1. **API Key Security**
   - Never commit keys to repository
   - Use environment variables
   - Rotate keys regularly
   - Use service accounts for backend

2. **Cost Optimization**
   - Use Gemini Flash for most tasks
   - Batch requests when possible
   - Cache responses
   - Monitor API usage

3. **Rate Limiting**
   - Implement exponential backoff
   - Queue long-running requests
   - Use job queue system

4. **Error Handling**
   - Graceful fallbacks
   - Retry logic
   - User-friendly error messages
   - Logging and monitoring

---

## Future Enhancements

1. **Google Bard/Gemini Chat UI**
   - Direct chat with AI tutor
   - Context-aware responses

2. **Google Cloud BigQuery**
   - Analyze learning patterns
   - Predictive analytics

3. **Google Cloud Natural Language**
   - Sentiment analysis of student feedback
   - Automated essay grading

4. **Google Cloud Vision**
   - Handwritten work recognition
   - Document scanning

5. **Google Cloud Translation**
   - Multi-language support
   - Real-time translation

---

## Troubleshooting

### Common Issues

**API Key Not Found**
```python
ERROR: GEMINI_API_KEY not found. Using mock client for testing.
→ Solution: Set GEMINI_API_KEY in .env file
```

**Calendar Service Initialization Failed**
```python
WARNING: Could not initialize calendar service
→ Solution: Place credentials.json in project root and grant permissions
```

**Rate Limit Exceeded**
```python
429: Too Many Requests
→ Solution: Implement exponential backoff and request queuing
```

---

## Testing

### Unit Tests
```bash
cd tests/
pytest test_gemini_integration.py -v
pytest test_google_calendar.py -v
pytest test_gcs_integration.py -v
```

### Integration Tests
```bash
pytest integration/test_content_generation.py -v
pytest integration/test_assessment_generation.py -v
```

---

## References

- [Google Gemini API Docs](https://ai.google.dev/)
- [Google Cloud Storage Docs](https://cloud.google.com/storage/docs)
- [Google Calendar API Docs](https://developers.google.com/calendar)
- [Google Sheets API Docs](https://developers.google.com/sheets)
- [LangChain + Google Integration](https://python.langchain.com/docs/integrations/providers/google/)

