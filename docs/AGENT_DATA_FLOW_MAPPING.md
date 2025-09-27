# Agent Data Flow Mapping Guide

## 🎯 Overview

This guide provides a detailed mapping of how each agent interacts with database collections, what data they read/write, and where this happens in the codebase. It's designed to help new developers understand the agent-specific data flow and storage patterns.

## 🤖 Agent-Specific Data Flow

### 1. **Assessment Agent**

#### **Primary Collections Used**

- **`templates`** - Assessment templates and schemas
- **`assessments`** - Generated assessments metadata
- **`question_bank`** - Question repository
- **`jobs`** - Job tracking

#### **Data Flow Details**

##### **Input Data (What Agent Reads)**

```python
# From templates collection
{
    "target_exam": "CBSE_Grade10_Physics_Monthly",
    "metadata": {
        "board": "CBSE",
        "grade": 10,
        "subject": "Physics",
        "exam_type": "monthly",
        "duration_minutes": 90,
        "total_marks": 100
    },
    "scheme": {
        "answer_types": {"MCQ": ["A", "B", "C", "D"]},
        "question_formats": ["multiple_choice", "integer"],
        "sections": [{
            "name": "Section A",
            "marks_per_question": {"single_correct": 1},
            "difficulty_distribution_percent": {"easy": 30, "medium": 50, "hard": 20}
        }]
    }
}
```

##### **Output Data (What Agent Writes)**

```python
# To assessments collection
{
    "job_id": "JOB_ASSESSMENT_abc123",
    "status": "completed",
    "question_ids": ["q1", "q2", "q3"],
    "request_params": {
        "target_exam": "CBSE_Grade10_Physics_Monthly",
        "difficulty": "medium",
        "subject": "Physics"
    },
    "created_at": "2024-01-15T10:30:00Z"
}
```

##### **Key Files and Nodes**

- **File**: `core/agents/assessment_agent.py`
- **File**: `core/graphs/assessment_graph.py`
- **File**: `core/services/ai/assessment_generator.py`
- **Node**: `assessment_node` in `core/nodes/assessment_nodes/assessment_node.py`
- **Node**: `schema_node` in `core/nodes/common_nodes/schema_node.py`
- **Node**: `question_generation_node` in `core/nodes/common_nodes/question_generation_node.py`

##### **Database Operations**

```python
# Reading template
template = await templates_collection.find_one({
    "target_exam": request.target_exam
})

# Writing assessment
await assessments_collection.insert_one({
    "job_id": job_id,
    "status": "pending",
    "question_ids": [],
    "request_params": request.dict()
})

# Updating question bank
await question_bank_collection.update_many(
    {"_id": {"$in": question_ids}},
    {"$push": {"usageHistory": {"setId": job_id, "setType": "assessment", "dateUsed": datetime.now()}}}
)
```

---

### 2. **Content Agent (AHS - After Hour Session)**

#### **Primary Collections Used**

- **`sessions`** - Class session data with generated content
- **`teacher_class_data`** - Teacher-class relationships and curriculum
- **`student_reports`** - Student performance for context
- **`lesson_script`** - Curriculum structure
- **`jobs`** - Job tracking

#### **Data Flow Details**

##### **Input Data (What Agent Reads)**

```python
# From sessions collection
{
    "teacherClassDataId": "class_123",
    "chapterId": "ch_456",
    "lessonNumber": 1,
    "sessionTitle": "Introduction to Physics",
    "learningOutcomes": ["Understand basic concepts", "Apply formulas"],
    "inClassQuestions": {
        "mcqs": [{"question": "What is force?", "options": ["A", "B", "C", "D"], "answer": "A"}]
    }
}

# From teacher_class_data collection
{
    "className": "10A",
    "subject": "Physics",
    "curriculum": {
        "chapters": [{
            "chapterId": "ch_456",
            "title": "Mechanics",
            "status": "active"
        }]
    }
}

# From student_reports collection (for context)
{
    "studentId": "student_789",
    "report": {
        "inclass_report": [{
            "chapterName": "Mechanics",
            "score": "85%",
            "learning_gaps": "Understanding of vectors"
        }]
    }
}
```

