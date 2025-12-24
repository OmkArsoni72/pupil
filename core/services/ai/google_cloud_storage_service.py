"""
Google Cloud Storage Integration for PupilPrep
Handles storage of educational content, student submissions, and media files
"""

import os
import io
from typing import Optional, BinaryIO, List
from google.cloud import storage
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'pupilprep-content')


class GoogleCloudStorageService:
    """Service for managing files in Google Cloud Storage"""
    
    def __init__(self):
        """Initialize GCS service"""
        self.client = None
        self.bucket = None
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize Google Cloud Storage client"""
        try:
            if os.path.exists(SERVICE_ACCOUNT_FILE):
                credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
                project_id = credentials.project_id
                self.client = storage.Client(credentials=credentials, project=project_id)
                
                # Get or create bucket
                try:
                    self.bucket = self.client.bucket(GCS_BUCKET_NAME)
                    if not self.bucket.exists():
                        self.bucket = self.client.create_bucket(GCS_BUCKET_NAME)
                        print(f"✓ Created GCS bucket: {GCS_BUCKET_NAME}")
                    else:
                        print(f"✓ Connected to GCS bucket: {GCS_BUCKET_NAME}")
                except Exception as e:
                    print(f"⚠ Could not access/create bucket: {e}")
            else:
                print(f"⚠ Service account file not found at {SERVICE_ACCOUNT_FILE}")
                print("  Google Cloud Storage features will be disabled")
        
        except Exception as e:
            print(f"✗ Failed to initialize GCS service: {e}")
    
    def upload_file(self, file_path: str, blob_name: str) -> Optional[str]:
        """
        Upload a file to GCS
        
        Args:
            file_path: Local path to file
            blob_name: Path in GCS bucket (e.g., 'content/videos/lesson1.mp4')
        
        Returns:
            Public URL if successful, None otherwise
        """
        if not self.bucket:
            print("GCS service not initialized")
            return None
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(file_path)
            
            # Make public if it's content
            if 'content/' in blob_name or 'public/' in blob_name:
                blob.make_public()
                print(f"✓ Uploaded to GCS: {blob_name}")
                return blob.public_url
            
            print(f"✓ Uploaded to GCS: {blob_name}")
            return f"gs://{GCS_BUCKET_NAME}/{blob_name}"
        
        except Exception as e:
            print(f"✗ Failed to upload file: {e}")
            return None
    
    def upload_from_memory(
        self, 
        file_content: BinaryIO, 
        blob_name: str, 
        content_type: str = None
    ) -> Optional[str]:
        """
        Upload a file from memory to GCS
        
        Args:
            file_content: File content as bytes
            blob_name: Path in GCS bucket
            content_type: MIME type (e.g., 'image/jpeg')
        
        Returns:
            Public URL if successful
        """
        if not self.bucket:
            return None
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(file_content, content_type=content_type)
            
            if 'content/' in blob_name or 'public/' in blob_name:
                blob.make_public()
            
            print(f"✓ Uploaded to GCS: {blob_name}")
            return blob.public_url if blob.public_url else f"gs://{GCS_BUCKET_NAME}/{blob_name}"
        
        except Exception as e:
            print(f"✗ Failed to upload from memory: {e}")
            return None
    
    def download_file(self, blob_name: str, local_path: str) -> bool:
        """
        Download a file from GCS
        
        Args:
            blob_name: Path in GCS bucket
            local_path: Local path to save file
        
        Returns:
            True if successful
        """
        if not self.bucket:
            return False
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.download_to_filename(local_path)
            print(f"✓ Downloaded from GCS: {blob_name}")
            return True
        
        except Exception as e:
            print(f"✗ Failed to download file: {e}")
            return False
    
    def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from GCS
        
        Args:
            blob_name: Path in GCS bucket
        
        Returns:
            True if successful
        """
        if not self.bucket:
            return False
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            print(f"✓ Deleted from GCS: {blob_name}")
            return True
        
        except Exception as e:
            print(f"✗ Failed to delete file: {e}")
            return False
    
    def list_files(self, prefix: str = '') -> Optional[List[str]]:
        """
        List files in GCS bucket
        
        Args:
            prefix: Filter by prefix (e.g., 'content/videos/')
        
        Returns:
            List of file paths
        """
        if not self.bucket:
            return None
        
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            file_list = [blob.name for blob in blobs]
            print(f"✓ Listed {len(file_list)} files with prefix: {prefix}")
            return file_list
        
        except Exception as e:
            print(f"✗ Failed to list files: {e}")
            return None
    
    def get_file_url(self, blob_name: str, signed: bool = False, expiration_hours: int = 1) -> Optional[str]:
        """
        Get URL for a file
        
        Args:
            blob_name: Path in GCS bucket
            signed: Whether to generate signed URL (for private files)
            expiration_hours: Hours until signed URL expires
        
        Returns:
            File URL
        """
        if not self.bucket:
            return None
        
        try:
            blob = self.bucket.blob(blob_name)
            
            if signed:
                from datetime import timedelta
                url = blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(hours=expiration_hours),
                    method="GET"
                )
                return url
            else:
                # Try public URL
                if blob.public_url:
                    return blob.public_url
                return f"gs://{GCS_BUCKET_NAME}/{blob_name}"
        
        except Exception as e:
            print(f"✗ Failed to get file URL: {e}")
            return None
    
    def create_folder_structure(self) -> bool:
        """Create standard folder structure in GCS"""
        if not self.bucket:
            return False
        
        try:
            folders = [
                'content/videos/',
                'content/pdfs/',
                'content/images/',
                'submissions/assignments/',
                'submissions/projects/',
                'assessments/quizzes/',
                'assessments/exams/',
                'student-work/',
                'media/thumbnails/',
                'backups/',
            ]
            
            for folder in folders:
                blob = self.bucket.blob(folder)
                blob.upload_from_string('')
                print(f"✓ Created folder: {folder}")
            
            return True
        
        except Exception as e:
            print(f"✗ Failed to create folder structure: {e}")
            return False
    
    def upload_learning_content(
        self, 
        file_path: str, 
        subject: str, 
        topic: str, 
        file_type: str
    ) -> Optional[str]:
        """
        Upload learning content with organized structure
        
        Args:
            file_path: Local file path
            subject: Subject name (e.g., 'Mathematics')
            topic: Topic name (e.g., 'Algebra')
            file_type: Type of content ('video', 'pdf', 'image')
        
        Returns:
            File URL if successful
        """
        if not self.bucket:
            return None
        
        try:
            file_name = os.path.basename(file_path)
            blob_name = f"content/{file_type}s/{subject}/{topic}/{file_name}"
            
            return self.upload_file(file_path, blob_name)
        
        except Exception as e:
            print(f"✗ Failed to upload learning content: {e}")
            return None
    
    def upload_student_submission(
        self, 
        file_path: str, 
        student_id: str, 
        assignment_id: str
    ) -> Optional[str]:
        """
        Upload student assignment submission
        
        Args:
            file_path: Local file path
            student_id: Student's ID
            assignment_id: Assignment ID
        
        Returns:
            File path in GCS if successful
        """
        if not self.bucket:
            return None
        
        try:
            file_name = os.path.basename(file_path)
            blob_name = f"submissions/assignments/{student_id}/{assignment_id}/{file_name}"
            
            self.upload_file(file_path, blob_name)
            return blob_name
        
        except Exception as e:
            print(f"✗ Failed to upload student submission: {e}")
            return None
    
    def get_bucket_stats(self) -> Optional[dict]:
        """Get storage statistics for the bucket"""
        if not self.bucket:
            return None
        
        try:
            blobs = self.bucket.list_blobs()
            total_size = sum(blob.size for blob in blobs)
            total_files = sum(1 for _ in self.bucket.list_blobs())
            
            stats = {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_gb': total_size / (1024 ** 3),
                'bucket_name': self.bucket.name,
            }
            
            print(f"✓ Bucket stats: {total_files} files, {stats['total_size_gb']:.2f} GB")
            return stats
        
        except Exception as e:
            print(f"✗ Failed to get bucket stats: {e}")
            return None


# Initialize service instance
gcs_service = GoogleCloudStorageService()
