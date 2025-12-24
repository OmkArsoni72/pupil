# Google Services Setup Guide for PupilPrep

## Quick Start (5 minutes)

### 1. Get Gemini API Key

```bash
# Visit: https://ai.google.dev   
# Click "Get API Key" 
# Create new API key in Google AI Studio
# Copy and paste below:

# In your .env file or terminal:
export GEMINI_API_KEY="your_api_key_here"
```

### 2. Install Required Packages

```bash
# Python packages already in requirements.txt:
pip install google-generativeai==0.8.5
pip install google-cloud-storage==2.14.0
pip install google-auth==2.40.3
pip install google-api-python-client==2.178.0

# Or install all:
pip install -r requirements.txt
```

### 3. Set Up Google Cloud Project (for Storage, Sheets, Calendar)

#### Step 1: Create Google Cloud Project
```bash
# Visit: https://console.cloud.google.com
# Click "Select a Project" → "NEW PROJECT"
# Name: "PupilPrep"
# Click "Create"
```

#### Step 2: Enable Required APIs
```bash
# In Google Cloud Console, enable:
1. Gemini API (already done with API key)
2. Cloud Storage API
3. Sheets API
4. Drive API  
5. Calendar API

# Search each and click "ENABLE"
```

#### Step 3: Create Service Account
```bash
# In Google Cloud Console:
1. Go to "Service Accounts"
2. Click "Create Service Account"
3. Name: "pupilprep-service"
4. Grant roles:
   - Editor (for testing)
   - Cloud Storage Admin
   - Sheets Editor
5. Click "Create Key" → JSON
6. Download and save as `credentials.json` in project root
```

#### Step 4: Create Storage Bucket
```bash
# In Google Cloud Console:
1. Go to Cloud Storage → Buckets
2. Click "CREATE BUCKET"
3. Name: "pupilprep-content" (must be globally unique)
4. Location: closest to your users
5. Default settings → Create

# Add to .env:
export GCS_BUCKET_NAME="pupilprep-content"
export GOOGLE_APPLICATION_CREDENTIALS="./credentials.json"
```

### 4. Test Installation

```bash
# Test Gemini
python -c "
from core.services.ai.llm_client import LLMFactory
factory = LLMFactory()
client = factory.get_client()
response = client.chat('Say hello!')
print(response)
"

# Test GCS
python -c "
from core.services.ai.google_cloud_storage_service import gcs_service
print('✓ GCS initialized:', gcs_service.bucket is not None)
"

# Test Sheets
python -c "
from core.services.ai.google_sheets_service import sheets_service
print('✓ Sheets initialized:', sheets_service.service is not None)
"
```

---

## Usage Examples

### Generate a Lesson and Store

```python
from core.services.ai.google_integration_examples import generate_and_store_lesson

lesson = generate_and_store_lesson(
    subject="Physics",
    topic="Newton's Laws",
    grade_level=9
)

print(f"Lesson URL: {lesson['gcs_url']}")
```

### Create Class Gradebook

```python
from core.services.ai.google_integration_examples import setup_class_management

class_setup = setup_class_management(
    class_name="Grade 10 Physics",
    students=["Alice", "Bob", "Carol", "David"]
)

print(f"Gradebook: {class_setup['services']['gradebook']['url']}")
print(f"Attendance: {class_setup['services']['attendance']['url']}")
```

### Generate Assessment

```python
from core.services.ai.google_integration_examples import create_and_schedule_assessment
from datetime import datetime, timedelta

assessment = create_and_schedule_assessment(
    class_name="Grade 10 Physics",
    topic="Newton's Laws",
    difficulty="medium",
    num_questions=15,
    due_date=datetime.now() + timedelta(days=3)
)

print(f"Assessment: {assessment['gcs_url']}")
```

### Track Student Progress

```python
from core.services.ai.google_integration_examples import create_student_progress_dashboard

sheet_id = create_student_progress_dashboard(
    student_id="STU001",
    student_name="Alice Kumar"
)

print(f"Progress Sheet: https://docs.google.com/spreadsheets/d/{sheet_id}")
```

