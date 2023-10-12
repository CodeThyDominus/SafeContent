import scrapy
from bs4 import BeautifulSoup
from selenium import webdriver


# scrapy spider
class InappropriateWordsSpider(scrapy.Spider):
    name = 'inappropriate_words'
    start_urls = ['https://www.noswearing.com/dictionary']

    def parse(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        words = [word.strip() for word in soup.get_text().split('\n')]
        yield {'words': words}

    # selenium for web interaction
    def scrape_web_content(url):
        # initializing Selenium webdriver
        driver = webdriver.Chrome(executable_path='webdriver path')
        driver.get(url)

        # extracting the webpage's HTML source
        html_source = driver.page_source
        driver.quit()  # Close the WebDriver

        return html_source
