import random
import csv
import io
from flask import Response
from flask import render_template, request, redirect, url_for, flash
from app import app, scraper
from models import Search, Tweet, Batch, Trend
import plotly.graph_objects as go
import plotly.io as pio


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

    # Sélectionner le premier topic comme défaut
    default_topic = list(structured_trends.keys())[0] if structured_trends else None

    graph_html, table_html = create_trend_visualization(structured_trends, default_topic)

    return render_template('trends.html', structured_trends=structured_trends, graph_html=graph_html, table_html=table_html)



def group_trends_by_topic(trends):
    grouped = {}
    for trend in trends:
        if trend.topic not in grouped:
            grouped[trend.topic] = []
        grouped[trend.topic].append(trend)
    return grouped


def generate_colors(topics):
    """Génère une couleur aléatoire pour chaque topic."""
    colors = {}
    for topic in topics:
        colors[topic] = f'rgba({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)}, 0.7)'
    return colors


def create_trend_visualization(structured_trends, default_topic):
    visualization = {}
    all_trends = []  # Liste pour stocker toutes les tendances

    # Générer les couleurs pour chaque topic
    colors = generate_colors(structured_trends.keys())

    for topic, trends in structured_trends.items():
        # Utiliser les tendances telles quelles, sans tri
        visualization[topic] = {
            "trends": [t.trend for t in trends],
            "posts": [t.posts for t in trends],
        }
        # Ajouter toutes les tendances à la liste
        all_trends.extend(trends)

    # Créer les données pour la table sans tri
    table_data = []
    for trend in all_trends:
        table_data.append([trend.topic, trend.trend, trend.posts])

    # Générer le graphique
    fig = go.Figure()

    # Afficher tous les trends, mais le topic par défaut est affiché en premier
    for topic, data in visualization.items():
        fig.add_trace(go.Bar(
            x=data['posts'],
            y=data['trends'],
            name=topic,
            orientation='h',
            marker=dict(color=colors[topic], line=dict(width=0.7, color='black')),
            visible='legendonly' if topic != default_topic else True  # Cacher sauf le default
        ))

    fig.update_layout(
        barmode='group',
        height=600,
        template='plotly_white',
        legend_title_text='Domaines'
    )

    # Convertir le graphique en HTML
    graph_html = pio.to_html(fig, full_html=False)

    # Créer une figure pour la table
    table_fig = go.Figure(data=[go.Table(
        header=dict(values=['Domaine', 'Tendance', 'Posts'],
                    fill_color='#002239',
                    align='left'),
        cells=dict(values=list(zip(*table_data)),
                   fill_color='#eaf6ff',
                   align='left'))
    ])

    # Convertir la table en HTML
    table_html = pio.to_html(table_fig, full_html=False)

    return graph_html, table_html


@app.route('/export_trends', methods=['GET'])
def export_trends():
    latest_batch = Batch.objects.order_by('-created_at').first()
    if not latest_batch:
        flash('Aucun batch trouvé.')
        return redirect(url_for('index'))

    trends = Trend.objects(batch_id=latest_batch.id)

    # Utiliser StringIO pour écrire le CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Domaine', 'Tendance', 'Posts'])  # Écrire l'en-tête

    for trend in trends:
        writer.writerow([trend.topic, trend.trend, trend.posts])  # Écrire chaque ligne

    # Récupérer le contenu CSV généré
    output.seek(0)
    response = Response(output.getvalue(), content_type='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=trends.csv'

    return response
