from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.post("/createContentForAfterhours")
def create_content_for_afterhours():
    """
    Create mock content for afterhours
    """
    return {
        "status": "success",
        "data": {
            "content": "This is mock content for afterhours activities. Students can engage in various extracurricular activities including sports, arts, and academic clubs.",
            "timestamp": datetime.now().isoformat()
        }
    }


@router.post("/createContentForRemedies")
def create_content_for_remedies():
    """
    Create mock content for remedies
    """
    return {
        "status": "success",
        "data": {
            "content": "This is mock content for remedies. Here are some study tips and academic support resources for students who need additional help.",
            "timestamp": datetime.now().isoformat()
        }
    }
