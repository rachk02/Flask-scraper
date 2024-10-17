# Documentation - Projet Tutoré : Analyse des Tweets

## Table des matières
1. [Introduction](#introduction)
2. [Prérequis](#prérequis)
3. [Installation et Configuration](#installation-et-configuration)
   - [Clonage du Dépôt et Environnement Virtuel](#clonage-du-dépôt-et-environnement-virtuel)
   - [Installation de MongoDB](#installation-de-mongodb)
   - [Création de la Base de Données](#création-de-la-base-de-données)
   - [Installation des Dépendances](#installation-des-dépendances)
4. [Description des Fichiers](#description-des-fichiers)
   - [app.py](#app-py)
   - [models.py](#models-py)
   - [scraper.py](#scraper-py)
   - [routes.py](#routes-py)
5. [Lancement de l'Application](#lancement-de-lapplication)
6. [Fonctionnalités Principales](#fonctionnalités-principales)
7. [Utilisation et Routes](#utilisation-et-routes)
8. [Conclusion et Remarques](#conclusion-et-remarques)

---

## 1. Introduction <a name="introduction"></a>

Ce projet a pour objectif de scraper des tweets en fonction de mots-clés spécifiques, d'analyser les sentiments exprimés dans les tweets, et de générer des rapports basés sur ces analyses. L'application utilise Flask comme framework web, MongoDB comme base de données, Selenium pour le scraping de tweets, et un modèle de traitement de langage naturel (NLP) pour l'analyse de sentiments.

---

## 2. Prérequis <a name="prérequis"></a>

Avant de commencer, assurez-vous d'avoir les éléments suivants installés :

- **Python 3.8+**
- **Git**
- **MongoDB**
- **Chrome** (pour Selenium)

---

## 3. Installation et Configuration <a name="installation-et-configuration"></a>

### 3.1 Clonage du Dépôt et Environnement Virtuel <a name="clonage-du-dépôt-et-environnement-virtuel"></a>

1. **Cloner le dépôt GitHub** :
   ```bash
   git clone https://github.com/rachk02/Flask-scraper.git
   cd Flask-scraper
   ```

2. **Créer et activer un environnement virtuel** :
   ```bash
   python -m venv env
   ```

   - **Windows** :  
     ```bash
     .\env\Scripts\activate
     ```
   - **macOS/Linux** :  
     ```bash
     source env/bin/activate
     ```

### 3.2 Installation de MongoDB <a name="installation-de-mongodb"></a>

1. **Installation** : Suivez les instructions officielles pour installer MongoDB [ici](https://docs.mongodb.com/manual/installation/).

2. **Lancement de MongoDB** :
   ```bash
   sudo systemctl start mongod
   ```

   Pour démarrer MongoDB automatiquement :
   ```bash
   sudo systemctl enable mongod
   ```

### 3.3 Création de la Base de Données <a name="création-de-la-base-de-données"></a>

1. **Créer la base de données et les collections** :
   ```bash
   mongosh
   use app_data;

   db.createCollection("batches");
   db.createCollection("predictions");
   db.createCollection("searches");
   db.createCollection("tweets");
   db.createCollection("results");
   db.createCollection("trends");
   ```

### 3.4 Installation des Dépendances <a name="installation-des-dépendances"></a>

1. **Installer les packages requis** :
   ```bash
   pip install -r requirements.txt
   ```

---

## 4. Description des Fichiers <a name="description-des-fichiers"></a>

### 4.1 app.py <a name="app-py"></a>

Le fichier `app.py` est le point d'entrée principal de l'application Flask. Voici ses fonctionnalités principales :

- **Configuration** : 
  - Connexion à MongoDB via MongoEngine.
  - Initialisation du scraper Twitter et des modèles de traitement de langage naturel (NLP) pour l'analyse des sentiments.
  
- **Modules chargés** : 
  - Scraper Twitter (`TwitterScraper`) pour le scraping des tweets.
  - Modèle Keras pour la prédiction des sentiments.
  - Tokenizer pour transformer les textes en séquences utilisables.

### 4.2 models.py <a name="models-py"></a>

`models.py` définit les modèles de données utilisés pour stocker les informations dans MongoDB :

- **Search** : Représente une recherche de tweets.
- **Tweet** : Stocke les tweets collectés.
- **Batch** : Groupement de tendances récupérées.
- **Trend** : Stocke les tendances Twitter.
- **Result** : Stocke les résultats d'analyse des tweets.
- **Prediction** : Stocke les prédictions de sentiment sur les tweets.

Chaque modèle contient une méthode `create` qui permet d'insérer facilement des documents dans la base de données.

### 4.3 scraper.py <a name="scraper-py"></a>

Le fichier `scraper.py` contient la classe `TwitterScraper`, qui utilise Selenium pour scraper les tweets et tendances depuis Twitter. Les principales fonctions sont :

- **login()** : Connexion à Twitter via Selenium.
- **perform_search()** : Recherche de tweets en fonction d'un mot-clé.
- **scroll_and_collect_tweets()** : Collecte les tweets par défilement.
- **parse_tweet()** : Formatte les tweets collectés en dictionnaires structurés.
- **get_trends()** : Récupère et formate les tendances actuelles.

### 4.4 routes.py <a name="routes-py"></a>

Le fichier `routes.py` définit les routes Flask qui gèrent les différentes fonctionnalités de l'application. Les principales routes sont :

- **`/`** : Page d'accueil.
- **`/search`** : Permet de rechercher des tweets et de les sauvegarder.
- **`/refresh_trends`** : Actualise et sauvegarde les tendances Twitter.
- **`/predict`** : Prédiction du sentiment des tweets.
- **`/export_results`** et **`/export_trends`** : Exportation des résultats et des tendances en CSV.

---

## 5. Lancement de l'Application <a name="lancement-de-lapplication"></a>

1. **Lancer MongoDB** :
   ```bash
   sudo systemctl start mongod
   ```

2. **Activer l'environnement virtuel** :
   ```bash
   source env/bin/activate  # macOS/Linux
   .\env\Scripts\activate   # Windows
   ```

3. **Lancer l'application Flask** :
   ```bash
   flask run
   ```

L'application sera accessible à l'adresse : `http://127.0.0.1:5000/`.

---

## 6. Fonctionnalités Principales <a name="fonctionnalités-principales"></a>

### 6.1 Scraping des Tweets

Le scraping des tweets se fait via l'interface `/search`. Les tweets sont ensuite sauvegardés dans la collection `tweets` de MongoDB. Le scraper peut être configuré dans `scraper.py` avec les identifiants Twitter dans le fichier `credentials.json`.

### 6.2 Récupération et Analyse des Tendances

La route `/refresh_trends` permet de collecter les tendances actuelles sur Twitter, qui sont ensuite affichées sous forme de graphiques dans la route `/trends`.

### 6.3 Prédiction du Sentiment des Tweets

La route `/predict` permet d'effectuer une analyse de sentiment sur les tweets sauvegardés. Le modèle Keras pré-entraîné est utilisé pour prédire la polarité (négatif, neutre, positif) de chaque tweet.

### 6.4 Export des Résultats

Les tendances et résultats de prédiction peuvent être exportés au format CSV via les routes `/export_trends` et `/export_results`.

---

## 7. Utilisation et Routes <a name="utilisation-et-routes"></a>

Voici un aperçu des principales routes Flask et de leur fonction :

- **`/`** : Page d'accueil.
- **`/search`** (POST) : Recherche de tweets à partir d'un mot-clé.
- **`/refresh_trends`** (GET) : Actualisation des tendances Twitter.
- **`/trends`** (GET) : Affichage des tendances avec graphiques.
- **`/predict`** (GET) : Analyse de sentiment des tweets récupérés.
- **`/export_trends`** (GET) : Export des tendances en CSV.
- **`/export_results`** (GET) : Export des résultats d'analyse des tweets en CSV.

---

## 8. Conclusion et Remarques <a name="conclusion-et-remarques"></a>

Ce projet utilise une combinaison de Flask, MongoDB, Selenium, et un modèle de traitement de langage naturel pour fournir une plateforme de scraping et

 d'analyse de tweets. Les résultats sont visualisés sous forme de graphiques interactifs et peuvent être exportés pour une analyse plus approfondie.

### Remarques :
- Assurez-vous que MongoDB est démarré avant de lancer l'application Flask.
- L'environnement virtuel doit être activé à chaque nouvelle session.
- Le fichier `credentials.json` doit être correctement configuré avec vos identifiants Twitter pour que le scraper fonctionne.