---

## Environment Variables

Add to your `.env` file:

```bash
# Gemini API
GEMINI_API_KEY=your_api_key_here

# Google Cloud
GOOGLE_CLOUD_PROJECT=pupilprep-2025
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
GCS_BUCKET_NAME=pupilprep-content

# Frontend
NEXT_PUBLIC_GEMINI_API_KEY=your_api_key_here
NEXT_PUBLIC_API_URL=http://localhost:8080
```

---

## Folder Structure in GCS

Your bucket will have this structure:

```
pupilprep-content/
├── content/
│   ├── videos/
│   │   └── [Subject]/
│   │       └── [Topic]/
│   ├── pdfs/
│   │   └── [Subject]/
│   │       └── [Topic]/
│   └── images/
├── submissions/
│   ├── assignments/
│   │   └── [StudentID]/
│   │       └── [AssignmentID]/
│   └── projects/
├── assessments/
│   ├── quizzes/
│   └── exams/
├── student-work/
├── media/
│   └── thumbnails/
└── backups/
```

---

## Cost Estimation

### Gemini API
- **Free**: 15 requests/minute
- **Paid**: ~$0.075 per 1M input tokens, $0.30 per 1M output tokens
- **Estimated**: $5-15/month for typical classroom use

### Google Cloud Storage
- **Storage**: $0.020 per GB/month
- **Data Transfer**: Free within Google Cloud
- **Operations**: ~$0.004 per 10k writes
- **Estimated**: $1-5/month for typical usage

### Google Sheets API
- **Free**: 500 requests/100 seconds
- **No charges** for Sheet creation/updates (quota-based only)

### Google Calendar API
- **Free**: 50M quota/day
- **No charges** for standard usage

**Total Monthly Cost**: $6-20 for a classroom of 30 students

---

## Troubleshooting

### "GEMINI_API_KEY not found"
```python
# Solution: Set environment variable
import os
os.environ['GEMINI_API_KEY'] = 'your_key_here'
```

### "Could not initialize calendar service"
```python
# Solution: Place credentials.json in project root
# Or set GOOGLE_APPLICATION_CREDENTIALS environment variable
export GOOGLE_APPLICATION_CREDENTIALS="./credentials.json"
```

### "Bucket does not exist"
```python
# Solution: Create bucket in Google Cloud Console
# Or let the service auto-create it:
GCS_BUCKET_NAME=new-bucket-name
```

### "Permission denied" for Sheets
```python
# Solution: Share sheet with service account email
# Found in credentials.json: "client_email"
# Share with Editor role
```

---

## Security Best Practices

1. ✅ **Never commit credentials.json to git**
   ```bash
   # Add to .gitignore:
   credentials.json
   .env
   *.env.local
   ```

2. ✅ **Use environment variables for keys**
   ```python
   api_key = os.getenv('GEMINI_API_KEY')
   ```

3. ✅ **Rotate service account keys regularly**
   - Every 90 days in production

4. ✅ **Use signed URLs for private content**
   ```python
   url = gcs_service.get_file_url(
       'submissions/...',
       signed=True,
       expiration_hours=1
   )
   ```

5. ✅ **Limit service account permissions**
   - Only grant necessary roles
   - Use custom IAM roles for fine-grained control

---

## Next Steps

1. **Generate Content**
   ```bash
   python -m core.services.ai.google_integration_examples
   ```

2. **Integrate with Backend Routes**
   - Create `/api/v1/content/generate` endpoint
   - Integrate with agents

3. **Frontend Integration**
   - Fetch content from GCS
   - Display student dashboards

4. **Scale Up**
   - Monitor costs and quotas
   - Implement caching
   - Queue long-running jobs

---

## Support & Resources

- [Google Gemini Docs](https://ai.google.dev/docs)
- [GCS Python Client](https://cloud.google.com/python/docs/reference/storage/latest)
- [Google Sheets API Guide](https://developers.google.com/sheets/api/guides/concepts)
- [Google Cloud Console](https://console.cloud.google.com)

---

**Status**: ✅ Complete implementation ready for production use!
