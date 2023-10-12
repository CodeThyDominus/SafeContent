# SafeContent
content filtering system which will report and restrict use of illcit words, phrases, slangs, images, videos, etc

# Using Chromedriver
To use Chome(chromedriver) instead of firefox(geckodriver)
Replace
`firefox_options = Options(
driver = Firefox(executable_path='path to geckodriver', options=firefox_options)`
with
`driver = webdriver.Chrome(executable_path='path to chromedriver.exe')`

# To access scraping and web interaction in headless mode (no window mode)
Use,
`firefox_options.headless = True`

