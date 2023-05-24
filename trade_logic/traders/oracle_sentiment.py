import json
import os
import nltk
nltk.download('vader_lexicon')  ## Download this if you are running the script for the first time
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import openai
import requests
from trade_logic.traders.oracle_sentiment_utils import *
from schemas.enums.karar import Karar


class OracleSentimentStrategy:
    def __init__(self, config) -> None:
        self.config = config
        # TODO:: business and tech category loop
        # TODO:: run this daily trigger discord webhook
        self.news_api_top_headlines_url = 'https://newsapi.org/v2/top-headlines'
        self.news_api_everything_url = 'https://newsapi.org/v2/everything'
        openai.api_key = os.getenv("OPENAI_APIKEY")
        self.client = openai
        self.karar = 0

    def get_news_from_news_api(self, url, params):
        response = requests.get(url, params=params)
        data = json.loads(response.text)
        titles = []
        for article in data.get("articles"):
            desc = article.get('description', '')
            titles.append(desc if desc else '')
        return titles

    def create_sentiment_analysis(self, summary):
        sia = SentimentIntensityAnalyzer()
        sentiment = sia.polarity_scores(summary)
        self.sentiment_compound = sentiment['compound']
        # print(summary)
        #print('Compound:', sentiment['compound'], 'Positive:', sentiment['pos'], 'Negative:', sentiment['neg'], 'Neutral:', sentiment['neu'])
        if sentiment['compound'] >= 0.1:
            return 1
        elif sentiment['compound'] <= -0.1:
            return -1
        else:
            return 0

    def run(self, start_date):
        params = {
            # 'country': 'us',  ## try commenting this out for analyzing global headlines
            'q': 'crypto',
            'searchIn': 'title,description',
            'from': datetime.strftime(start_date - timedelta(days=1), '%Y-%m-%d'),
            'to': datetime.strftime(start_date, '%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'popularity',
            'apiKey': os.getenv("NEWSAPI_KEY"),
            'pageSize': 80,
            'page': 1
        }
        titles_array = self.get_news_from_news_api(self.news_api_everything_url, params)
        titles_array = ' '.join(titles_array)
        # translated_titles = translate_titles(self, ' '.join(titles_array))
        translated_titles = generate_summary(self, titles_array)
        result = self.create_sentiment_analysis(translated_titles)
        self.karar = Karar(result)
