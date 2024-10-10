from flask import render_template, request, redirect, url_for, flash
from app import app, scraper
from models import Search, Tweet, Batch, Trend
import json
import plotly.graph_objects as go
import plotly.io as pio
import io
import base64

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
        # Effectuer la recherche
        scraper.perform_search(keyword)

        # Collecter et parser les tweets
        scraper.scroll_and_collect_tweets()
        scraper.parse_tweet()

        user_id = None  # Remplacer par l'ID utilisateur approprié si nécessaire
        search = Search.create(user_id=user_id, keyword=keyword)

        # Sauvegarder les tweets structurés dans la base de données
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

        # Optionnellement sauvegarder la recherche
        search.tweets.extend(saved_tweet_ids)
        search.save()

        flash(f'Tweets collectés pour la recherche: "{keyword}"!')
    except Exception as e:
        flash(f'Erreur lors de la collecte des tweets: {str(e)}')

    return redirect(url_for('index'))


@app.route('/refresh_trends', methods=['GET'])
def refresh_trends():
    try:
        # Obtenir les tendances
        scraper.get_trends()

        # Collecter et analyser les tendances
        scraper.scroll_and_collect_trends()
        scraper.parse_trend()

        user_id = None  # Remplacer par l'ID utilisateur approprié si nécessaire
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

        return redirect(url_for('trends'))

    except Exception as e:
        flash(f'Erreur lors de la collecte des tendances: {str(e)}')
        return redirect(url_for('trends'))


@app.route('/trends', methods=['GET'])
def trends():
    latest_batch = Batch.objects.order_by('-created_at').first()
    if not latest_batch:
        flash('Aucun batch trouvé.')
        return redirect(url_for('index'))

    trends = Trend.objects(batch_id=latest_batch.id)
    structured_trends = group_trends_by_topic(trends)
    visualization_data = create_trend_visualization(structured_trends)

    return render_template('trends.html', structured_trends=structured_trends, visualization_data=visualization_data)

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
        top_trends = sorted(trends, key=lambda t: t.posts, reverse=True)[:2]
        visualization[topic] = {
            "trends": [t.trend for t in top_trends],
            "posts": [t.posts for t in top_trends],
        }

    # Générer le graphique
    fig = go.Figure()
    for topic, data in visualization.items():
        fig.add_trace(go.Bar(
            x=data['posts'],
            y=data['trends'],
            name=topic,
            orientation='h'
        ))

    fig.update_layout(
        title='Tendances par Nombre de Posts',
        xaxis_title='Posts',
        barmode='group',
        height=400
    )

    # Convertir le graphique en HTML
    graph_html = pio.to_html(fig, full_html=False)  # Utiliser pio ici
    return graph_html

