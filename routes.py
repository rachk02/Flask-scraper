from flask import render_template, request, redirect, url_for, flash
from app import app, scraper
from models import Search, Tweet, Batch, Trend
import json
import plotly

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword')
    if not keyword:
        flash('Veuillez entrer un mot-clé pour la recherche.')
        return redirect(url_for('index'))

    try:
        # Perform search
        scraper.perform_search(keyword)

        # Collect and parse tweets
        scraper.scroll_and_collect_tweets()
        scraper.parse_tweet()

        user_id = None  # A remplacer par l'ID utilisateur approprié si nécessaire
        search = Search.create(user_id=user_id, keyword=keyword)

        # Save structured tweets to the database
        saved_tweet_ids = []
        for tweet_data in scraper.structured_tweets:
            tweet = Tweet.create(
                user=tweet_data['user'],
                username=tweet_data['username'],
                content=tweet_data['content'],
                engagement=tweet_data['engagement'],
                search_id=search.id
            )
            saved_tweet_ids.append(tweet.id)

        # Optionally save the search
        search.tweets.extend(saved_tweet_ids)
        search.save()

        flash(f'Tweets collectés pour la recherche: "{keyword}"!')
    except Exception as e:
        flash(f'Erreur lors de la collecte des tweets: {str(e)}')

    return redirect(url_for('index'))

@app.route('/trends', methods=['GET'])
def trends():
    try:
        # Obtenir les tendances
        scraper.get_trends()

        # Collecter et analyser les tendances
        scraper.scroll_and_collect_trends()
        scraper.parse_trend()

        user_id = None  # A remplacer par l'ID utilisateur approprié si nécessaire
        batch = Batch.create(user_id=user_id)

        # Enregistrer les tendances structurées dans la base de données
        saved_trend_ids = []
        for trend_data in scraper.structured_trends:
            trend = Trend.create(
                topic=trend_data['topic'],
                trend=trend_data['trend'],  # Correction ici, utilisez 'trend'
                posts=trend_data['posts'],
                batch_id=batch.id
            )
            saved_trend_ids.append(trend.id)

        # Enregistrer le batch
        batch.trends.extend(saved_trend_ids)
        batch.save()

    except Exception as e:
        flash(f'Erreur lors de la collecte des tendances: {str(e)}')

    return redirect(url_for('index'))
