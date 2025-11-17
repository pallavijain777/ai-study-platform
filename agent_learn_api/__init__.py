from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_cors import CORS
from flask_socketio import SocketIO

db = SQLAlchemy()
bcrypt = Bcrypt()
mail = Mail()
socket_io = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config.from_object("agent_learn_api.config.Config")

    # ✅ Correct CORS setup
    CORS(
        app,
        origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    socket_io.init_app(app)

    # Import blueprints
    from agent_learn_api.routes.auth import auth_bp
    from agent_learn_api.routes.chat import chat_bp
    from agent_learn_api.routes.document import document_bp
    from agent_learn_api.routes.workspace import workspace_bp
    from agent_learn_api.routes.quiz import quiz_bp
    from agent_learn_api.routes.question import question_bp
    from agent_learn_api.routes.mindmap import mindmap_bp
    from agent_learn_api.routes.ai_doc import ai_doc_bp

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(document_bp, url_prefix="/documents")
    app.register_blueprint(workspace_bp, url_prefix="/workspaces")
    app.register_blueprint(quiz_bp, url_prefix="/quizzes")
    app.register_blueprint(question_bp, url_prefix="/questions")
    app.register_blueprint(mindmap_bp, url_prefix="/mindmaps")
    app.register_blueprint(ai_doc_bp, url_prefix="/aidocs")

    return app
