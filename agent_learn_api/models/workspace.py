from agent_learn_api import db

class Workspace(db.Model):
    __tablename__ = "workspaces"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)