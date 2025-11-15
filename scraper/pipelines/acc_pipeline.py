import json
from scraper.crawler import SiteCrawler
from llm.acc_extractor import AcceleratorExtractor
from utils.file_saver import save_json

def run_accelerators():
    with open("config/websites_acc.json") as f:
        sites = json.load(f)

    extractor = AcceleratorExtractor()

    for site in sites:
        print(f"=== ACCELERATORS: Crawling {site['name']} ===")

        crawler = SiteCrawler(site["domain"], site["start_url"])
        crawler.crawl()

        text = crawler.get_text()
        accelerators = extractor.extract(text)

        save_json("output/accelerators/", accelerators)
