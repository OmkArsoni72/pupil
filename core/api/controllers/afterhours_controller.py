from datetime import datetime
from typing import Dict, Any


class AfterhoursController:
    """
    Controller for afterhours content operations.
    Handles business logic for afterhours and remedies content generation.
    """

    @staticmethod
    def create_afterhours_content() -> Dict[str, Any]:
        """
        Generate mock content for afterhours activities.
        
        Returns:
            Dict containing status, content data and timestamp
        """
        return {
            "status": "success",
            "data": {
                "content": "This is mock content for afterhours activities. Students can engage in various extracurricular activities including sports, arts, and academic clubs.",
                "timestamp": datetime.now().isoformat()
            }
        }

    @staticmethod
    def create_remedies_content() -> Dict[str, Any]:
        """
        Generate mock content for remedies and academic support.
        
        Returns:
            Dict containing status, content data and timestamp
        """
        return {
            "status": "success",
            "data": {
                "content": "This is mock content for remedies. Here are some study tips and academic support resources for students who need additional help.",
                "timestamp": datetime.now().isoformat()
            }
        }