"""
Google Services Integration Examples for PupilPrep

This file demonstrates how to use Google Gemini, Google Sheets, 
Google Cloud Storage, and Google Calendar together.
"""

from core.services.ai.llm_client import LLMFactory
from core.services.ai.google_sheets_service import sheets_service
from core.services.ai.google_cloud_storage_service import gcs_service
from core.services.calendar import CalendarService
from datetime import datetime, timedelta
import json


# ============================================================================
# Example 1: Generate Content and Store in GCS
# ============================================================================

def generate_and_store_lesson(
    subject: str,
    topic: str,
    grade_level: int,
    learning_format: str = 'markdown'
) -> dict:
    """
    Generate a lesson using Gemini and store it in Google Cloud Storage
    
    Args:
        subject: Subject name (e.g., 'Mathematics')
        topic: Topic name (e.g., 'Quadratic Equations')
        grade_level: Grade level (9-12)
        learning_format: Format for content ('markdown', 'html', 'pdf')
    
    Returns:
        Dictionary with content URL and metadata
    """
    print(f"\n📚 Generating {subject} lesson on {topic}...")
    
    # Step 1: Generate content using Gemini
    llm_factory = LLMFactory()
    gemini_client = llm_factory.get_client("gemini_2.5_flash")
    
    prompt = f"""
    Create a comprehensive learning material for {subject} - {topic} for Grade {grade_level}.
    
    Include:
    1. Learning Objectives (3-5 key goals)
    2. Key Concepts (main ideas to understand)
    3. Detailed Explanation (with examples)
    4. Real-world Applications
    5. Common Misconceptions
    6. Practice Problems (5 progressive difficulty levels)
    
    Format as clear markdown with proper headings and structure.
    """
    
    content = gemini_client.chat(prompt)
    print(f"✓ Generated content ({len(content)} characters)")
    
    # Step 2: Save to temporary file
    temp_file = f"/tmp/{subject}_{topic}.md"
    with open(temp_file, 'w') as f:
        f.write(content)
    
    # Step 3: Upload to Google Cloud Storage
    gcs_path = f"content/lessons/{subject}/{topic}/{topic}_lesson.md"
    gcs_url = gcs_service.upload_file(temp_file, gcs_path)
    
    # Step 4: Create metadata
    metadata = {
        'subject': subject,
        'topic': topic,
        'grade_level': grade_level,
        'created_at': datetime.now().isoformat(),
        'content_type': 'lesson',
        'gcs_path': gcs_path,
        'gcs_url': gcs_url,
        'word_count': len(content.split()),
    }
    
    print(f"✓ Stored at: {gcs_path}")
    print(f"✓ Public URL: {gcs_url}")
    
    return metadata


# ============================================================================
# Example 2: Create Gradebook and Track Assignments
# ============================================================================

def setup_class_management(class_name: str, students: list) -> dict:
    """
    Set up complete class management system
    - Create gradebook in Google Sheets
    - Create attendance tracker
    - Create progress tracking
    - Set up GCS folders for assignments
    
    Args:
        class_name: Name of the class (e.g., 'Grade 10 - Section A')
        students: List of student names
    
    Returns:
        Dictionary with all service IDs and URLs
    """
    print(f"\n📊 Setting up class management for {class_name}...")
    
    result = {
        'class_name': class_name,
        'students': students,
        'created_at': datetime.now().isoformat(),
        'services': {}
    }
    
    # Step 1: Create gradebook
    print("Creating gradebook...")
    gradebook_id = sheets_service.create_class_gradebook(class_name, students)
    if gradebook_id:
        result['services']['gradebook'] = {
            'id': gradebook_id,
            'url': f"https://docs.google.com/spreadsheets/d/{gradebook_id}/edit"
        }
    
    # Step 2: Create attendance sheet
    print("Creating attendance tracker...")
    attendance_id = sheets_service.create_attendance_sheet(class_name, students)
    if attendance_id:
        result['services']['attendance'] = {
            'id': attendance_id,
            'url': f"https://docs.google.com/spreadsheets/d/{attendance_id}/edit"
        }
    
    # Step 3: Create GCS folder structure
    print("Creating storage folders...")
    gcs_service.create_folder_structure()
    result['services']['storage'] = {
        'bucket': 'pupilprep-content',
        'class_folder': f"content/{class_name.replace(' ', '_')}/"
    }
    
    # Step 4: Share gradebook with teachers (example)
    teacher_email = "teacher@school.com"
    sheets_service.share_sheet(gradebook_id, teacher_email, role='writer')
    
    print(f"✓ Class setup complete!")
    return result


