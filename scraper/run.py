import os
from dotenv import load_dotenv

# Load .env from the scraper directory
SCRAPER_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(SCRAPER_DIR)
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from pipelines.grants_pipeline import run_grants
from pipelines.acc_pipeline import run_accelerators
from pipelines.vc_pipeline import run_vc

if __name__ == "__main__":
    run_grants()
    run_accelerators()
    run_vc()
