import re
import json
from pathlib import Path

# Function to convert tweet string to a structured dictionary
def parse_tweet(keyword, filename='tweets.json'):
    # Load the list of tweets from a JSON file
    file_path = Path("data_set") / filename
    with file_path.open('r', encoding='utf-8') as f:
        tweets = json.load(f)

    structured_tweets = []  # List to store structured tweets

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
            "keyword": keyword,
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
                tweet_data["mentioned_account"] = lines[i + 1].strip()

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
            tweet_data["reposts"] = reposts

        tweet_data["content"] = tweet_data["content"].replace('\\', '')

        structured_tweets.append(tweet_data)  # Append the structured tweet data to the list

    return structured_tweets  # Return the list of structured tweets

# Save structured tweets to file
def structure_tweets(keyword, filename='struct_tweets.json'):
    # Ensure the data_set directory exists
    data_set_path = Path("data_set")
    data_set_path.mkdir(exist_ok=True)

    # Call the parse_tweet function to get structured tweets
    structured_tweets = parse_tweet(keyword)

    # Full path for the output file
    full_path = data_set_path / filename

    # Check if the file already exists and is not empty
    existing_tweets = []
    if full_path.exists() and full_path.stat().st_size > 0:  # Check if file is not empty
        with full_path.open('r', encoding='utf-8') as f:
            try:
                existing_tweets = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: '{filename}' is corrupted or empty. Starting with an empty list.")
                existing_tweets = []

    # Only combine if structured_tweets is not empty
    if structured_tweets:
        all_tweets = existing_tweets + structured_tweets
    else:
        all_tweets = existing_tweets

    # Write the combined list of structured tweets back to the file
    with full_path.open('w', encoding='utf-8') as f:
        json.dump(all_tweets, f, ensure_ascii=False, indent=4)
