import random
import csv
import re
import numpy as np
import io
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
from flask import Response, render_template, request, redirect, url_for, flash
from keras_preprocessing.sequence import pad_sequences
from app import app, scraper, model, tokenizer, nlp
from models import Search, Tweet, Batch, Trend, Result, Prediction

# === Route d'accueil ===
@app.route('/')
def index():
    """Affiche la page d'accueil."""
    return render_template('index.html')


# === Route pour effectuer une recherche de tweets ===
@app.route('/search', methods=['POST'])
def search():
    """Gère la recherche des tweets et leur sauvegarde dans la base de données."""
    keyword = request.form.get('keyword')
    if not keyword:
        flash('Veuillez entrer un mot-clé pour la recherche.')
        return redirect(url_for('index'))

    try:
        scraper.perform_search(keyword)  # Recherche initiale
        scraper.scroll_and_collect_tweets()  # Collecter les tweets par défilement
        scraper.parse_tweet()  # Parser les tweets

        user_id = None  # Ajouter l'ID utilisateur si nécessaire
        search = Search.create(user_id=user_id, keyword=keyword)

        # Sauvegarder les tweets dans la base de données
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

        search.tweets.extend(saved_tweet_ids)  # Associer les tweets à la recherche
        search.save()

        flash(f'Tweets collectés pour la recherche: "{keyword}"!')
    except Exception as e:
        flash(f'Erreur lors de la collecte des tweets: {str(e)}')

    return redirect(url_for('predict'))


# === Route pour rafraîchir les tendances ===
@app.route('/refresh_trends', methods=['GET'])
def refresh_trends():
    """Actualise et sauvegarde les tendances actuelles."""
    try:
        scraper.get_trends()  # Récupérer les tendances
        scraper.scroll_and_collect_trends()
        scraper.parse_trend()

        user_id = None  # Ajouter l'ID utilisateur si nécessaire
        batch = Batch.create(user_id=user_id)

        # Sauvegarder les tendances
        saved_trend_ids = []
        for trend_data in scraper.structured_trends:
            trend = Trend.create(
                topic=trend_data['topic'],
                trend=trend_data['trend'],
                posts=trend_data['posts'],
                batch_id=batch.id
            )
            saved_trend_ids.append(trend.id)

        batch.trends.extend(saved_trend_ids)
        batch.save()

        return redirect(url_for('trends'))
    except Exception as e:
        flash(f'Erreur lors de la collecte des tendances: {str(e)}')
        return redirect(url_for('trends'))


# === Route pour afficher les tendances ===
@app.route('/trends', methods=['GET'])
def trends():
    """Affiche les tendances actuelles avec une visualisation graphique."""
    latest_batch = Batch.objects.order_by('-created_at').first()
    if not latest_batch:
        flash('Aucun batch trouvé.')
        return redirect(url_for('refresh_trends'))

    trends = Trend.objects(batch_id=latest_batch.id)
    structured_trends = group_trends_by_topic(trends)

    default_topic = list(structured_trends.keys())[0] if structured_trends else None

    graph_html, table_html = create_trend_visualization(structured_trends, default_topic)

    return render_template('trends.html', structured_trends=structured_trends,
                           graph_html=graph_html, table_html=table_html)


# === Fonction pour regrouper les tendances par sujet ===
def group_trends_by_topic(trends):
    """Groupe les tendances par sujet."""
    grouped = {}
    for trend in trends:
        if trend.topic not in grouped:
            grouped[trend.topic] = []
        grouped[trend.topic].append(trend)
    return grouped


# === Générer des couleurs aléatoires ===
def generate_colors(topics):
    """Génère des couleurs aléatoires pour chaque sujet."""
    colors = {}
    for topic in topics:
        colors[topic] = f'rgba({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)}, 0.7)'
    return colors


# === Visualisation des tendances ===
def create_trend_visualization(structured_trends, default_topic):
    """Crée un graphique et une table pour visualiser les tendances."""
    visualization = {}
    all_trends = []
    colors = generate_colors(structured_trends.keys())

    for topic, trends in structured_trends.items():
        visualization[topic] = {
            "trends": [t.trend for t in trends],
            "posts": [t.posts for t in trends],
        }
        all_trends.extend(trends)

    table_data = [[trend.topic, trend.trend, trend.posts] for trend in all_trends]

    fig = go.Figure()
    for topic, data in visualization.items():
        fig.add_trace(go.Bar(
            x=data['trends'], y=data['posts'], name=topic,
            marker=dict(color=colors[topic], line=dict(width=2, color='black')),
            visible='legendonly' if topic != default_topic else True
        ))

    fig.update_layout(barmode='group', height=600, template='plotly_white',
                      legend_title_text='Domaines', xaxis_title='Tendances', yaxis_title='Nombre de Posts')

    graph_html = pio.to_html(fig, full_html=False)

    table_fig = go.Figure(data=[go.Table(
        header=dict(values=['Domaine', 'Tendance', 'Posts'], fill_color='#fff2e9', align='left'),
        cells=dict(values=list(zip(*table_data)), fill_color='#eaf6ff', align='left'))
    ])
    table_html = pio.to_html(table_fig, full_html=False)

    return graph_html, table_html


