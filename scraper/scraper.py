import time
import json
from pathlib import Path
from selenium import webdriver
from key_words import KeywordManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TwitterScraper:
    def __init__(self, credentials_file):
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("window-size=1200,10000")  # Set the default width and height
        self.driver = webdriver.Chrome(options=chrome_options)
        self.tweets = []
        self.credentials_file = credentials_file
        self.keyword_manager = KeywordManager()
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

            next_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Next']]"))
            )
            next_button.click()

            username_field = WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located((By.NAME, "text"))  # Assuming the same field name
            )
            username_field.send_keys(credentials["username"])

            next_button_again = WebDriverWait(self.driver, 7).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Next']]"))
            )
            next_button_again.click()

            password_field = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.send_keys(credentials["password"])

            login_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Log in']]"))
            )
            login_button.click()

            print("Notification: User logged in!\n")
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
        print("Notification: search performed!\n")

        time.sleep(10)  # Wait for the results to load

    def scroll_and_collect_tweets(self, scroll_pause_time=5, max_scrolls=20):
        # Scroll and collect tweets after the search
        for _ in range(max_scrolls):
            time.sleep(scroll_pause_time)
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, "article")
            for tweet in tweet_elements:
                tweet_text = tweet.text
                if tweet_text not in self.tweets:
                    self.tweets.append(tweet_text)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def close(self):
        self.driver.quit()

    def save_tweets(self, filename="tweets.json"):
        # Create the data_set directory if it doesn't exist
        data_set_path = Path("data_set")
        data_set_path.mkdir(exist_ok=True)

        # Save tweets to a temporary file in the data_set folder
        file_path = data_set_path / filename
        with file_path.open('w', encoding='utf-8') as f:
            json.dump(self.tweets, f, ensure_ascii=False, indent=4)
