import scrapy
from scrapy.crawler import CrawlerProcess

from bs4 import BeautifulSoup

import nltk

import spacy
import psycopg2

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options


# initializing nltk resource
nltk.download("punkt")
nltk.download("words")

# initializing spaCy
nlp = spacy.load("en_core_web_sm")


# postgreSQL database
class InappropriateWordsDatabase:
    def __init__(self, database_url):
        self.conn = psycopg2.connect(database_url)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inappropriate_words (
                id SERIAL PRIMARY KEY,
                word TEXT UNIQUE
            )
        """
        )
        self.conn.commit()

    def add_word(self, word):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO inappropriate_words (word) VALUES (%s)", (word,)
            )
            self.conn.commit()
        except psycopg2.IntegrityError:
            # Word already exists
            pass

    def get_inappropriate_words(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT word FROM inappropriate_words")
        return [row[0] for row in cursor.fetchall()]


# scrapy spider
class InappropriateWordsSpider(scrapy.Spider):
    name = "inappropriate_words"
    start_urls = ["target url"]

    def parse(self, response):
        soup = BeautifulSoup(response.body, "html.parser")
        words = [word.strip() for word in soup.get_text().split("\n")]
        yield {"words": words}


# Selenium - web interaction
def scrape_web_content(url):
    # initializing selenium webdriver for firefox
    firefox_options = Options()
    driver = Firefox(executable_path="path to geckodriver", options=firefox_options)
    driver.get(url)

    # Extract the webpage's HTML source using Selenium
    html_source = driver.page_source
    driver.quit()  # Close the WebDriver

    return html_source


# NLP filter
class ContentFilter:
    def __init__(self, database):
        self.inappropriate_words = set(database.get_inappropriate_words())

    def filter_content(self, text):
        doc = nlp(text)
        filtered_text = text
        for token in doc:
            if token.lower_ in self.inappropriate_words:
                replacement = "*" * len(token.text)
                filtered_text = filtered_text.replace(token.text, replacement)
        return filtered_text


def update_database(database):
    process = CrawlerProcess()
    process.crawl(InappropriateWordsSpider)
    process.start()

    scraped_data = process.crawlers[0].spider.data
    if "words" in scraped_data:
        words = scraped_data["words"]
        for word in words:
            database.add_word(word)
