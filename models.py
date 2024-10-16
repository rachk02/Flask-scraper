from mongoengine import DateTimeField
from app import db  # Importation de l'objet `db` depuis l'application Flask
from datetime import datetime  # Pour gérer les dates

# --- Modèle utilisateur (commenté) ---
"""
class User(db.Document, UserMixin):
    meta = {'collection': 'users'}  # Spécifie la collection MongoDB
    name = db.StringField()  # Nom de l'utilisateur
    email = db.StringField()  # Email de l'utilisateur

    @classmethod
    def get(cls, user_id):
        # Récupérer un utilisateur via son ID
        return cls.objects(id=user_id).first()

    @classmethod
    def create(cls, name, email):
        # Créer un nouvel utilisateur et le sauvegarder
        user = cls(name=name, email=email)
        user.save()
        return user
"""

# --- Modèle de recherche ---
class Search(db.Document):
    meta = {'collection': 'searches'}  # Collection MongoDB pour les recherches
    user_id = db.ObjectIdField(required=False)  # ID de l'utilisateur (optionnel)
    keyword = db.StringField(required=True)  # Mot-clé recherché
    created_at = DateTimeField(default=datetime.now)  # Date de création
    tweets = db.ListField(db.ObjectIdField())  # Liste des ID de tweets associés

    @classmethod
    def create(cls, user_id, keyword):
        # Crée et enregistre une recherche
        search = cls(user_id=user_id, keyword=keyword)
        search.save()
        return search

# --- Modèle de tweet ---
class Tweet(db.Document):
    meta = {'collection': 'tweets'}  # Collection MongoDB pour les tweets
    user = db.StringField()  # Utilisateur ayant posté le tweet
    username = db.StringField()  # Nom d'utilisateur
    content = db.StringField()  # Contenu du tweet
    engagement = db.DictField()  # Dictionnaire contenant les engagements (likes, retweets, etc.)
    search_id = db.ObjectIdField(required=False)  # ID de recherche lié au tweet (optionnel)

    @classmethod
    def create(cls, user, username, content, engagement, search_id=None):
        # Crée et enregistre un tweet
        tweet = cls(user=user, username=username, content=content,
                    engagement=engagement, search_id=search_id)
        tweet.save()
        return tweet

# --- Modèle de lot (batch) ---
class Batch(db.Document):
    meta = {'collection': 'batches'}  # Collection MongoDB pour les lots
    user_id = db.ObjectIdField(required=False)  # ID de l'utilisateur associé au lot
    created_at = DateTimeField(default=datetime.now)  # Date de création du lot
    trends = db.ListField(db.ObjectIdField())  # Liste des tendances associées

    @classmethod
    def create(cls, user_id):
        # Crée et enregistre un lot
        batch = cls(user_id=user_id)
        batch.save()
        return batch

# --- Modèle de tendance ---
class Trend(db.Document):
    meta = {'collection': 'trends'}  # Collection MongoDB pour les tendances
    topic = db.StringField()  # Sujet de la tendance
    trend = db.StringField()  # Description de la tendance
    posts = db.IntField()  # Nombre de posts liés à la tendance
    batch_id = db.ObjectIdField(required=False)  # ID du lot associé (optionnel)
    created_at = DateTimeField(default=datetime.now)  # Date de création

    @classmethod
    def create(cls, topic, trend, posts, batch_id=None):
        # Crée et enregistre une tendance
        trd = cls(topic=topic, trend=trend, posts=posts, batch_id=batch_id)
        trd.save()
        return trd

# --- Modèle de résultat ---
class Result(db.Document):
    meta = {'collection': 'results'}  # Collection MongoDB pour les résultats
    user_id = db.ObjectIdField(required=False)  # ID de l'utilisateur associé
    created_at = DateTimeField(default=datetime.now)  # Date de création
    predictions = db.ListField(db.ObjectIdField())  # Liste des ID de prédictions

    @classmethod
    def create(cls, user_id):
        # Crée et enregistre un résultat
        result = cls(user_id=user_id)
        result.save()
        return result

# --- Modèle de prédiction ---
class Prediction(db.Document):
    meta = {'collection': 'predictions'}  # Collection MongoDB pour les prédictions
    tweet = db.StringField()  # Contenu du tweet analysé
    polarite = db.StringField()  # Polarité du tweet (positif, négatif, neutre)
    result_id = db.ObjectIdField(required=False)  # ID du résultat associé (optionnel)
    created_at = DateTimeField(default=datetime.now)  # Date de création

    @classmethod
    def create(cls, tweet, polarite, result_id=None):
        # Crée et enregistre une prédiction
        prediction = cls(tweet=tweet, polarite=polarite, result_id=result_id)
        prediction.save()
        return prediction
