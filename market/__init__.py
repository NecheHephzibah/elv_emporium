# Import necessary modules
import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from paystackapi.paystack import Paystack

# Initialize Flask application
app = Flask(__name__, static_folder='static')

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set secret key for session management
app.config['SECRET_KEY'] = '8f2d191c390fdb4fd3c7c13105dc5e91ba25c5bd6e9a2c6c'

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Configure Paystack API keys
app.config['PAYSTACK_SECRET_KEY'] = os.environ.get('PAYSTACK_SECRET_KEY', 'sk_test_b9ea25fc47d33cac3542bc25ae63ef415be85782')
app.config['PAYSTACK_PUBLIC_KEY'] = os.environ.get('PAYSTACK_PUBLIC_KEY', 'pk_test_3e90032c631e39cd94623b61bcf7dadafe7ab4a7')

# Initialize Paystack
paystack = Paystack(secret_key=app.config['PAYSTACK_SECRET_KEY'])

# Initialize database
db = SQLAlchemy(app)

# Initialize database migration
migrate = Migrate(app, db)

# Initialize password hashing
bcrypt = Bcrypt(app)

# Configure user session management
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"

# Import routes and models
from market import routes
from market import models