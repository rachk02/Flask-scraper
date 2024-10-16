### README - Projet Tutoré : Analyse des Tweets

Ce projet a pour objectif de scraper des tweets liés à des mots-clés spécifiques, d'analyser les sentiments et les tendances, et de générer des rapports d'analyse. Cette documentation vous guide pour configurer l'environnement de développement, installer MongoDB, créer la base de données, installer les dépendances et lancer l'application Flask.

---

#### 1. Prérequis

Assurez-vous d'avoir les éléments suivants installés sur votre machine :

- **Python 3.8+**
- **Git**
- **MongoDB**
- **Chrome**

---

#### 2. Création de l'Environnement Virtuel

1. **Cloner le dépôt GitHub**

   Clonez le dépôt GitHub du projet en utilisant la commande suivante :

   ```bash
   git clone https://github.com/rachk02/Flask-scraper.git
   cd Flask-scraper
   ```

2. **Créer et activer un environnement virtuel**

   Pour isoler les dépendances du projet, créez un environnement virtuel :

   ```bash
   # Création de l'environnement virtuel
   python -m venv env

   # Activation de l'environnement virtuel
   # Sur Windows
   .\env\Scripts\activate
   # Sur macOS/Linux
   source env/bin/activate
   ```

---

#### 3. Installation de MongoDB

1. **Téléchargement et installation de MongoDB**

   Suivez les instructions officielles pour installer MongoDB en local : [Installation MongoDB](https://docs.mongodb.com/manual/installation/)

2. **Lancer MongoDB localement**

 - Assurez-vous que MongoDB est démarré en exécutant la commande suivante :

    ```bash
    sudo systemctl start mongod
    ``
 - Si vous voulez qu'il démarre automatiquement à chaque fois que vous allumez votre ordinateur, utilisez :
    
    ```bash
    sudo systemctl enable mongod
    ```

---

#### 4. Création de la Base de Données et des Collections

1. **Script MongoDB pour créer la base de données et les collections**

   Utilisez `mongosh` pour créer la base de données `app_data` et ses collections :

   ```bash
   mongosh
   ```

   Une fois dans la console MongoDB, exécutez le script suivant :

   ```javascript
   use app_data;

   db.createCollection("batches");
   db.createCollection("predictions");
   db.createCollection("searches");
   db.createCollection("tweets");
   db.createCollection("results");
   db.createCollection("trends");
   ```

---

#### 5. Installation des Dépendances

1. **Installer les packages requis**

   Installez toutes les dépendances nécessaires à l'aide du fichier `requirements.txt` :

   ```bash
   pip install -r requirements.txt
   ```

---

#### 6. Lancement de l'Application Flask

1. **Lancer l'application**

   Une fois toutes les étapes précédentes terminées, vous pouvez lancer l'application Flask :

   ```bash
   flask run
   ```

   L'application sera accessible à l'adresse suivante : `http://127.0.0.1:5000/`

---

### Remarques supplémentaires

- N'oubliez pas d'activer l'environnement virtuel à chaque fois que vous travaillez sur le projet.
- MongoDB doit être démarré avant de lancer l'application Flask.
