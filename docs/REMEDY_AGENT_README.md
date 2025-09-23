# Remedy Agent Implementation

## Overview

The Remedy Agent is an internal planning layer that sits between the Reports Agent and Content Agent in the PupilTree system. It takes classified learning gaps and generates targeted remediation plans with specific learning mode sequences and content specifications. The Remedy Agent is accessed through the existing `contentGenerationForRemedies` route, not as a separate service.

## Architecture

```
Reports Agent → contentGenerationForRemedies → Remedy Agent → Content Agent
     ↓                    ↓                        ↓              ↓
Classified           API Route              Remediation    Learning
   Gaps                                   Plans        Content
```

**Key Point**: Remedy Agent is an internal component, not a separate API service.

## Key Components

### 1. Remedy Graph (`services/ai/remedy_graph.py`)

- **Gap Classifier Node**: Classifies gaps into 6 types (knowledge, conceptual, application, foundational, retention, engagement)
- **Strategy Planner Node**: Generates remediation plans with mode sequences
- **Prerequisite Discovery Node**: Uses RAG to find prerequisites for foundational gaps
- **Content Integration Node**: Passes plans to Content Agent
- **Finalizer Node**: Prepares final output

### 2. Integrated Remedy Runner (`services/ai/integrated_remedy_runner.py`)

- Orchestrates Remedy Agent → Content Agent flow
- Manages integrated job execution and status tracking
- Handles database operations for remedy plans

### 3. Updated Content Routes (`routes/content.py`)

- `POST /v1/contentGenerationForRemedies`: Create remediation content (uses Remedy Agent internally)
- `GET /v1/jobs/{job_id}`: Get job status (handles both AHS and Remedy jobs)
- `GET /v1/remedyJobs/{job_id}/plans`: Get generated remediation plans
- `GET /v1/remedyJobs/{job_id}/content`: Get final content from Content Agent

### 4. Database Operations (`services/db_operations/remedy_db.py`)

- Store and retrieve remedy plans
- Track completion status
- Manage prerequisite discoveries

### 5. RAG Integration (`services/ai/rag_integration.py`)

- Prerequisite discovery for foundational gaps
- Learning path generation
- Fallback mechanisms

## Gap Types and Strategies

| Gap Type         | Definition                       | Learning Mode Sequence                    |
| ---------------- | -------------------------------- | ----------------------------------------- |
| **Knowledge**    | Missing basic facts/information  | Reading → Watching → Assessment           |
| **Conceptual**   | Can't understand relationships   | Questioning & Debating → Doing → Reading  |
| **Application**  | Can't apply concepts to problems | Solving → Playing → Doing                 |
| **Foundational** | Missing prerequisite knowledge   | Reading → Watching → RAG Discovery        |
| **Retention**    | Previously learned but forgotten | Reading (refreshers) → Solving → Playing  |
| **Engagement**   | Lack of motivation/interest      | Playing → Listening & Speaking → Watching |

## API Usage

### Create Remediation Content

```bash
POST /api/v1/v1/contentGenerationForRemedies
Content-Type: application/json

{
  "student_id": "student_123",
  "teacher_class_id": "class_456",
  "classified_gaps": [
    {
      "code": "algebra_basic_equations",
      "evidence": ["Cannot solve simple linear equations", "Confuses variables with numbers"]
    }
  ],
  "context_refs": {
    "grade_level": "grade_7",
    "subject": "mathematics"
  }
}
```

### Response

```json
{
  "job_id": "REMEDY_abc123",
  "status": "pending",
  "progress": 0
}
```

### Get Remediation Plans

```bash
GET /api/v1/remedyJobs/REMEDY_abc123/plans
```

### Response

```json
{
  "job_id": "REMEDY_abc123",
  "status": "completed",
  "remedy_plans": [
    {
      "gap_type": "conceptual",
      "selected_modes": [
        "learn_by_questioning_debating",
        "learn_by_doing",
        "learn_by_reading"
      ],
      "content_specifications": {
        "gap_code": "algebra_basic_equations",
        "gap_evidence": ["Cannot solve simple linear equations"],
        "focus": "understanding_relationships",
        "include_visualizations": true,
        "assessment_focus": "analysis"
      },
      "priority": 1,
      "estimated_duration_minutes": 15
    }
  ],
  "content_job_ids": ["CONTENT_conceptual_xyz789"]
}
```

## Integration with Content Agent

The Remedy Agent generates remediation plans that are passed to the Content Agent as specifications. The Content Agent then generates the actual learning content using its 10-node graph.

### Key Changes from Previous Architecture

1. **No more top-level modes array**: Modes are now determined by the Remedy Agent based on gap type (modes field is optional in API)
2. **Gap-specific content specifications**: Each plan includes detailed specifications for content generation
3. **Prerequisite handling**: Foundational gaps trigger RAG-based prerequisite discovery
4. **Assessment integration**: Plans include assessment strategies for gap verification

## Database Schema

### Remedy Plans Collection

```json
{
  "_id": "remedy_plan_id",
  "student_id": "student_123",
  "teacher_class_id": "class_456",
  "classified_gaps": [...],
  "remediation_plans": [...],
  "context_refs": {...},
  "status": "completed",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z",
  "content_job_ids": ["CONTENT_job_1", "CONTENT_job_2"],
  "completion_status": {
    "total_plans": 2,
    "completed_plans": 2,
    "failed_plans": 0
  }
}
```

## Testing

Run the test script to verify the integrated implementation:

```bash
python test_integrated_remedy.py
```

This will test:

- Remedy Agent integration
- Integrated Remedy Agent → Content Agent flow
- API flow simulation
- Gap classification logic
- Remediation plan generation
- RAG integration (simulated)

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Required for LLM operations
- `MONGO_URI`: MongoDB connection string

### Gap Classification Keywords

The system uses keyword-based classification. Keywords can be customized in `services/ai/remedy_graph.py`:

```python
GAP_TYPE_KEYWORDS = {
    "knowledge": ["basic", "fact", "term", "definition", ...],
    "conceptual": ["concept", "principle", "theory", ...],
    # ... etc
}
```

## Future Enhancements

1. **Real RAG Integration**: Replace simulated RAG with actual vector database queries
2. **Machine Learning Classification**: Use ML models for more accurate gap classification
3. **Adaptive Strategies**: Learn from successful remediation patterns
4. **Multi-language Support**: Extend to support multiple languages
5. **Advanced Analytics**: Track remediation effectiveness and optimize strategies

## Error Handling

The system includes comprehensive error handling:

- **Fallback Classification**: If RAG fails, uses rule-based fallbacks
- **Graceful Degradation**: Continues processing even if some components fail
- **Detailed Logging**: Extensive logging for debugging and monitoring
- **Status Tracking**: Real-time job status updates

## Performance Considerations

- **Parallel Processing**: Multiple remediation plans can be processed concurrently
- **Caching**: Prerequisite discoveries can be cached for similar gaps
- **Resource Management**: LLM calls are optimized and batched where possible
- **Database Indexing**: Proper indexing on student_id, teacher_class_id, and status fields
