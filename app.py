from flask import Flask
from flask_mongoengine import MongoEngine
from scraper import TwitterScraper

app = Flask(__name__)
app.secret_key = '3604e1243eaa6e0147364162a6ab29900efb056d538e6534da5d5a3d75b420f2'

# Configuration MongoDB avec MongoEngine
app.config['MONGODB_SETTINGS'] = {
    'db': 'app_data',
    'host': 'localhost',
    'port': 27017
}

# Configuration MongoEngine
db = MongoEngine(app)

# Initialize TwitterScraper
credentials_file = 'credentials.json'
scraper = TwitterScraper(credentials_file)
scraper.login()

from routes import *

if __name__ == '__main__':
    app.run()
