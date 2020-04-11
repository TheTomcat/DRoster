from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_httpauth import HTTPBasicAuth
from passlib.context import CryptContext
from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
bootstrap = Bootstrap(app)
login.login_view = 'login'
app_name = "DRoster"
auth = HTTPBasicAuth()
mail = Mail(app)
#CORS(app)
pwd_context = CryptContext(schemes=["pbkdf2_sha512"])

from app import routes, models