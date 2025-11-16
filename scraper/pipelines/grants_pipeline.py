import json
from scraper.crawler import SiteCrawler
from llm.grant_extractor import GrantExtractor
from utils.file_saver import save_json

def run_grants():
    with open("config/websites_grants.json") as f:
        sites = json.load(f)

    extractor = GrantExtractor()

    for site in sites:
        print(f"=== GRANTS: Crawling {site['name']} ===")

        crawler = SiteCrawler(site["domain"], site["start_url"])
        crawler.crawl()

        text = crawler.get_text()
        grants = extractor.extract(text)

        save_json("output/grants/", grants)
