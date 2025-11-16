import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pdfminer.high_level import extract_text
from io import BytesIO


class SiteCrawler:
    def __init__(self, domain, start_url):
        self.domain = domain
        self.start_url = start_url
        self.visited = set()
        self.collected_text = []

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })

    def is_internal(self, url):
        parsed = urlparse(url)
        if parsed.netloc == "" or self.domain in parsed.netloc:
            return True
        return False

    def is_pdf(self, response, url):
        # Content-Type header is best
        if "application/pdf" in response.headers.get("Content-Type", ""):
            return True
        # URL extension fallback
        return url.lower().endswith(".pdf")

    def crawl(self, url=None):
        if url is None:
            url = self.start_url

        if url in self.visited:
            return
        self.visited.add(url)

        print(f"[CRAWL] {url}")

        try:
            res = self.session.get(url, timeout=10)
            res.raise_for_status()
        except:
            return

        # ----- PDF Support -----
        if self.is_pdf(res, url):
            try:
                pdf_text = extract_text(BytesIO(res.content))
                if pdf_text.strip():
                    self.collected_text.append(pdf_text)
            except Exception as e:
                print(f"[PDF ERROR] {e}")
            return
        # ------------------------

        # HTML handling
        html = res.text
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.extract()

        text = soup.get_text(separator=" ", strip=True)
        if text:
            self.collected_text.append(text)

    def get_text(self):
        return "\n\n".join(self.collected_text)
