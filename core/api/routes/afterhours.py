from fastapi import APIRouter
from api.controllers.afterhours_controller import AfterhoursController

router = APIRouter()


@router.post("/createContentForAfterhours")
def create_content_for_afterhours():
    """
    Create mock content for afterhours
    """
    return AfterhoursController.create_afterhours_content()


@router.post("/createContentForRemedies")
def create_content_for_remedies():
    """
    Create mock content for remedies
    """
    return AfterhoursController.create_remedies_content()