##### **Output Data (What Agent Writes)**

```python
# To sessions collection (afterHourSession field)
{
    "afterHourSession": {
        "texts": [{
            "title": "Vector Addition Explained",
            "url": "https://example.com/vector-addition"
        }],
        "videos": [{
            "title": "Physics Concepts Video",
            "url": "https://youtube.com/watch?v=abc123"
        }],
        "games": [{
            "title": "Physics Quiz Game",
            "url": "https://game.example.com/physics-quiz"
        }],
        "practiceQuestions": {
            "questions": [{
                "question": "Calculate the resultant force",
                "options": ["A", "B", "C", "D"],
                "answer": "B"
            }]
        },
        "assessmentQuestions": {
            "questions": [{
                "question": "Explain Newton's laws",
                "answerGuide": "Focus on the three laws and their applications",
                "questionType": "descriptive"
            }]
        },
        "status": "generated"
    }
}
```

##### **Key Files and Nodes**

- **File**: `core/agents/content_agent.py`
- **File**: `core/graphs/content_graph.py`
- **File**: `core/services/ai/content_graph.py`
- **Node**: `orchestrator_node` in `core/nodes/content_nodes/orchestrator_node.py`
- **Node**: `collector_node` in `core/nodes/content_nodes/collector_node.py`
- **Learning Mode Nodes**: `reading_node`, `watching_node`, `solving_node`, etc.

##### **Database Operations**

```python
# Reading session data
session = await sessions_collection.find_one({
    "_id": ObjectId(session_id)
})

# Reading teacher class data
teacher_class = await teacher_class_data_collection.find_one({
    "classId": teacher_class_id
})

# Reading student reports for context
student_reports = await student_reports_collection.find({
    "classId": class_id
}).to_list(length=10)

# Writing generated content
await sessions_collection.update_one(
    {"_id": ObjectId(session_id)},
    {"$set": {"afterHourSession": generated_content}}
)
```

---

### 3. **Remedy Agent**

#### **Primary Collections Used**

- **`remedy_plans`** - Remediation plans and gap analysis
- **`student_reports`** - Student performance gaps
- **`prerequisite_cache`** - Cached prerequisite discoveries
- **`remediation_logs`** - Logs of remediation activities
- **`jobs`** - Job tracking

#### **Data Flow Details**

##### **Input Data (What Agent Reads)**

```python
# From student_reports collection
{
    "studentId": "student_789",
    "report": {
        "inclass_report": [{
            "learning_gaps": "Difficulty with vector operations",
            "score": "60%"
        }],
        "assessment_report": [{
            "learning_gaps": "Cannot solve problems involving force calculations"
        }]
    }
}

# From prerequisite_cache collection
{
    "gap_code": "VECTOR_OPERATIONS",
    "prerequisites": [{
        "topic": "Basic Algebra",
        "grade_level": "9",
        "priority": 1,
        "description": "Understanding of algebraic operations"
    }]
}
```

##### **Output Data (What Agent Writes)**

```python
# To remedy_plans collection
{
    "remedy_id": "remedy_123",
    "student_id": "student_789",
    "teacher_class_id": "class_123",
    "classified_gaps": [{
        "code": "VECTOR_OPERATIONS",
        "evidence": ["Cannot add vectors", "Confuses direction"]
    }],
    "remediation_plans": [{
        "gap_type": "conceptual_gap",
        "selected_modes": ["reading", "watching", "solving"],
        "content_specifications": {
            "reading": {"topics": ["Vector basics", "Vector addition"]},
            "watching": {"videos": ["Vector operations tutorial"]},
            "solving": {"problems": ["Basic vector addition", "Vector subtraction"]}
        },
        "priority": 1,
        "estimated_duration_minutes": 30
    }],
    "context_refs": {
        "lesson_script_id": "script_456",
        "recent_session_ids": ["session_789"]
    },
    "prerequisite_discoveries": {
        "VECTOR_OPERATIONS": [{
            "topic": "Basic Algebra",
            "grade_level": "9",
            "priority": 1
        }]
    },
    "status": "completed",
    "content_job_ids": ["job_abc", "job_def"]
}

# To remediation_logs collection
{
    "plan_id": "plan_123",
    "student_id": "student_789",
    "gap_type": "conceptual_gap",
    "cycle": 1,
    "result": {
        "success": True,
        "improvement": "15%",
        "time_spent": "25 minutes"
    },
    "created_at": "2024-01-15T11:00:00Z"
}
```

