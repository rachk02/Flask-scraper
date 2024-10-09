import re
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TwitterScraper:
    def __init__(self, credentials_file):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--lang=en")  # Set the language t670574e4d8db09ad9182cabao English
        chrome_options.add_argument("window-size=1200,10000")  # Set the default width and height
        self.driver = webdriver.Chrome(options=chrome_options)
        self.tweets = []
        self.structured_tweets = []
        self.trends = []
        self.structured_trends = []
        self.credentials_file = credentials_file
        self.logged_in = False

    def login(self):
        if not self.logged_in:
            with open(self.credentials_file) as f:
                credentials = json.load(f)

            self.driver.get("https://x.com/login")
            time.sleep(3)

            email_field = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            email_field.send_keys(credentials["email"])

            # Cliquer sur le bouton "Next"
            next_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Next']]"))
            )
            next_button.click()

            # Vérifier quel champ est présent après le premier clic
            try:
                username_field = WebDriverWait(self.driver, 7).until(
                    EC.presence_of_element_located((By.NAME, "text"))  # Vérifie si le champ d'utilisateur est présent
                )
                username_field.send_keys(credentials["username"])

                # Cliquer à nouveau sur le bouton "Next"
                next_button_again = WebDriverWait(self.driver, 7).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Next']]"))
                )
                next_button_again.click()

                # Maintenant, chercher le champ de mot de passe
                password_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "password"))
                )
                password_field.send_keys(credentials["password"])

                # Cliquer sur le bouton "Log in"
                login_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Log in']]"))
                )
                login_button.click()

            except Exception as e:
                # Si le champ d'utilisateur n'est pas présent, essayer le champ de mot de passe
                try:
                    password_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.NAME, "password"))
                    )
                    password_field.send_keys(credentials["password"])

                    # Cliquer sur le bouton "Log in"
                    login_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Log in']]"))
                    )
                    login_button.click()

                except Exception as e:
                    print("Erreur lors de l'authentification :", e)

            WebDriverWait(self.driver, 5).until(
                EC.url_contains("home")
            )
            # Navigate to the Explore section
            self.driver.get("https://x.com/explore")
            self.logged_in = True

    def perform_search(self, keyword):
        # free the previous search data
        self.tweets = []
        # Locate the search input field using XPath
        search_input = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@data-testid='SearchBox_Search_Input']"))
        )
        search_input.click()
        # Clear the input using Ctrl + A and Delete
        search_input.send_keys(Keys.CONTROL, 'a')  # Select all text
        search_input.send_keys(Keys.DELETE)  # Delete the selected text
        search_input.send_keys(keyword)
        search_input.send_keys(Keys.ENTER)

        # Notification

        time.sleep(10)  # Wait for the results to load

    def scroll_and_collect_tweets(self, scroll_pause_time=3, max_scrolls=3):
        # Scroll and collect tweets after the search
        for _ in range(max_scrolls):
            time.sleep(scroll_pause_time)
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, "article")
            for tweet in tweet_elements:
                tweet_text = tweet.text
                if tweet_text not in self.tweets:
                    self.tweets.append(tweet_text)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Function to convert tweet string to a structured dictionary
    def parse_tweet(self):

        self.structured_tweets = []  # List to store structured tweets
        tweets = self.tweets

        for tweet in tweets:
            tweet = tweet.replace("\n\n", ' ')
            lines = tweet.split('\n')

            # Ensure there are enough lines to parse
            if len(lines) < 8:
                continue

            # Check if the tweet is an ad
            if lines[2].strip() == 'Ad':
                continue  # Skip this tweet

            # Main tweet data
            tweet_data = {
                "user": lines[0].strip(),
                "username": lines[1].strip(),
                "content": ' '.join(line.strip() for line in lines[4:-4]),  # Join content lines
                "engagement": {
                    "likes": lines[-2].strip(),
                    "retweets": lines[-3].strip(),
                    "replies": lines[-4].strip(),
                    "views": lines[-1].strip()
                }
            }

            tweet_data["content"] = re.sub(r'\b\d+:\d+\b', '', tweet_data["content"]).strip()

            # Check for mentions
            for i, line in enumerate(lines):
                if "From" in line:
                    # Split content at "From" and reassign
                    content_part = tweet_data["content"].split("From", 1)[0].strip()  # Everything before "From"
                    tweet_data["content"] = content_part  # Update the content

            # Extract reposts
            reposts = []
            for i in range(5, len(lines) - 4):  # Adjust to avoid engagement lines
                if lines[i].startswith('@') and len(lines[i]) > 1 and lines[i + 1] == '·':
                    repost_data = {
                        "user": lines[i - 1].strip() if lines[i - 1].strip() != lines[4].strip() else None,
                        "username": lines[i].strip(),
                        "content": ' '.join(line.strip() for line in lines[i + 3:-4]),
                    }
                    repost_data["content"] = re.sub(r'\b\d+:\d+\b', '', repost_data["content"]).strip()
                    repost_data["content"] = repost_data["content"].replace('\\', '')

                    reposts.append(repost_data)

                    # Adjust the main tweet content based on the repost
                    if repost_data["user"] is not None:
                        tweet_data["content"] = tweet_data["content"].replace(repost_data["user"], '').strip()

                    # Split the content at repost line and reassign
                    if lines[i] in tweet_data["content"]:
                        split_index = tweet_data["content"].index(lines[i])
                        tweet_data["content"] = tweet_data["content"][:split_index].strip()

            if reposts:
                continue

            # Vérification de la longueur de likes
            if len(tweet_data["engagement"]["likes"]) > 4:
                tweet_data["content"] += f" {tweet_data['engagement']['likes']}"
                tweet_data["engagement"]["likes"] = "0"

            # Vérification de la longueur de retweets
            if len(tweet_data["engagement"]["retweets"]) > 4:
                tweet_data["content"] += f" {tweet_data['engagement']['retweets']}"
                tweet_data["engagement"]["retweets"] = "0"

            # Vérification de la longueur de replies
            if len(tweet_data["engagement"]["replies"]) > 4:
                tweet_data["content"] += f" {tweet_data['engagement']['replies']}"
                tweet_data["engagement"]["replies"] = "0"

            # Vérification de la longueur de views
            if len(tweet_data["engagement"]["views"]) > 4:
                tweet_data["content"] += f" {tweet_data['engagement']['views']}"
                tweet_data["engagement"]["views"] = "0"

            tweet_data["content"] = tweet_data["content"].replace('\\', '')

            self.structured_tweets.append(tweet_data)  # Append the structured tweet data to the list

        return self.structured_tweets  # Return the list of structured tweets


    def get_trends(self):
        self.trends = []

        # Navigate to the Explore section
        self.driver.get("https://x.com/explore")

        # Cliquer sur l'onglet "Trending"
        trending_tab = WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "//a[contains(@href, '/explore/tabs/trending')]"))
        )
        trending_tab.click()
        time.sleep(3)
        self.scroll_and_collect_trends()

        # Cliquer sur l'onglet "News"
        news_tab = WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "//a[contains(@href, '/explore/tabs/news')]"))
        )
        news_tab.click()
        time.sleep(3)
        self.scroll_and_collect_trends()

        # Cliquer sur l'onglet "Sports"
        sports_tab = WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "//a[contains(@href, '/explore/tabs/sports')]"))
        )
        sports_tab.click()
        time.sleep(3)
        self.scroll_and_collect_trends()

        # Cliquer sur l'onglet "Entertainment"
        entertainment_tab = WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "//a[contains(@href, '/explore/tabs/entertainment')]"))
        )
        entertainment_tab.click()
        time.sleep(3)
        self.scroll_and_collect_trends()

    def scroll_and_collect_trends(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            # Collect visible trends using a more specific selector
            time.sleep(5)
            trend_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='trend']")
            for trend in trend_elements:
                trend_text = trend.text
                if trend_text and trend_text not in self.trends:
                    self.trends.append(trend_text)  # Collect only the text of the trend

            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # Check if we reached the bottom
                break
            last_height = new_height

    def parse_trend(self):

        self.structured_trends = []  # Liste pour stocker les tendances structurées
        trends = self.trends  # Récupérer les tendances à partir de l'attribut 'trends'

        for trd in trends:
            lines = trd.split('\n')  # Diviser chaque tendance en lignes

            # Vérifier si la dernière ligne contient des informations sur les posts
            if lines[-1].endswith("posts"):
                # Extraire le nombre de posts en enlevant le mot "posts"
                posts_info = lines[-1].replace("posts", "").strip()

                topic = None  # Variable pour stocker le sujet de la tendance
                trend = None  # Variable pour stocker le texte de la tendance

                # Parcourir les lignes pour trouver le sujet et la tendance
                for line_index, line in enumerate(lines):
                    if "· Trending" in line:
                        tpc = lines[line_index].replace("· Trending", "").strip()
                        topic = tpc
                        trend = lines[line_index + 1].strip()  # Obtenir la ligne suivante comme tendance
                        break
                    elif "Trending in" in line:
                        tpc = lines[line_index].replace("Trending in", "").strip()
                        topic = tpc
                        trend = lines[line_index + 1].strip()
                        break
                    elif "Trending" in line:
                        tpc = lines[line_index].replace("Trending", "").strip()
                        topic = tpc
                        trend = lines[line_index + 1].strip()
                        break

                def convert_posts_to_int(n):
                    # Vérifier le format du nombre de posts
                    if 'M' in n:
                        # Convertir les millions (M) en nombre entier
                        number = n.replace('M', '').strip()
                        return int(float(number) * 1_000_000)
                    if 'K' in n:
                        # Convertir les milliers (K) en nombre entier
                        number = n.replace('K', '').strip()
                        return int(float(number) * 1_000)
                    elif ',' in n:
                        # Supprimer les virgules et convertir en entier
                        number = n.replace(',', '').strip()
                        return int(number)
                    else:
                        return int(n)  # Conversion standard si aucun format spécial

                # Créer un dictionnaire pour stocker les données de tendance
                trend_data = {
                    "topic": topic,
                    "trend": trend,
                    "posts": convert_posts_to_int(posts_info)
                }

                self.structured_trends.append(trend_data)  # Ajouter les données structurées à la liste

        return self.structured_trends  # Retourner les données structurées

    def close(self):
        self.driver.quit()
