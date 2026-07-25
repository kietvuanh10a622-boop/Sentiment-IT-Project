import concurrent.futures
import logging
import time

from sentiment import apply_sentiment_analysis
from bbc import BBCCrawler
from vnexpress import VnExpressCrawler
from database import export_database_to_files, initialize_database, save_articles_to_db
from forecasting import generate_trend_predictions
from text_processor import clean_articles_pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')


def run_parallel_crawlers():
    crawlers = [VnExpressCrawler(), BBCCrawler()]
    all_articles = []

    logging.info('--- STEP 1: STARTING PARALLEL INGESTION ---')
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(crawlers)) as executor:
        future_to_crawler = {executor.submit(crawler.crawl_articles, max_age_days=2): crawler for crawler in crawlers}
        for future in concurrent.futures.as_completed(future_to_crawler):
            crawler = future_to_crawler[future]
            try:
                data = future.result() or []
                if not data:
                    logging.warning(f'No data returned from {crawler.source_name}; using fallback cache.')
                all_articles.extend(data)
            except Exception as exc:
                logging.critical(f'CRITICAL ERROR: {crawler.source_name} failed: {exc}')

    return all_articles


def main():
    start_time = time.time()
    logging.info('========== STARTING NEWS AGGREGATOR PIPELINE ==========')

    initialize_database(clear_existing=True)
    raw_data = run_parallel_crawlers()

    if not raw_data:
        logging.warning('No articles were collected. Pipeline stopped.')
        return

    cleaned_data = clean_articles_pipeline(raw_data)
    analyzed_data = apply_sentiment_analysis(cleaned_data)
    save_articles_to_db(analyzed_data)
    export_database_to_files()
    generate_trend_predictions(analyzed_data, output_path='trend_predictions.json', horizon_days=14)

    end_time = time.time()
    logging.info(f'========== PIPELINE COMPLETED IN {end_time - start_time:.2f} SECONDS ==========')


if __name__ == '__main__':
    main()
