import re
import time
from googleapiclient.discovery import build
import google.generativeai as genai_
from youtube_transcript_api import YouTubeTranscriptApi
#import google.generativeai as genai
import google.generativeai as genai
from google.cloud import storage
import os
import googleapiclient.errors
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Resolve and set GOOGLE_APPLICATION_CREDENTIALS to an absolute path if present/available
default_sa_path = r"services/ai/helper/dulcet-legend-465615-i5-8d0c54600847.json"
sa_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', default_sa_path)
try:
    if not os.path.isabs(sa_path):
        sa_path_abs = os.path.abspath(sa_path)
    else:
        sa_path_abs = sa_path
    if os.path.exists(sa_path_abs):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = sa_path_abs
    else:
        print(f"[⚠️ GCS Auth] Service account file not found at {sa_path_abs}. Set GOOGLE_APPLICATION_CREDENTIALS.")
except Exception as _e:
    print(f"[⚠️ GCS Auth] Failed to resolve service account path: {str(_e)}")

bucket_name = os.environ.get('BUCKET_NAME', 'pratik-1103')
output_prefix_base = os.environ.get('OUTPUT_PREFIX_BASE', 'vision_output')
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "").split(",")


def gemini_generate(prompt):
    response = model.generate_content(prompt)
    return response.text.strip()

genai_.configure(api_key=GEMINI_API_KEY)
model = genai_.GenerativeModel("gemini-2.5-flash")

class YouTubeAPIKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0
    def get_key(self):
        return self.keys[self.index]
    def rotate_key(self):
        self.index = (self.index + 1) % len(self.keys)
        print(f"[🔁 Switching to API key #{self.index + 1}]")
        return self.get_key()

# Initialize these lazily when functions are called
key_manager = None
youtube = None

def _get_youtube_client():
    global key_manager, youtube
    if key_manager is None:
        key_manager = YouTubeAPIKeyManager(YOUTUBE_API_KEY)
    if youtube is None:
        api_key = key_manager.get_key()
        youtube = build('youtube', 'v3', developerKey=api_key)
    return youtube, key_manager

def search_youtube_videos(query, max_results=10):
    youtube_client, _ = _get_youtube_client()
    request = youtube_client.search().list(
        part="snippet",
        q=query,
        type="video",
        videoDuration="short",
        relevanceLanguage="en",
        maxResults=max_results
    )
    response = request.execute()
    return response.get("items", [])

def get_video_details(video_id):
    youtube_client, _ = _get_youtube_client()
    request = youtube_client.videos().list(
        part="snippet,contentDetails",
        id=video_id
    )
    response = request.execute()
    items = response.get("items", [])
    if not items:
        return None
    return items[0]

def iso8601_duration_to_seconds(duration):
    import isodate
    try:
        parsed_duration = isodate.parse_duration(duration)
        return parsed_duration.total_seconds()
    except Exception:
        return None

def search_youtube_video(description, grade, number, lesson_context):
    # 1️⃣ Generate better search query via Gemini
    refine_prompt = f"""
You are an AI search assistant generating YouTube search queries for school students.

Context:
- Grade: {grade}
- Learning objective: {description}
- Audience: school students of grade {grade}
- Language: English
- Video length: under 5 minutes
- Take context of the video suggestions so make sure the videos are found accordingly: {lesson_context}
- Prefer highly visual, animated, and concept-clearing videos.

ONLY output the search query:
"""
    refined_query = gemini_generate(refine_prompt)
    print(f"🔎 Refined Search Query: `{refined_query}`")
    
    for _ in range(len(YOUTUBE_API_KEY)):
        try:
            search_results = search_youtube_videos(refined_query)
            break
        except googleapiclient.errors.HttpError as e:
            print(f"⚠️ API Error during search: {e}")
            # Reset the global clients to force re-initialization with new key
            global key_manager, youtube
            key_manager = None
            youtube = None
            _get_youtube_client()  # Re-initialize with rotated key
    else:
        print("❌ All API keys exhausted during search.")
        return None
    for item in search_results:
        video_id = item['id']['videoId']
        title = item['snippet']['title']
        desc_snippet = item['snippet'].get('description', "")
        print(f"\n🎯 Candidate: {title}")
        details = get_video_details(video_id)
        if not details:
            print("⚠️ Could not fetch details.")
            continue
        duration_str = details['contentDetails']['duration']
        duration_seconds = iso8601_duration_to_seconds(duration_str)
        if duration_seconds is None or duration_seconds > 600 or duration_seconds < 30:
            print("⏳ Skipped: duration invalid.")
            continue
        transcript_text = None
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            try:
                transcript_metadata = transcript_list.find_transcript(['en'])
                transcript = transcript_metadata.fetch()
                transcript_text = " ".join([entry['text'] for entry in transcript])
                print("📄 English transcript found.")
            except Exception:
                print("🚫 No English transcript available.")
        except Exception as e:
            print(f"🚫 Transcript list error: {str(e)}")
        if transcript_text:
            relevance_prompt = f"""
You are evaluating a YouTube video for grade {grade} students.

Video title: {title}
Description: {desc_snippet}
Transcript: {transcript_text}

Decide if this video is:
- In English
- Educational and helpful for school students
- Explains concept visually or with animations
- Duration under 5 mins

Reply ONLY Yes or No:
"""
        else:
            relevance_prompt = f"""
You are evaluating a YouTube video for grade {grade} students.

Video title: {title}
Description: {desc_snippet}

Transcript not available.

Decide if this video is:
- In English
- Educational and helpful for school students
- Likely explains concept visually or with animations
- Duration under 5 mins

If unsure, lean towards Yes based on title/description.

Reply ONLY Yes or No:
"""
        relevance = gemini_generate(relevance_prompt)
        print(f"🤖 Gemini Relevance: {relevance}")
        if "Yes" in relevance:
            print(f"✅ Selected video: {title} - https://www.youtube.com/watch?v={video_id}")
            return f"https://www.youtube.com/watch?v={video_id}"
        time.sleep(1)
    print("❌ No relevant video found.")
    return None

