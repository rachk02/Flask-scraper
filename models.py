from flask_login import UserMixin
from mongoengine import DateTimeField

from app import db
from datetime import datetime

class User(db.Document, UserMixin):
    meta = {'collection': 'users'}
    name = db.StringField()
    email = db.StringField()

    @classmethod
    def get(cls, user_id):
        return cls.objects(id=user_id).first()

    @classmethod
    def create(cls, name, email):
        user = cls(name=name, email=email)
        user.save()
        return user


class Search(db.Document):
    meta = {'collection': 'searches'}
    user_id = db.ObjectIdField(required=False)  # User ID related to the search
    keyword = db.StringField(required=True)  # Keyword for the search
    created_at = DateTimeField(default=datetime.now)  # Automatically set the creation time
    tweets = db.ListField(db.ObjectIdField())  # List of tweet IDs

    @classmethod
    def create(cls, user_id, keyword):
        search = cls(user_id=user_id, keyword=keyword)
        search.save()
        return search


class Tweet(db.Document):
    meta = {'collection': 'tweets'}
    user = db.StringField()
    username = db.StringField()
    content = db.StringField()
    engagement = db.DictField()  # Dictionnaire pour stocker les données d'engagement
    search_id = db.ObjectIdField(required=False)  # ID de la recherche liée au tweet (optionnel)

    @classmethod
    def create(cls, user, username, content, engagement, search_id=None):
        tweet = cls(user=user, username=username, content=content, engagement=engagement, search_id=search_id)
        tweet.save()
        return tweet

class Batch(db.Document):
    meta = {'collection': 'batches'}
    user_id = db.ObjectIdField(required=False)  # User ID related to the search
    created_at = DateTimeField(default=datetime.now)  # Automatically set the creation time
    trends = db.ListField(db.ObjectIdField())  # List of trend IDs

    @classmethod
    def create(cls, user_id):
        search = cls(user_id=user_id)
        search.save()
        return search

class Trend(db.Document):
    meta = {'collection': 'trends'}
    topic = db.StringField()
    trend = db.StringField()
    posts = db.IntField()
    batch_id = db.ObjectIdField(required=False)  # ID de la recherche liée au batch (optionnel)
    created_at = DateTimeField(default=datetime.now)  # Automatically set the creation time


    @classmethod
    def create(cls, topic, trend, posts, batch_id=None):
        trd = cls(topic=topic, trend=trend, posts=posts, batch_id=batch_id)
        trd.save()
        return trd