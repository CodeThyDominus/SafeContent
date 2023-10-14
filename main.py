import scrapy
from scrapy.crawler import CrawlerProcess
from bs4 import BeautifulSoup
import nltk
import spacy
import psycopg2
import schedule
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# Initializing nltk resource
nltk.download("punkt")
nltk.download("words")

# Initializing spaCy
nlp = spacy.load("en_core_web_sm")


def run_pending():
    while True:
        schedule.run_pending()
        time.sleep(1)


# PostgreSQL database
class InappropriateWordsDatabase:
    def __init__(self, db_url):
        self.conn = psycopg2.connect(db_url)
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


# Scrapy spider
class InappropriateWordsSpider(scrapy.Spider):
    name = "inappropriate_words"
    start_urls = ["https://en.wiktionary.org/wiki/Category:English_swear_words"]

    def parse(self, response):
        # Extract data from the response
        soup = BeautifulSoup(response.body, "html.parser")
        words = [word.strip() for word in soup.get_text().split("\n")]
        yield {"words": words}


# Selenium - web interaction
def scrape_web_content(url, geckodriver_path):
    firefox_options = Options()
    firefox_options.headless = True
    firefox_options.binary_location = "/usr/bin/firefox"  # Specify the path to Firefox if needed

    driver = webdriver.Firefox(options=firefox_options, executable_path=geckodriver_path)

    driver.get(url)
    html_source = driver.page_source
    driver.quit()
    return html_source


# NLP filter
class ContentFilter:
    def __init__(self, db):
        self.inappropriate_words = set(db.get_inappropriate_words())

    def filter_content(self, text):
        doc = nlp(text)
        filtered_text = text
        for token in doc:
            if token.lower_ in self.inappropriate_words:
                replacement = "*" * len(token.text)
                filtered_text = filtered_text.replace(token.text, replacement)
        return filtered_text


# Reporting
""" def send_admin_notification(message):
    admin_email = "thydominus@gmail.com"
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
    server.quit() """


def report_words(content, usr_id):
    with open("log_file.txt", "a") as log_file:
        log_file.write(f"Inappropriate content detected: {content}\n")
        log_file.write(f"User ID: {user_id}\n")

    admin_notification = f"Admin: Inappropriate content detected from User ID {usr_id}.\nContent: {content}"
    # uncomment send_admin notification and insert valid credential or use smptlib with gmail.
    send_admin_notification(admin_notification)


# Function to update the database with the latest
def update_database(db):
    process = CrawlerProcess()
    process.crawl(InappropriateWordsSpider)
    process.start()

    scraped_data = process.crawlers[0].spider.data
    if "words" in scraped_data:
        words = scraped_data["words"]
        for word in words:
            db.add_word(word)


if __name__ == '__main__':
    database_url = "postgresql database url"
    database = InappropriateWordsDatabase(database_url)

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

        run_pending()
