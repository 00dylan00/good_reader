"""Writer

Structure:
    1. Imports, Variables, Functions
    2. Tweet Papers
"""

# 1. Imports, Variables, Functions
# imports
import schedule
import time
import random
import pandas as pd, json, os
from dotenv import load_dotenv
import os
import tweepy
import logging
from datetime import datetime
logging.basicConfig(level=logging.INFO)

# variables
n_daily_tweets = random.choice([1,2,3])  # Number of tweets per day
n_daily_tweets = 3

# functions
def load_tweeted_pmids():
    path_tweeted_pmids = os.path.join("..","results","tweeted_pmids.json")

    try:
        with open(path_tweeted_pmids, 'r') as f:
            return set(json.load(f))  # Load and convert list back to set
    except FileNotFoundError:
        return set()  # Return an empty set if the file doesn't exist

def save_tweeted_pmids(tweeted_pmids):
    path_tweeted_pmids = os.path.join("..", "results", "tweeted_pmids.json")
    with open(path_tweeted_pmids, "w") as f:
        # Ensure all elements are converted to Python native int before serialization
        tweeted_pmids_list = [int(pmid) for pmid in tweeted_pmids]
        json.dump(tweeted_pmids_list, f)


def tweet_paper():
    """Tweet Paper
    Structure:
        1. Load Data
        2. Tweet Paper
        3. Save Data"""

    # 1. Load Data

    load_dotenv()  # Load environment variables from .env file

    api_key = os.getenv("API_KEY")
    api_key_secret = os.getenv("API_KEY_SECRET")
    bearer_token = os.getenv("BEARER_TOKEN")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
    path_csv = os.path.join("..","results","papers_to_tweet.csv")

    global df_papers  # Ensure we're modifying the global DataFrame

    # Load the latest DataFrame and tweeted_pmids at the beginning of each call
    df_papers = pd.read_csv(path_csv)
    tweeted_pmids = load_tweeted_pmids()

    # check if the papers haven't been tweeted already
    available_papers = df_papers[~df_papers['pmid'].isin(tweeted_pmids)]
    if available_papers.empty:
        logging.info("All papers have been tweeted.")
        return
    paper = available_papers.sample(1).iloc[0]  # Randomly select an untweeted paper

    min_abstract_length = 60
    # check if the paper has an abstract
    if isinstance(paper["abstract_summary"], str):

        # check there is room for abstract ! ! !
        tweet_content = f"{paper['title']}\n{paper['doi_link']}"

        # check if there is room for abstract
        if len(tweet_content) < 280 - min_abstract_length:
            # There is room for an abstract ! ! !
            room_available = 280 - len(tweet_content) - 2  # +2 \n\n
            # check if there is room for entire abstract summary
            if len(paper["abstract_summary"]) < room_available:
                logging.info("Title + abstract summary")
                tweet_content = f"{paper['title']}\n\n{paper['abstract_summary']}\n{paper['doi_link']}"
            # check if there is room for a truncated abstract summary
            else:
                logging.info("Title + truncated abstract summary")
                tweet_content = f"{paper['title']}\n\n{paper['abstract_summary'][:room_available-5]}...\n{paper['doi_link']}"

        else:
            # check if there is room for a title ! ! !

            if len(tweet_content) < 280:
                logging.info("Title")
                # redundant
                tweet_content = f"{paper['title']}\n{paper['doi_link']}"
            else:
                logging.info("Truncated title")
                space_left = 280 - len(tweet_content)
                tweet_content = (
                    f"{paper['title'][:space_left-4]}...\n{paper['doi_link']}"
                )

        assert (
            len(tweet_content) <= 280
        ), f"Tweet content too long: {len(tweet_content)} characters"

    # If the paper doesn't have an abstract, tweet the title and DOI link
    else:
        # check there is room for abstract ! ! !
        tweet_content = f"{paper['title']}\n{paper['doi_link']}"
        # check if there is room for a title ! ! !
        if len(tweet_content) < 280:
            logging.info("Title")

            # redundant
            tweet_content = f"{paper['title']}\n{paper['doi_link']}"
        else:
            logging.info("Truncated title")
            space_left = 280 - len(tweet_content)
            tweet_content = f"{paper['title'][:space_left-4]}...\n{paper['doi_link']}"

        assert (
            len(tweet_content) <= 280
        ), f"Tweet content too long: {len(tweet_content)} characters"



    # 2. Tweet Paper
    # Attempt to tweet the content
    try:
        # Authentication
        client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_key_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        )
        auth = tweepy.OAuth1UserHandler(
        api_key, api_key_secret, access_token, access_token_secret
        )
        api = tweepy.API(auth)

        # posting tweet
        client.create_tweet(text=tweet_content)
        logging.info(f"Successfully tweeted: {tweet_content}")

        # 3. Save Data
        # updated the tweeted_pmids
        tweeted_pmids.add(paper['pmid'])  # Mark this paper as tweeted
        save_tweeted_pmids(tweeted_pmids)  # Save the updated set of tweeted PMIDs

        # Remove the tweeted paper from the DataFrame and save the update
        df_papers = df_papers[~df_papers['pmid'].isin(tweeted_pmids)]
        df_papers.to_csv(path_csv, index=False)

    except Exception as e:
        logging.info(f"Failed to tweet: {e}")

def schedule_tweets(n_daily_tweets=5):
    current_time = datetime.now()
    for _ in range(n_daily_tweets):
        attempts = 0
        while True:
            hour = random.randint(8, 17)
            minute = random.randint(0, 59)
            schedule_time_str = f"{hour:02d}:{minute:02d}"
            schedule_time = datetime.strptime(f"{current_time.strftime('%Y-%m-%d')} {schedule_time_str}", '%Y-%m-%d %H:%M')

            if schedule_time > datetime.now():  # Always compare to the current moment
                schedule.every().day.at(schedule_time_str).do(tweet_paper).tag('daily-tweets')
                logging.info(f"Scheduled a tweet at {schedule_time_str}")
                break
            else:
                attempts += 1
                # logging.info(f"Time {schedule_time_str} has already passed. Picking another time.")
                if attempts > 1000:  # Prevent infinite loop
                    logging.warning("Too many failed attempts to find a future time. Skipping this tweet.")
                    break

def reset_and_schedule_tweets():
    # Clearing schedules tagged as 'daily-tweets'
    schedule.clear('daily-tweets')
    logging.info("Cleared all scheduled tweets.")
    schedule_tweets()

# 2.
# Schedule the reset function to run daily at 00:01
schedule.every().day.at("00:01").do(reset_and_schedule_tweets)

# Start by scheduling today's tweets
reset_and_schedule_tweets()

# Main loop to keep the script running and handle scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(1)

