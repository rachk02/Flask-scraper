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

def collect_and_visualize_trends():
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
                trend=trend_data['trend'],
                posts=trend_data['posts'],
                batch_id=batch.id
            )
            saved_trend_ids.append(trend.id)

        # Enregistrer le batch
        batch.trends.extend(saved_trend_ids)
        batch.save()

        # Obtenir le dernier batch pour visualisation
        return get_latest_batch_visualization()

    except Exception as e:
        flash(f'Erreur lors de la collecte des tendances: {str(e)}')
        return None, None


def get_latest_batch_visualization():
    try:
        # Obtenir le dernier batch
        latest_batch = Batch.objects.order_by('-created_at').first()
        if not latest_batch:
            flash('Aucun batch trouvé.')
            return None, None

        # Obtenir les tendances associées à ce batch
        trends = Trend.objects(batch_id=latest_batch.id)

        # Grouper par topic
        structured_trends = group_trends_by_topic(trends)
        visualization = create_trend_visualization(structured_trends)

        # Convertir la visualisation en JSON
        visualization_json = json.dumps(visualization, cls=plotly.utils.PlotlyJSONEncoder)

        return structured_trends, visualization_json

    except Exception as e:
        flash(f'Erreur lors de la récupération des tendances: {str(e)}')
        return None, None


@app.route('/trends', methods=['GET'])
def trends():
    structured_trends, visualization_json = collect_and_visualize_trends()

    if structured_trends is None:
        return redirect(url_for('index'))

    return render_template('trends.html', structured_trends=structured_trends, visualization_json=visualization_json)


def group_trends_by_topic(trends):
    grouped = {}
    for trend in trends:
        if trend.topic not in grouped:
            grouped[trend.topic] = []
        grouped[trend.topic].append(trend)
    return grouped

def create_trend_visualization(structured_trends):
    visualization = {}
    for topic, trends in structured_trends.items():
        # Sélectionner les deux tendances avec le plus de posts
        top_trends = sorted(trends, key=lambda t: t.posts, reverse=True)[:2]
        visualization[topic] = {
            "trends": [t.trend for t in top_trends],
            "posts": [t.posts for t in top_trends],
        }
    return visualization
