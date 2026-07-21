from app.services.learning_style_service import LearningStyleService
from app.services.learning_path_service import LearningPathService
from app.services.content_service import ContentService


def get_learning_style_service() -> LearningStyleService:
    return LearningStyleService()


def get_learning_path_service() -> LearningPathService:
    return LearningPathService()


def get_content_service() -> ContentService:
    return ContentService()