# ============================================================================
# Example 3: Generate Assessment and Schedule It
# ============================================================================

def create_and_schedule_assessment(
    class_name: str,
    topic: str,
    difficulty: str = 'medium',
    num_questions: int = 10,
    due_date: datetime = None
) -> dict:
    """
    Generate an assessment using Gemini and schedule it with Google Calendar
    
    Args:
        class_name: Class name
        topic: Assessment topic
        difficulty: 'easy', 'medium', or 'hard'
        num_questions: Number of questions
        due_date: When the assessment is due
    
    Returns:
        Assessment details
    """
    if not due_date:
        due_date = datetime.now() + timedelta(days=3)
    
    print(f"\n📝 Creating assessment on {topic}...")
    
    # Step 1: Generate assessment using Gemini
    llm_factory = LLMFactory()
    gemini_client = llm_factory.get_client("gemini_2.5_flash")
    
    prompt = f"""
    Create a {difficulty} assessment on {topic} with {num_questions} questions.
    
    Include:
    - Mix of question types (MCQ, short answer, essay)
    - Answer key with explanations
    - Difficulty progression
    - Time estimate
    
    Format as JSON with clear structure.
    """
    
    assessment_content = gemini_client.chat(prompt)
    print(f"✓ Generated assessment with {num_questions} questions")
    
    # Step 2: Store assessment in GCS
    assessment_file = f"/tmp/assessment_{topic}.json"
    with open(assessment_file, 'w') as f:
        f.write(assessment_content)
    
    gcs_path = f"assessments/{class_name.replace(' ', '_')}/{topic}_assessment.json"
    gcs_url = gcs_service.upload_file(assessment_file, gcs_path)
    
    # Step 3: Schedule in Google Calendar
    calendar_service = CalendarService()
    calendar_service.create_event(
        title=f"Assessment: {topic}",
        description=f"Assessment for class {class_name}. Access here: {gcs_url}",
        start_time=due_date.isoformat(),
        end_time=(due_date + timedelta(hours=1)).isoformat(),
        calendar_id=class_name
    )
    
    print(f"✓ Assessment scheduled for {due_date.date()}")
    
    result = {
        'topic': topic,
        'class': class_name,
        'num_questions': num_questions,
        'difficulty': difficulty,
        'due_date': due_date.isoformat(),
        'gcs_path': gcs_path,
        'gcs_url': gcs_url,
    }
    
    return result


# ============================================================================
# Example 4: Student Progress Tracking Dashboard
# ============================================================================

def create_student_progress_dashboard(student_id: str, student_name: str) -> str:
    """
    Create a comprehensive progress tracking sheet for a student
    
    Args:
        student_id: Student's unique ID
        student_name: Student's name
    
    Returns:
        Spreadsheet ID
    """
    print(f"\n📈 Creating progress dashboard for {student_name}...")
    
    # Create Google Sheet for progress tracking
    progress_sheet_id = sheets_service.create_progress_tracking_sheet(
        student_id, 
        student_name
    )
    
    if not progress_sheet_id:
        print("✗ Failed to create progress sheet")
        return None
    
    # Share with student and parents
    student_email = f"{student_id}@school.com"
    sheets_service.share_sheet(progress_sheet_id, student_email, role='reader')
    
    parent_email = f"{student_id}_parent@school.com"
    sheets_service.share_sheet(progress_sheet_id, parent_email, role='reader')
    
    print(f"✓ Progress dashboard created and shared")
    print(f"  Link: https://docs.google.com/spreadsheets/d/{progress_sheet_id}/edit")
    
    return progress_sheet_id


# ============================================================================
# Example 5: Personalized Learning Path Generation
# ============================================================================

