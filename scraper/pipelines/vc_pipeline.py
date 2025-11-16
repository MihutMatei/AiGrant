import json
from scraper.crawler import SiteCrawler
from llm.vc_extractor import VCExtractor
from utils.file_saver import save_json

def run_vc():
    with open("config/websites_vc.json") as f:
        sites = json.load(f)

    extractor = VCExtractor()

    for site in sites:
        print(f"=== VC: Crawling {site['name']} ===")

        crawler = SiteCrawler(site["domain"], site["start_url"])
        crawler.crawl()

        text = crawler.get_text()
        vcs = extractor.extract(text)

        save_json("output/vcs/", vcs)
