import os

class Config:
    secret_key = os.environ.get('SECRET_KEY')
    MONGODB_SETTINGS = {
        'db': 'app_data',
        'host': 'localhost',
        'port': 27017
    }
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    # GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
    # GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')