"""
Base Agent - Common functionality for all agents.
Provides shared utilities and patterns for agent implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid
import logging
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all agents with common functionality."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.created_at = datetime.utcnow()
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main workflow."""
        pass
    
    def generate_job_id(self) -> str:
        """Generate unique job ID."""
        return f"JOB_{self.agent_name.upper()}_{uuid.uuid4().hex[:8]}"
    
    async def log_agent_activity(self, activity: str, details: Dict[str, Any]):
        """Log agent activity."""
        self.logger.info(f"[{self.agent_name}] {activity}: {details}")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "agent_name": self.agent_name,
            "created_at": self.created_at.isoformat(),
            "status": "active"
        }
