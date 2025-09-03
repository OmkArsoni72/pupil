from pydantic import BaseModel
from typing import List, Optional

# Models for After-Hour Session Content
class AfterHourText(BaseModel):
    contentId: str
    title: str
    source: str
    content: str

class AfterHourVideo(BaseModel):
    contentId: str
    title: str
    source: str
    url: str
    durationInSeconds: int

class AfterHourGame(BaseModel):
    contentId: str
    title: str
    type: str
    url: str
    estimatedPlayTimeInMinutes: int

class AfterHourPracticeQuestions(BaseModel):
    setId: str
    title: str
    numberOfQuestions: int
    questionIds: List[str]

class AfterHourAssessmentQuestions(BaseModel):
    assessmentId: str
    title: str
    numberOfQuestions: int
    timeLimitInMinutes: int
    questionIds: List[str]

class AfterHourSession(BaseModel):
    texts: List[AfterHourText]
    videos: List[AfterHourVideo]
    games: List[AfterHourGame]
    practiceQuestions: AfterHourPracticeQuestions
    assessmentQuestions: AfterHourAssessmentQuestions

# Model for Lesson Script
class LessonScript(BaseModel):
    scriptId: str
    creationMethod: str
    estimatedReadingTimeInMinutes: int
    scriptContent: str

# Model for In-Class Questions
class InClassQuestions(BaseModel):
    setId: str
    title: str
    numberOfQuestions: int
    creationMethod: str
    timeAssignedInMinutes: int
    questionIds: List[str] 