def search_image(grade, query: str, bucket_name: str,lesson_context) -> str | None:
    """
    Generates a visually descriptive, age-appropriate image for a Grade 10 topic,
    uploads it directly to GCS, and returns the public URL.
    """

    # Step 1: Rephrase query using Gemini Pro
    try:
        genai_.configure(api_key=GEMINI_API_KEY)
        text_model = genai_.GenerativeModel("gemini-2.0-flash")
        prompt = f"""You are an AI prompt engineer for Imagen 3.0 generating **educational images** for Grade {grade} students.

This is the textbook lesson context: {lesson_context}

Your task is to generate a **purely visual scene description** of the concept: "{query}"

Strict rules:
- DO NOT include any text, title, label, or words inside the image.(Strict Requirements)
- DO NOT mention any text in your prompt.
- Focus entirely on objects, diagrams, processes, structures, or scenes that visually explain the topic.
- Describe spatial layout clearly, but using only physical objects and shapes.
- Avoid humans, people, faces, animals, or any decorative elements.
- Avoid artistic interpretations. Keep it scientific, educational, and highly clear for school students.
- The output must be exactly one simple sentence describing what to draw visually.

Example format:
"A diagram showing a plant cell with its organelles clearly separated and colored for easy understanding."

Now generate the scene description:
"""
        improved_prompt = text_model.generate_content(prompt).text.strip()
        print(f"[🧠 Rephrased Prompt] {improved_prompt}")
    except Exception as e:
        print(f"[Gemini Text Error] {e}")
        improved_prompt = query

    # Step 2: Generate image with Imagen 3.0
    try:
        
        MODEL_ID = "imagen-3.0-generate-002"
        client = genai.Client(api_key=GEMINI_API_KEY)
        result = client.models.generate_images(
            model=MODEL_ID,
            prompt=improved_prompt,
            config=dict(
                number_of_images=1,
                output_mime_type="image/jpeg",
                person_generation="DONT_ALLOW",
                aspect_ratio="4:3"
            )
        )
        image = result.generated_images[0].image
        local_path = "generated_image.jpg"
        image.save(local_path)
        print("[✅ Image generated]")
    except Exception as e:
        print(f"[Image Generation Error] {e}")
        return None

    # Step 3: Upload to GCS and return URL
    try:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob_name = f"images/{int(time.time())}.jpg"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)
        blob.make_public()
        url = blob.public_url
        print(f"[📤 Uploaded] {url}")
        return url
    except Exception as e:
        print(f"[Upload Error] {e}")
        return None

def parse_media_suggestions_from_string(media_suggestions_str: str) -> list:
    entries = []
    current_period = None
    for line in media_suggestions_str.splitlines():
        line = line.strip()
        inline_match = re.match(r'\*Period\s+(\d+):\s+Media Type\s+\((Image|Video)\):\s+(.+)', line)
        if inline_match:
            period = inline_match.group(1)
            media_type = inline_match.group(2)
            description = inline_match.group(3)
            entries.append({
                'period': period,
                'media_type': media_type,
                'description': description
            })
            continue
        period_match = re.match(r'\*\*Period\s+(\d+):\*\*', line)
        if period_match:
            current_period = period_match.group(1)
            continue
        media_match = re.match(r'\*\s+Media Type\s+\((Image|Video)\):\s+(.+)', line)
        if media_match and current_period:
            media_type = media_match.group(1)
            description = media_match.group(2)
            entries.append({
                'period': current_period,
                'media_type': media_type,
                'description': description
            })
    return entries

def update_script_with_media_in_memory(grade, script: str, media_entries: list, youtube_key: str,  chapter, subject, lesson_context) -> list:
    pattern = re.compile(r'(?P<header>^####Period\s*:?\s*(\d+)####\s*)(?P<content>.*?)(?=^####Period\s*:?\s*\d+####|\Z)', re.MULTILINE | re.DOTALL)
    periods = []
    
    matches = list(pattern.finditer(script))
    if not matches:
        return [{"script": script, "learning_outcomes": []}]

    for match in matches:
        header, number, content = match.group('header'), match.group(2).strip(), match.group('content')
        media_notes = ''
        for entry in filter(lambda e: e['period'] == number, media_entries):
            media_type, desc = entry['media_type'].lower(), entry['description']
            print(media_type)
            link = search_youtube_video(desc, grade, number=number, lesson_context=lesson_context) if media_type == 'video' else search_image(grade, desc, bucket_name, lesson_context)
            media_notes += f"\n[Media Suggestion]\nType: {media_type.capitalize()}\nDescription: {desc}\nLink: {link or 'No media found'}\n"
        
        period_script = header + media_notes + content
        periods.append({'script': period_script.strip(), "learning_outcomes": []})

    return periods

def teleprompt_with_media(grade, chapter, subject, teleprompt_script, media_suggestions, lesson_context):
    media_entries = parse_media_suggestions_from_string(media_suggestions)
    # Pass lesson_context to update_script_with_media_in_memory
    updated_periods = update_script_with_media_in_memory(grade, teleprompt_script, media_entries, YOUTUBE_API_KEY, chapter, subject, lesson_context=lesson_context)
    print(f"✅ Updated script with media generated in-memory.")
    return updated_periods

