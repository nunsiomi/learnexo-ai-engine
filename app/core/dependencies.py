from app.services.learning_style_service import LearningStyleService

def get_learning_style_service() -> LearningStyleService:
    return LearningStyleService()