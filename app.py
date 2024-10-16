from flask import Flask  # Import de Flask pour créer l'application web
from flask_mongoengine import MongoEngine  # Pour utiliser MongoDB avec MongoEngine
from scraper import TwitterScraper  # Import du scraper Twitter personnalisé
from keras.src.saving import load_model  # Charger un modèle Keras pré-entrainé
import pickle  # Pour charger le tokenizer sérialisé
import spacy  # Pour la NLP avec le modèle spaCy

# === Initialisation de l'application Flask ===
app = Flask(__name__)  # Crée l'application Flask

# === Configuration des cookies de session ===
app.secret_key = '3604e1243eaa6e0147364162a6ab29900efb056d538e6534da5d5a3d75b420f2'  # Clé secrète pour la sécurité
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Politique SameSite (ou 'Lax')
app.config['SESSION_COOKIE_SECURE'] = True  # Rend le cookie accessible uniquement via HTTPS

# === Configuration de la base de données MongoDB ===
app.config['MONGODB_SETTINGS'] = {
    'db': 'app_data',  # Nom de la base de données
    'host': 'localhost',  # Hôte MongoDB (local)
    'port': 27017  # Port MongoDB
}

# === Initialisation de MongoEngine ===
db = MongoEngine(app)  # Connecte l'application à MongoDB via MongoEngine

# === Chargement du modèle Keras pré-entrainé ===
model = load_model('best_model_french.keras')  # Charge le modèle de sentiment

# === Chargement du tokenizer sérialisé avec pickle ===
with open('tokenizer_french.pkl', 'rb') as file:
    tokenizer = pickle.load(file)  # Charge le tokenizer pour transformer le texte

# === Chargement du modèle spaCy pour le traitement NLP ===
nlp = spacy.load('fr_core_news_sm')  # Charge le modèle français de spaCy

# === Initialisation du scraper Twitter ===
credentials_file = 'credentials.json'  # Chemin du fichier de credentials
scraper = TwitterScraper(credentials_file)  # Instancie le scraper
scraper.login()  # Connexion avec les identifiants fournis

# === Importation des routes ===
from routes import *  # Importe toutes les routes définies dans le fichier 'routes.py'

# === Lancement de l'application ===
if __name__ == '__main__':
    app.run()  # Démarre le serveur Flask
