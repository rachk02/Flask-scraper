import random
import csv
import re
import numpy as np
import io
from flask import Response, render_template, request, redirect, url_for, flash
from keras_preprocessing.sequence import pad_sequences
from app import app, scraper, model, tokenizer, nlp
from models import Search, Tweet, Batch, Trend, Result, Prediction
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
import plotly.figure_factory as ff

# Route d'accueil
@app.route('/')
def index():
    return render_template('index.html')


# Route pour effectuer une recherche
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

    return redirect(url_for('predict'))


# Route pour rafraîchir les tendances
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


# Route pour afficher les tendances
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

    # Créer la visualisation des tendances
    graph_html, table_html = create_trend_visualization(structured_trends, default_topic)

    return render_template('trends.html', structured_trends=structured_trends, graph_html=graph_html, table_html=table_html)


# Fonction pour regrouper les tendances par sujet
def group_trends_by_topic(trends):
    grouped = {}
    for trend in trends:
        if trend.topic not in grouped:
            grouped[trend.topic] = []
        grouped[trend.topic].append(trend)
    return grouped


# Fonction pour générer des couleurs aléatoires pour chaque sujet
def generate_colors(topics):
    colors = {}
    for topic in topics:
        colors[topic] = f'rgba({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)}, 0.7)'
    return colors


# Fonction pour créer une visualisation des tendances
def create_trend_visualization(structured_trends, default_topic):
    visualization = {}
    all_trends = []  # Liste pour stocker toutes les tendances

    # Générer les couleurs pour chaque sujet
    colors = generate_colors(structured_trends.keys())

    for topic, trends in structured_trends.items():
        visualization[topic] = {
            "trends": [t.trend for t in trends],
            "posts": [t.posts for t in trends],
        }
        all_trends.extend(trends)

    # Créer les données pour la table
    table_data = []
    for trend in all_trends:
        table_data.append([trend.topic, trend.trend, trend.posts])

    # Générer le graphique
    fig = go.Figure()

    # Afficher les tendances, le sujet par défaut est affiché en premier
    for topic, data in visualization.items():
        fig.add_trace(go.Bar(
            x=data['trends'],  # Utiliser les tendances pour l'axe x
            y=data['posts'],  # Utiliser les posts pour l'axe y
            name=topic,
            marker=dict(color=colors[topic], line=dict(width=2, color='black')),
            visible='legendonly' if topic != default_topic else True  # Cacher sauf le sujet par défaut
        ))

    fig.update_layout(
        barmode='group',
        height=600,
        template='plotly_white',
        legend_title_text='Domaines',
        xaxis_title='Tendances',  # Titre pour l'axe x
        yaxis_title='Nombre de Posts'  # Titre pour l'axe y
    )

    # Convertir le graphique en HTML
    graph_html = pio.to_html(fig, full_html=False)

    # Créer une figure pour la table
    table_fig = go.Figure(data=[go.Table(
        header=dict(values=['Domaine', 'Tendance', 'Posts'],
                    fill_color='#fff2e9',
                    align='left'),
        cells=dict(values=list(zip(*table_data)),
                   fill_color='#eaf6ff',
                   align='left'))
    ])

    # Convertir la table en HTML
    table_html = pio.to_html(table_fig, full_html=False)

    return graph_html, table_html


# Route pour exporter les tendances
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


def get_tweets():
    latest_search = Search.objects.order_by('-created_at').first()

    # Récupérer les tweets associés à la dernière recherche
    if latest_search:
        tweets = Tweet.objects(id__in=latest_search.tweets)
    else:
        tweets = []

    return tweets


# Lemmatisation
def lemmatize_text(text):
    doc = nlp(text)
    lemmatized_tokens = [
        token.lemma_ for token in doc if not token.is_stop and not token.is_punct
    ]
    return ' '.join(lemmatized_tokens)

