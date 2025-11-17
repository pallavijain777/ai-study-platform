from agent_learn_api import db
from sqlalchemy import Column, Integer, ForeignKey, String

class AIDoc(db.Model):
    __tablename__ = "aidocs"
    
    id = Column(Integer, primary_key=True)
    file_name = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)
    
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)      
     