##### **Key Files and Nodes**

- **File**: `core/agents/remedy_agent.py`
- **File**: `core/graphs/remedy_graph.py`
- **File**: `core/services/ai/remedy_graph.py`
- **Node**: `gap_classifier_node` in `core/graphs/remedy_graph.py`
- **Node**: `strategy_planner_node` in `core/graphs/remedy_graph.py`
- **Node**: `prerequisite_discovery_node` in `core/graphs/remedy_graph.py`
- **Node**: `content_agent_integration_node` in `core/graphs/remedy_graph.py`

##### **Database Operations**

```python
# Reading student reports for gap analysis
student_report = await student_reports_collection.find_one({
    "studentId": student_id,
    "classId": class_id
})

# Reading prerequisite cache
prerequisites = await prerequisite_cache_collection.find_one({
    "gap_code": gap_code,
    "grade_level": grade_level
})

# Writing remedy plan
await remedy_plans_collection.insert_one({
    "remedy_id": remedy_id,
    "student_id": student_id,
    "classified_gaps": classified_gaps,
    "remediation_plans": plans,
    "status": "pending"
})

# Logging remediation activity
await remediation_logs_collection.insert_one({
    "plan_id": plan_id,
    "student_id": student_id,
    "gap_type": gap_type,
    "result": result
})
```

---

### 4. **RAG System (NCERT Integration)**

#### **Primary Collections Used**

- **`prerequisite_cache`** - Cached prerequisite discoveries
- **`remediation_logs`** - Logs of remediation activities
- **External**: Pinecone vector database

#### **Data Flow Details**

##### **Input Data (What RAG Reads)**

```python
# From prerequisite_cache collection
{
    "gap_code": "ALGEBRA_BASICS",
    "grade_level": "10",
    "subject": "Mathematics",
    "prerequisites": [{
        "topic": "Basic Arithmetic",
        "grade_level": "8",
        "priority": 1,
        "description": "Addition, subtraction, multiplication, division"
    }]
}

# From Pinecone (vector search)
{
    "query": "What are the prerequisites for learning algebra?",
    "top_k": 8,
    "citations": [{
        "text": "Before learning algebra, students should understand...",
        "source": "NCERT Grade 8 Mathematics",
        "page": 45
    }]
}
```

##### **Output Data (What RAG Writes)**

```python
# To prerequisite_cache collection
{
    "gap_code": "ALGEBRA_BASICS",
    "grade_level": "10",
    "subject": "Mathematics",
    "prerequisites": [{
        "topic": "Basic Arithmetic",
        "grade_level": "8",
        "priority": 1,
        "description": "Addition, subtraction, multiplication, division",
        "learning_objectives": ["Perform basic operations", "Solve word problems"],
        "success_rate": 0.85,
        "source": "NCERT Grade 8"
    }],
    "created_at": "2024-01-15T12:00:00Z",
    "expires_at": "2024-01-22T12:00:00Z"
}
```

##### **Key Files and Nodes**

- **File**: `core/services/ai/rag_integration.py`
- **File**: `core/services/ai/enhanced_rag_integration.py`
- **File**: `core/services/ai/pinecone_client.py`
- **File**: `core/services/ai/ncert_ingest.py`
- **File**: `core/services/ai/floor_wise_prerequisite_discovery.py`

##### **Database Operations**

