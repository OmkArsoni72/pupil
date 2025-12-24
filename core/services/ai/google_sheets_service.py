"""
Google Sheets API Integration for PupilPrep
Manages student progress tracking, attendance, and gradebooks
"""

import os
import json
from typing import List, Dict, Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]

SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')


class GoogleSheetsService:
    """Service for managing Google Sheets integration"""
    
    def __init__(self):
        """Initialize Google Sheets service"""
        self.service = None
        self.drive_service = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Google Sheets and Drive services"""
        try:
            if os.path.exists(SERVICE_ACCOUNT_FILE):
                credentials = Credentials.from_service_account_file(
                    SERVICE_ACCOUNT_FILE, scopes=SCOPES
                )
                self.service = build('sheets', 'v4', credentials=credentials)
                self.drive_service = build('drive', 'v3', credentials=credentials)
                print("✓ Google Sheets service initialized successfully")
            else:
                print(f"⚠ Service account file not found at {SERVICE_ACCOUNT_FILE}")
                print("  Google Sheets features will be disabled")
        except Exception as e:
            print(f"✗ Failed to initialize Google Sheets service: {e}")
    
    def create_class_gradebook(self, class_name: str, students: List[str]) -> Optional[str]:
        """
        Create a gradebook spreadsheet for a class
        
        Args:
            class_name: Name of the class
            students: List of student names
        
        Returns:
            Spreadsheet ID if successful, None otherwise
        """
        if not self.service:
            print("Google Sheets service not initialized")
            return None
        
        try:
            # Create spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': f'{class_name} - Gradebook',
                    'locale': 'en_US',
                }
            }
            
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            spreadsheet_id = spreadsheet['spreadsheetId']
            
            # Add headers and student names
            self._setup_gradebook_sheet(spreadsheet_id, students)
            
            print(f"✓ Created gradebook: {spreadsheet_id}")
            return spreadsheet_id
        
        except HttpError as error:
            print(f"✗ Failed to create gradebook: {error}")
            return None
    
    def _setup_gradebook_sheet(self, spreadsheet_id: str, students: List[str]):
        """Set up gradebook with headers and student names"""
        try:
            # Headers: Name, Email, Subject1, Subject2, Subject3, Average, Status
            headers = ['Student Name', 'Email', 'Math', 'Science', 'English', 'History', 'Average', 'Status']
            
            # Prepare data
            data = [headers]
            for student in students:
                data.append([student, f'{student.lower().replace(" ", ".")}@school.com'] + [''] * 6)
            
            # Update sheet
            body = {
                'values': data
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1:H100',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            # Format headers
            self._format_headers(spreadsheet_id)
            
        except HttpError as error:
            print(f"✗ Failed to setup gradebook sheet: {error}")
    
    def _format_headers(self, spreadsheet_id: str):
        """Format header row with bold text and background color"""
        try:
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True,
                            },
                            'backgroundColor': {
                                'red': 0.25,
                                'green': 0.52,
                                'blue': 0.95,
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)',
                }
            }]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
        
        except HttpError as error:
            print(f"✗ Failed to format headers: {error}")
    
    def add_student_grade(
        self, 
        spreadsheet_id: str, 
        student_name: str, 
        subject: str, 
        grade: float
    ) -> bool:
        """
        Add or update a student's grade
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            student_name: Name of the student
            subject: Subject name
            grade: Grade/score
        
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            return False
        
        try:
            # Get all values to find student row
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A:A'
            ).execute()
            
            values = result.get('values', [])
            student_row = None
            
            for i, row in enumerate(values):
                if row and row[0] == student_name:
                    student_row = i + 1
                    break
            
            if not student_row:
                print(f"Student '{student_name}' not found")
                return False
            
            # Get headers to find subject column
            headers_result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!1:1'
            ).execute()
            
            headers = headers_result.get('values', [[]])[0]
            subject_col = None
            
            for i, header in enumerate(headers):
                if header == subject:
                    subject_col = i
                    break
            
            if subject_col is None:
                print(f"Subject '{subject}' not found in headers")
                return False
            
            # Update the grade
            cell_notation = chr(65 + subject_col) + str(student_row)
            body = {'values': [[grade]]}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'Sheet1!{cell_notation}',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"✓ Updated {student_name}'s {subject} grade to {grade}")
            return True
        
        except HttpError as error:
            print(f"✗ Failed to add grade: {error}")
            return False
    
    def create_attendance_sheet(self, class_name: str, students: List[str]) -> Optional[str]:
        """
        Create an attendance tracking sheet
        
        Args:
            class_name: Name of the class
            students: List of student names
        
        Returns:
            Spreadsheet ID if successful
        """
        if not self.service:
            return None
        
        try:
            spreadsheet_body = {
                'properties': {
                    'title': f'{class_name} - Attendance',
                    'locale': 'en_US',
                }
            }
            
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            spreadsheet_id = spreadsheet['spreadsheetId']
            
            # Setup attendance sheet with dates
            headers = ['Student Name'] + [f'Day {i+1}' for i in range(30)]
            data = [headers]
            
            for student in students:
                data.append([student] + [''] * 30)
            
            body = {'values': data}
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1:AE100',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"✓ Created attendance sheet: {spreadsheet_id}")
            return spreadsheet_id
        
        except HttpError as error:
            print(f"✗ Failed to create attendance sheet: {error}")
            return None
    
    def create_progress_tracking_sheet(self, student_id: str, student_name: str) -> Optional[str]:
        """
        Create a progress tracking sheet for individual student
        
        Args:
            student_id: Student's ID
            student_name: Student's name
        
        Returns:
            Spreadsheet ID if successful
        """
        if not self.service:
            return None
        
        try:
            spreadsheet_body = {
                'properties': {
                    'title': f'{student_name} - Progress Tracking',
                }
            }
            
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            spreadsheet_id = spreadsheet['spreadsheetId']
            
            # Setup progress tracking with metrics
            headers = [
                'Date',
                'Subject',
                'Topic',
                'Score',
                'Time Spent (min)',
                'Completion %',
                'Assessment',
                'Level'
            ]
            
            data = [headers]
            
            body = {'values': data}
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1:H1',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"✓ Created progress sheet for {student_name}: {spreadsheet_id}")
            return spreadsheet_id
        
        except HttpError as error:
            print(f"✗ Failed to create progress sheet: {error}")
            return None
    
    def share_sheet(self, spreadsheet_id: str, email: str, role: str = 'reader') -> bool:
        """
        Share a spreadsheet with a user
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            email: Email to share with
            role: 'reader', 'commenter', or 'writer'
        
        Returns:
            True if successful
        """
        if not self.drive_service:
            return False
        
        try:
            self.drive_service.permissions().create(
                fileId=spreadsheet_id,
                body={
                    'kind': 'drive#permission',
                    'type': 'user',
                    'role': role,
                    'emailAddress': email,
                }
            ).execute()
            
            print(f"✓ Shared spreadsheet with {email} ({role})")
            return True
        
        except HttpError as error:
            print(f"✗ Failed to share spreadsheet: {error}")
            return False
    
    def get_spreadsheet_data(self, spreadsheet_id: str, range_name: str = 'Sheet1!A:Z') -> Optional[List[List]]:
        """
        Get data from a spreadsheet
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            range_name: Range to retrieve (e.g., 'Sheet1!A1:Z100')
        
        Returns:
            List of lists containing the data
        """
        if not self.service:
            return None
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
        
        except HttpError as error:
            print(f"✗ Failed to get spreadsheet data: {error}")
            return None


# Initialize service instance
sheets_service = GoogleSheetsService()
