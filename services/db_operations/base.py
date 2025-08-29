import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Debug: Print connection URL (remove in production)
print(f"MONGO_URI: {MONGO_URI}")

# First client for other parts of the app
client = MongoClient(MONGO_URI)
flashcard_db = client["flashcard_game"]
user_collection = flashcard_db["users"]

teacher_timeline_db = client['teacher_timeline']
timetable_events_collection = teacher_timeline_db["timetable_events"]
lessons_collection = teacher_timeline_db["lessons"]

# Second client for all Timetable features
try:
    client2 = MongoClient(MONGO_URI)
    # Test the connection
    client2.admin.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    raise

# IMPORTANT: Atlas already has DB named 'Pupil_teach' (capital P). Using a different
# case (e.g., 'pupil_teach' from the URI) causes a case-conflict error (code 13297).
# To avoid this, always select the existing 'Pupil_teach' database explicitly.
pupil_tree_db = client2['Pupil_teach']
print(f"Using database: {pupil_tree_db.name}")

# Alias for old imports
db = pupil_tree_db

# Collections
pdf_timetable_collection = pupil_tree_db["pdf_timetable"]
timetable_collection = pupil_tree_db["timetable"]
lessons_collection = pupil_tree_db["lessons"]
institutions_collection = pupil_tree_db["institutions"]
teacher_class_data_collection = pupil_tree_db["teacher_class_data"]
sessions_collection = pupil_tree_db["sessions"]
student_reports_collection = pupil_tree_db["student_reports"]
question_bank_collection = pupil_tree_db["question_bank"]
jobs_collection = pupil_tree_db["jobs"]

# Test read: list first 3 documents from timetable
# try:
#     sample_docs = list(timetable_collection.find().limit(3))
#     print(f"Sample timetable documents: {sample_docs}")
# except Exception as e:
#     print(f"Error reading from timetable collection: {e}")