```python
# Reading from cache
cached_result = await prerequisite_cache_collection.find_one({
    "gap_code": gap_code,
    "grade_level": grade_level,
    "expires_at": {"$gt": datetime.now()}
})

# Writing to cache
await prerequisite_cache_collection.insert_one({
    "gap_code": gap_code,
    "grade_level": grade_level,
    "prerequisites": prerequisites,
    "expires_at": datetime.now() + timedelta(days=7)
})

# Pinecone vector operations
results = await pinecone_client.query(
    index_name="ncert-index",
    query_vector=embedding,
    top_k=8
)
```

---

## 🔄 Cross-Agent Data Flow

### **Content Agent → Remedy Agent**

```python
# Content Agent generates content based on Remedy Agent's plans
remedy_plan = await remedy_plans_collection.find_one({
    "remedy_id": remedy_id
})

# Content Agent uses the plan to generate specific content
content_specifications = remedy_plan["remediation_plans"][0]["content_specifications"]
```

### **Assessment Agent → Content Agent**

```python
# Assessment Agent generates questions that Content Agent can use
assessment_questions = await question_bank_collection.find({
    "setId": assessment_id
}).to_list(length=10)

# Content Agent incorporates these questions into AHS content
```

### **RAG System → All Agents**

```python
# All agents can use RAG for prerequisite discovery
prerequisites = await prerequisite_cache_collection.find_one({
    "gap_code": gap_code
})
```

---

## 📊 Data Storage Patterns

### **Session-Based Storage**

- **Collection**: `sessions`
- **Pattern**: Each session stores generated content
- **Agents**: Content Agent, Assessment Agent

### **Job-Based Storage**

- **Collection**: `jobs`
- **Pattern**: Background job tracking
- **Agents**: All agents

### **Plan-Based Storage**

- **Collection**: `remedy_plans`
- **Pattern**: Remediation plans and gap analysis
- **Agents**: Remedy Agent

### **Cache-Based Storage**

- **Collection**: `prerequisite_cache`
- **Pattern**: Cached discoveries for performance
- **Agents**: RAG System, Remedy Agent

---

## 🛠️ Development Guidelines

### **When Adding New Agent Features**

1. **Identify Required Collections**: Determine which collections your agent needs
2. **Define Data Flow**: Map input → processing → output
3. **Create Database Operations**: Write async functions for read/write operations
4. **Add Error Handling**: Handle database connection issues
5. **Test Data Flow**: Verify data is stored and retrieved correctly

### **Common Patterns**

```python
# Reading with error handling
async def get_student_data(student_id: str):
    try:
        student = await student_reports_collection.find_one({
            "studentId": student_id
        })
        if not student:
            raise HTTPException(404, "Student not found")
        return student
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(500, "Database error")

# Writing with validation
async def save_remedy_plan(plan_data: dict):
    try:
        # Validate data structure
        if not plan_data.get("student_id"):
            raise ValueError("student_id is required")

        result = await remedy_plans_collection.insert_one(plan_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Failed to save remedy plan: {e}")
        raise HTTPException(500, "Failed to save plan")
```

---

## 🔍 Quick Reference

| Agent             | Primary Collections                                     | Key Operations                    | Main Files                                   |
| ----------------- | ------------------------------------------------------- | --------------------------------- | -------------------------------------------- |
| **Assessment**    | `templates`, `assessments`, `question_bank`             | Read templates, Write assessments | `assessment_agent.py`, `assessment_graph.py` |
| **Content (AHS)** | `sessions`, `teacher_class_data`, `student_reports`     | Read context, Write content       | `content_agent.py`, `content_graph.py`       |
| **Remedy**        | `remedy_plans`, `student_reports`, `prerequisite_cache` | Read gaps, Write plans            | `remedy_agent.py`, `remedy_graph.py`         |
| **RAG**           | `prerequisite_cache`, Pinecone                          | Read/write cache, Vector search   | `rag_integration.py`, `pinecone_client.py`   |

This mapping should help you understand exactly how each agent interacts with the database and what data flows through the system.
