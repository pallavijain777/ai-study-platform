from agent_learn_api import db

class VerificationCode(db.Model):
    __tablename__ = "verification_codes"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)