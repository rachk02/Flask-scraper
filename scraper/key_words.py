import json
from datetime import datetime

class KeywordManager:
    def __init__(self, filename='keywords.json'):
        self.filename = filename

    def get_keyword(self):
        # Prompt the user for a keyword
        keyword = input("Please enter a keyword (can include hashtags): ")
        return keyword

    def store_keyword(self, keyword):
        # Load existing keywords from the JSON file
        try:
            with open(self.filename, 'r') as file:
                keywords_data = json.load(file)
        except FileNotFoundError:
            keywords_data = []

        # Create a new entry
        new_entry = {
            "id": len(keywords_data) + 1,
            "keyword": keyword,
            "timestamp": datetime.now().isoformat()
        }
        keywords_data.append(new_entry)

        # Save the updated keywords back to the JSON file
        with open(self.filename, 'w') as file:
            json.dump(keywords_data, file, indent=4)
