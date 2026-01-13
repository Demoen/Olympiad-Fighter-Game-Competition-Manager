from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable is not set")
app.config['DEBUG'] = os.getenv("FLASK_DEBUG", "False") == "True"
from game import routes