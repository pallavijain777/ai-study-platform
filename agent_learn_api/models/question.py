from agent_learn_api import db

class Question(db.Model):
    __tablename__ = "questions"
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=True)
    correct_answer = db.Column(db.Text, nullable=True)
    order_index = db.Column(db.Integer, nullable=True)
    
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    created_for = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    