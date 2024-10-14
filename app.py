from flask import Flask
from flask_mongoengine import MongoEngine
from scraper import TwitterScraper
from keras.src.saving import load_model
import pickle
import spacy



app = Flask(__name__)
app.secret_key = '3604e1243eaa6e0147364162a6ab29900efb056d538e6534da5d5a3d75b420f2'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Ou 'Lax' selon votre besoin
app.config['SESSION_COOKIE_SECURE'] = True  # Nécessaire si SameSite=None

# Configuration MongoDB avec MongoEngine
app.config['MONGODB_SETTINGS'] = {
    'db': 'app_data',
    'host': 'localhost',
    'port': 27017
}

# Configuration MongoEngine
db = MongoEngine(app)

# Load your pre-trained model at the start of your application
model = load_model('best_model_french.keras')
with open('tokenizer_french.pkl', 'rb') as file:
    tokenizer = pickle.load(file)
# Charger le modèle français
nlp = spacy.load('fr_core_news_sm')

# Initialize TwitterScraper
credentials_file = 'credentials.json'
scraper = TwitterScraper(credentials_file)
scraper.login()

from routes import *

if __name__ == '__main__':
    app.run()
