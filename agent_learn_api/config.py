class Config:
    SECRET_KEY = "<your-key>"  
    SQLALCHEMY_DATABASE_URI = "<your-key>"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "<your-key>"
    MAIL_PASSWORD = "<your-key>"

    FRONTEND_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