# === Exportation des tendances en CSV ===
@app.route('/export_trends', methods=['GET'])
def export_trends():
    """Exporte les tendances en fichier CSV."""
    latest_batch = Batch.objects.order_by('-created_at').first()
    if not latest_batch:
        flash('Aucun batch trouvé.')
        return redirect(url_for('index'))

    trends = Trend.objects(batch_id=latest_batch.id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Domaine', 'Tendance', 'Posts'])
    for trend in trends:
        writer.writerow([trend.topic, trend.trend, trend.posts])

    output.seek(0)
    response = Response(output.getvalue(), content_type='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=trends.csv'

    return response


def get_tweets():
    """Récupère les tweets associés à la dernière recherche."""
    latest_search = Search.objects.order_by('-created_at').first()
    if latest_search:
        tweets = Tweet.objects(id__in=latest_search.tweets)
    else:
        tweets = []
    return tweets


# === Prétraitement du texte ===
def preprocess_text(text):
    """Supprime les URLs, mentions, hashtags et ponctuations puis applique la lemmatisation."""
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)  # Supprimer les URLs
    text = re.sub(r'@\w+|#\w+', '', text)  # Supprimer les mentions et hashtags
    text = text.lower()  # Convertir en minuscules
    text = re.sub(r'[^\w\s]', '', text)  # Supprimer la ponctuation
    return lemmatize_text(text)  # Lemmatiser le texte


# === Lemmatisation ===
def lemmatize_text(text):
    """Lemmatise le texte en supprimant les stopwords et la ponctuation."""
    doc = nlp(text)
    return ' '.join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])


def predict_sentiment(texts):
    """Prédire le sentiment des textes fournis."""
    preprocessed_texts = [preprocess_text(text) for text in texts]  # Prétraitement
    sequences = tokenizer.texts_to_sequences(preprocessed_texts)  # Conversion en séquences numériques
    padded_sequences = pad_sequences(sequences, maxlen=80)  # Remplissage pour aligner les séquences
    return model.predict(padded_sequences)  # Prédiction des sentiments


# === Route pour afficher les prédictions de sentiment des tweets ===
@app.route('/predict', methods=['GET'])
def predict():
    """Prédire le sentiment des tweets et afficher les résultats sous forme de tableau et graphique."""
    tweets = get_tweets()  # Récupère les tweets à partir de la dernière recherche
    texts = [tweet['content'] for tweet in tweets]

    preprocessed_texts = [preprocess_text(text) for text in texts]  # Prétraiter les tweets
    predictions = predict_sentiment(preprocessed_texts)  # Prédire les sentiments

    sentiment_labels = ['négatif', 'neutre', 'positif']  # Catégories de sentiment
    categorized_predictions = [sentiment_labels[np.argmax(pred)] for pred in predictions]

    # Nettoyer les textes (supprimer mentions et hashtags)
    texts = [re.sub(r'@\w+|#\w+', '', text) for text in texts]

    results = list(zip(texts, categorized_predictions))  # Associer tweets et prédictions
    user_id = None  # Ajouter l'ID utilisateur si nécessaire
    resultat = Result.create(user_id=user_id)

    saved_prediction_ids = []
    # Enregistrer les prédictions dans la base de données
    for tweet, polarite in results:
        prediction = Prediction.create(
            tweet=tweet,
            polarite=polarite,
            result_id=resultat.id
        )
        saved_prediction_ids.append(prediction.id)

    resultat.predictions.extend(saved_prediction_ids)  # Associer les prédictions au résultat
    resultat.save()

    # Création du tableau des résultats
    table_fig = go.Figure(data=[go.Table(
        header=dict(values=['Tweets', 'Polarité'], fill_color='#fff2e9', align='left'),
        cells=dict(values=list(zip(*results)), fill_color='#eaf6ff', align='left'))
    ])
    table_fig.update_layout(height=550)

    # Création du graphique circulaire
    sentiment_counts = pd.Series(categorized_predictions).value_counts().reset_index()
    sentiment_counts.columns = ['Polarité', 'Nombre']  # Renommer les colonnes

    pie_chart = go.Figure(data=[go.Pie(
        labels=sentiment_counts['Polarité'],
        values=sentiment_counts['Nombre'],
        title='Répartition de la polarité des tweets'
    )])

    pie_chart.update_layout(
        title_text='Analyse des Tweets',
        height=400,
        margin=dict(t=75, l=50),
        annotations=[dict(x=0.5, y=1.1, font_size=20, showarrow=False)]
    )

    # Convertir les figures en HTML
    table_html = table_fig.to_html(full_html=False)
    pie_chart_html = pie_chart.to_html(full_html=False)

    return render_template('sentiment_results.html',
                           table_html=table_html,
                           pie_chart_html=pie_chart_html)


# === Route pour exporter les résultats de prédictions en CSV ===
@app.route('/export_results', methods=['GET'])
def export_results():
    """Exporte les résultats de prédiction en fichier CSV."""
    latest_result = Result.objects.order_by('-created_at').first()
    if not latest_result:
        flash('Aucun résultat trouvé.')
        return redirect(url_for('index'))

    predictions = Prediction.objects(result_id=latest_result.id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Tweet', 'Polarité'])  # En-tête du fichier CSV

    # Écrire chaque prédiction dans le fichier CSV
    for prediction in predictions:
        writer.writerow([prediction.tweet, prediction.polarite])

    output.seek(0)  # Revenir au début du flux en mémoire
    response = Response(output.getvalue(), content_type='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=resultats.csv'

    return response
