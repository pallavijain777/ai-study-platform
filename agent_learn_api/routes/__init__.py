# agent_learn_api/routes/__init__.py

from agent_learn_api.routes.auth import auth_bp
from agent_learn_api.routes.chat import chat_bp
from agent_learn_api.routes.document import document_bp
from agent_learn_api.routes.workspace import workspace_bp
from agent_learn_api.routes.quiz import quiz_bp
from agent_learn_api.routes.question import question_bp

__all__ = [
    "auth_bp",
    "chat_bp",
    "document_bp",
    "workspace_bp",
    "quiz_bp",
    "question_bp",
]
