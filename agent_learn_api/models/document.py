from agent_learn_api import db

class Document(db.Model):
    __tablename__ = "documents"
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, server_default = db.func.now())
    
    workspace_id = db.Column(db.Integer, db.ForeignKey("workspaces.id"), nullable=False)