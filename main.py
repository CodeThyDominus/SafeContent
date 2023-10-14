import scrapy
from scrapy.crawler import CrawlerProcess

from bs4 import BeautifulSoup

import nltk

import spacy
import psycopg2
import schedule

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


# reporting
def send_admin_notification(message):
    admin_email = "admin@gmail.com"
    subject = "Inappropriate Content Report"

    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg.set_content(message)
    msg["Subject"] = subject
    msg["From"] = "your_app@example.com"
    msg["To"] = admin_email

    server = smtplib.SMTP("smtp.example.com", 587)
    server.starttls()
    server.login("your_app@example.com", "your_password")
    server.send_message(msg)
    server.quit()


def report_words(content, user_id):
    with open("log_file.txt", "a") as log_file:
        log_file.write(f"Inappropriate content detected: {content}\n")
        log_file.write(f"User ID: {user_id}\n")

    admin_notification = f"Admin: Inappropriate content detected from User ID {user_id}.\nContent: {content}"
    send_admin_notification(admin_notification)


# Function to update the database with the latest


def update_database(database):
    process = CrawlerProcess()
    process.crawl(InappropriateWordsSpider)
    process.start()

    scraped_data = process.crawlers[0].spider.data
    if "words" in scraped_data:
        words = scraped_data["words"]
        for word in words:
            database.add_word(word)


def schedule_updates():
    update_interval = 1  # in days
    schedule.every(update_interval).days.do(update_database)


if __name__ == '__main__':
    database_url = "postgresql database url"
    database = InappropriateWordsDatabase(database_url)

    schedule_updates()

    content_filter = ContentFilter(database)

    while True:
        user_id = input("Enter your user ID: ")
        user_input = input("Enter your text: ")
        filtered_input = content_filter.filter_content(user_input)

        if filtered_input != user_input:
            print("Warning: Inappropriate content detected. Please review your text.")
            print("Filtered Text:", filtered_input)

            report_words(user_input, user_id)
        else:
            print("Your text is clean.")

        # Run scheduled jobs
        schedule.run_pending()