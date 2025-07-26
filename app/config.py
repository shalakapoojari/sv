import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")

    # ✅ Secure session cookie config for production
    SESSION_COOKIE_SECURE = False            # Required on HTTPS (PythonAnywhere)
    SESSION_COOKIE_SAMESITE = 'Lax'         # Ensures fetch/keepalive works

    # MySQL for PythonAnywhere
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'Shalaka@25'
    MYSQL_DB = 'employee_portal'

    # Debugging email and key loading (for verification)
    print("Loaded MAIL_USERNAME:", os.getenv("MAIL_USERNAME"))
    print("Loaded SECRET_KEY:", os.getenv("SECRET_KEY"))

    # Email
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "sventerprise01@gmail.com"
    MAIL_PASSWORD = "webl yztc yvjo sipj"

    # Uploads
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'uploads')
