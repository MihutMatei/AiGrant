from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from io import BytesIO
import requests
import time


class SiteCrawler:
    def __init__(self, domain, start_url, driver=None, headless=True):
        self.domain = domain
        self.start_url = start_url
        self.visited = set()
        self.collected_text = []

        # Requests session still used for PDFs or direct downloads
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })

        # Selenium WebDriver
        if driver is not None:
            self.driver = driver
        else:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--window-size=1920,1080")

            # Adjust this if you use Firefox/Edge/etc.
            self.driver = webdriver.Chrome(options=chrome_options)

    def __del__(self):
        # Best-effort cleanup
        try:
            self.driver.quit()
        except Exception:
            pass

    def is_internal(self, url):
        parsed = urlparse(url)
        if parsed.netloc == "" or self.domain in parsed.netloc:
            return True
        return False

    def is_pdf_url(self, url):
        return url.lower().endswith(".pdf")

    def fetch_pdf_and_extract(self, url):
        try:
            res = self.session.get(url, timeout=15)
            res.raise_for_status()
        except Exception as e:
            print(f"[PDF REQUEST ERROR] {url} -> {e}")
            return

        try:
            pdf_text = extract_text(BytesIO(res.content))
            if pdf_text.strip():
                self.collected_text.append(pdf_text)
        except Exception as e:
            print(f"[PDF PARSE ERROR] {url} -> {e}")

    def crawl(self, url=None):
        """
        Single-page crawl, like your original code.
        You can call this repeatedly on multiple URLs or extend it
        to follow links recursively.
        """
        if url is None:
            url = self.start_url

        if url in self.visited:
            return
        self.visited.add(url)

        print(f"[CRAWL] {url}")

        # If this is a PDF, don't even go through Selenium – just download.
        if self.is_pdf_url(url):
            self.fetch_pdf_and_extract(url)
            return

        # Use Selenium to render JS and get final page source
        try:
            self.driver.get(url)
            # crude wait for JS/XHRs; tune or replace with WebDriverWait if needed
            time.sleep(3)
            html = self.driver.page_source
        except TimeoutException:
            print(f"[TIMEOUT] {url}")
            return
        except Exception as e:
            print(f"[SELENIUM ERROR] {url} -> {e}")
            return

        soup = BeautifulSoup(html, "html.parser")

        # Strip non-content tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.extract()

        text = soup.get_text(separator=" ", strip=True)
        if text:
            self.collected_text.append(text)

        # OPTIONAL: follow internal links (uncomment if you want full crawling)
        # for a in soup.find_all("a", href=True):
        #     link = urljoin(url, a["href"])
        #     if self.is_internal(link) and link not in self.visited:
        #         self.crawl(link)

    def get_text(self):
        return "\n\n".join(self.collected_text)
