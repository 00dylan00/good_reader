# Good Reader

<div style="text-align: center;">
    <img src="good_reader.dalle.webp" alt="Good Reader" width="50%" height="50%">
</div>



Good Reader is a program designed to automate the process of retrieving relevant scientific articles, summarizing their content, and then publishing these summaries to Twitter. It consists of two main components: a **Reader** script for article retrieval and summarization, and a **Writer** script for publishing the summaries on Twitter.

## Features

- **Automated Article Retrieval**: Fetches recent articles from PubMed based on specified queries, focusing on bioinformatics, AI in medicine, and related fields.
- **Citation Count Fetching**: Gathers citation counts for each article to prioritize articles of higher impact.
- **Content Summarization**: Uses state-of-the-art NLP models to generate concise summaries of the articles.
- **Automated Tweeting**: Schedules and posts tweets with article titles, summaries, and links to the full texts at randomized times throughout the day.
- **Duplication Avoidance**: Tracks articles that have already been tweeted to avoid repetition.

## Requirements

- Python 3.8+
- Requests
- Pandas
- Tweepy
- Transformers
- Python-dotenv
- Schedule
- XML.etree.ElementTree

## Installation

1. Clone the Good Reader repository.
2. Install required Python packages:

```bash
pip install requests pandas tweepy transformers python-dotenv schedule
```
3. Before using the summarization feature in the Reader script, you need to install the facebook/bart-large-cnn model. You can download or clone it directly from Hugging Face:

```plaintext
https://huggingface.co/facebook/bart-large-cnn/tree/main
```

Ensure the model is correctly placed in a location accessible by the script, or adjust the script to use the model directly from Hugging Face's Transformers library.

4. Create a .env file in the root directory with your Twitter API credentials:
```plaintext
API_KEY=your_api_key
API_KEY_SECRET=your_api_key_secret
BEARER_TOKEN=your_bearer_token
ACCESS_TOKEN=your_access_token
ACCESS_TOKEN_SECRET=your_access_token_secret
```

## Usage
### Reader Script
1. Set up your query by modifying the journals list and other variables as needed.
2. Run the Reader script to fetch, summarize, and store articles:

```bash
python reader.py
```
This will generate a CSV file with summarized articles ready for tweeting.


### Writer Script

Ensure the .env file with Twitter API credentials is correctly set up.
Run the Writer script to start tweeting the article summaries:

```bash
python writer.py
```

The script will automatically tweet at randomized times throughout the day and track which articles have been tweeted to avoid duplication.
## Configuration
* Article Retrieval: Adjust the days_ago and n_articles parameters in the fetch_recent_papers function to control the date range and number of articles fetched.
* Summarization: Modify the summarization model and parameters in the Reader script as needed.
* Tweeting Schedule: Change the n_daily_tweets variable in the Writer script to set the number of tweets per day.

## Note

Ensure compliance with Twitter's API usage policies and rate limits when using the Writer script. The program is intended for educational and research purposes.

Good Reader simplifies the process of sharing the latest scientific discoveries in bioinformatics and AI with a broader audience on social media, making cutting-edge research accessible to all.