# Fonction pour prétraiter le texte
def preprocess_text(text):
    # Supprimer les URLs, mentions et hashtags
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'@\w+|#\w+', '', text)
    # Convertir en minuscules
    text = text.lower()
    # Supprimer la ponctuation
    text = re.sub(r'[^\w\s]', '', text)
    # Supprimer les stopwords
    text = lemmatize_text(text)
    return text


# Fonction pour prédire le sentiment
def predict_sentiment(texts):
    preprocessed_texts = [preprocess_text(text) for text in texts]
    sequences = tokenizer.texts_to_sequences(preprocessed_texts)
    padded_sequences = pad_sequences(sequences, maxlen=80)
    return model.predict(padded_sequences)

# Route pour prédire le sentiment des tweets
@app.route('/predict', methods=['GET'])
def predict():
    tweets = get_tweets()
    texts = [tweet['content'] for tweet in tweets]
    preprocessed_texts = [preprocess_text(text) for text in texts]
    # Prédire le sentiment
    predictions = predict_sentiment(preprocessed_texts)
    sentiment_labels = ['négatif', 'neutre', 'positif']

    # Catégoriser les prédictions selon le sentiment
    categorized_predictions = [sentiment_labels[np.argmax(pred)] for pred in predictions]

    # Créer une liste de listes avec les en-têtes
    results = list(zip(texts, categorized_predictions))  # Convertir en liste pour itération
    user_id = None  # Remplacer par l'ID utilisateur approprié si nécessaire
    resultat = Result.create(user_id=user_id)

    saved_prediction_ids = []
    # Sauvegarder les prédictions dans la base de données
    for tweet, polarite in results:
        prediction = Prediction.create(
            tweet=tweet,
            polarite=polarite,
            result_id=resultat.id
        )
        saved_prediction_ids.append(prediction.id)

    resultat.predictions.extend(saved_prediction_ids)
    resultat.save()

    # Créer la figure pour la table
    table_fig = go.Figure(data=[go.Table(
        header=dict(values=['Tweets', 'polarité'],
                    fill_color='#fff2e9',
                    align='left'),
        cells=dict(values=list(zip(*results)),  # Transpose the data
                   fill_color='#eaf6ff',
                   align='left'))
    ])
    table_fig.update_layout(height=550)

    # Créer le graphique circulaire
    sentiment_counts = pd.Series(categorized_predictions).value_counts().reset_index()
    sentiment_counts.columns = ['polarité', 'nombre']  # Renommer les colonnes

    pie_chart = go.Figure(data=[go.Pie(labels=sentiment_counts['polarité'],
                                       values=sentiment_counts['nombre'],
                                       title='Répartition de la polarité des tweets')])

    # Mettre à jour la mise en page pour le graphique circulaire
    pie_chart.update_layout(
        title_text='Analyse des Tweets',
        height=400,
        margin=dict(t=75, l=50),
        annotations=[dict(x=0.5, y=1.1, font_size=20, showarrow=False)]
    )

    # Convertir les figures en HTML
    table_html = table_fig.to_html(full_html=False)
    pie_chart_html = pie_chart.to_html(full_html=False)

    return render_template('sentiment_results.html', table_html=table_html, pie_chart_html=pie_chart_html)


# Route pour exporter les résultats des prédictions
@app.route('/export_results', methods=['GET'])
def export_results():
    latest_result = Result.objects.order_by('-created_at').first()
    if not latest_result:
        flash('Aucun batch trouvé.')
        return redirect(url_for('index'))

    predictions = Prediction.objects(result_id=latest_result.id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Tweet', 'polarité'])  # Écrire l'en-tête

    # Écrire chaque prédiction dans le CSV
    for prediction in predictions:
        writer.writerow([prediction.tweet, prediction.polarite])

    output.seek(0)  # Revenir au début du flux
    response = Response(output.getvalue(), content_type='text/csv')
    response.headers[
        'Content-Disposition'] = 'attachment; filename=resultats.csv'  # Nom du fichier pour le téléchargement

    return response