def generate_personalized_learning_path(
    student_name: str,
    current_level: str,
    target_level: str,
    learning_preferences: list,
    time_available_hours: int = 5
) -> dict:
    """
    Generate a personalized learning path using Gemini
    and create a detailed plan in Google Sheets
    
    Args:
        student_name: Student's name
        current_level: Current proficiency level
        target_level: Target proficiency level
        learning_preferences: List of preferred learning modes
        time_available_hours: Weekly hours available
    
    Returns:
        Learning path details
    """
    print(f"\n🎯 Generating learning path for {student_name}...")
    
    # Step 1: Generate path using Gemini
    llm_factory = LLMFactory()
    gemini_client = llm_factory.get_client("gemini_2.5_flash")
    
    prompt = f"""
    Create a detailed learning path for a student:
    - Name: {student_name}
    - Current Level: {current_level}
    - Target Level: {target_level}
    - Preferred Learning Modes: {', '.join(learning_preferences)}
    - Available Hours/Week: {time_available_hours}
    
    Generate:
    1. Week-by-week breakdown (8 weeks)
    2. Daily tasks
    3. Resources needed
    4. Checkpoints and assessments
    5. Estimated completion timeline
    
    Format as structured JSON.
    """
    
    learning_path = gemini_client.chat(prompt)
    print(f"✓ Generated personalized learning path")
    
    # Step 2: Create Google Sheet for tracking
    sheet_id = sheets_service.create_progress_tracking_sheet(
        f"student_{id(learning_path)}",
        f"{student_name}'s Learning Path"
    )
    
    result = {
        'student': student_name,
        'current_level': current_level,
        'target_level': target_level,
        'learning_modes': learning_preferences,
        'weekly_hours': time_available_hours,
        'learning_path': json.loads(learning_path),
        'tracking_sheet_id': sheet_id,
        'tracking_sheet_url': f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    }
    
    return result


# ============================================================================
# Example 6: Content Recommendation Engine
# ============================================================================

def generate_content_recommendations(
    student_id: str,
    student_performance: dict,
    learning_style: str
) -> list:
    """
    Generate personalized content recommendations using Gemini
    and retrieve from GCS
    
    Args:
        student_id: Student's ID
        student_performance: Dict with subject scores
        learning_style: 'visual', 'auditory', 'kinesthetic', 'reading-writing'
    
    Returns:
        List of recommended content with links
    """
    print(f"\n💡 Generating recommendations...")
    
    # Step 1: Analyze performance and generate recommendations
    llm_factory = LLMFactory()
    gemini_client = llm_factory.get_client("gemini_2.5_flash")
    
    weak_subjects = [s for s, score in student_performance.items() if score < 70]
    
    prompt = f"""
    Generate content recommendations for a student:
    - Weak areas: {', '.join(weak_subjects)}
    - Learning style: {learning_style}
    
    Recommend:
    1. Top 3 topics to focus on
    2. Recommended learning resources
    3. Practice materials
    4. Assessment suggestions
    
    Consider the {learning_style} learning style in recommendations.
    Format as JSON.
    """
    
    recommendations = gemini_client.chat(prompt)
    
    # Step 2: Link to actual content in GCS
    recommendations_dict = json.loads(recommendations)
    
    print(f"✓ Generated {len(recommendations_dict.get('recommendations', []))} recommendations")
    
    return recommendations_dict


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    """
    Demonstrate Google Services integration
    """
    
    print("=" * 70)
    print("🚀 Google Services Integration Examples for PupilPrep")
    print("=" * 70)
    
    # Example 1: Generate and store lesson
    lesson_meta = generate_and_store_lesson(
        subject="Mathematics",
        topic="Quadratic Equations",
        grade_level=10,
    )
    
    # Example 2: Setup class management
    students = ["Alice Kumar", "Bob Singh", "Carol Johnson", "David Chen"]
    class_setup = setup_class_management("Grade 10 - Section A", students)
    
    # Example 3: Create assessment
    assessment = create_and_schedule_assessment(
        class_name="Grade 10 - Section A",
        topic="Quadratic Equations",
        difficulty="medium",
        num_questions=10,
        due_date=datetime.now() + timedelta(days=5)
    )
    
    # Example 4: Student progress dashboard
    student_sheet = create_student_progress_dashboard(
        "STU001",
        "Alice Kumar"
    )
    
    # Example 5: Personalized learning path
    path = generate_personalized_learning_path(
        student_name="Alice Kumar",
        current_level="intermediate",
        target_level="advanced",
        learning_preferences=["video", "interactive", "problem-solving"],
        time_available_hours=5
    )
    
    print("\n" + "=" * 70)
    print("✓ All examples completed successfully!")
    print("=" * 70)
