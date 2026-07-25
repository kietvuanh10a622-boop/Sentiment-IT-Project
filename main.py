import concurrent.futures
import logging
import time

from ai_module.sentiment import apply_sentiment_analysis
from analytics_module.dashboard import generate_analytics_dashboard
from crawlers.bbc import BBCCrawler
from crawlers.vnexpress import VnExpressCrawler
from pipeline.database import export_database_to_files, initialize_database, save_articles_to_db
from pipeline.forecasting import generate_trend_predictions
from pipeline.text_processor import clean_articles_pipeline
from reporting_module.daily_report import generate_daily_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')


def run_parallel_crawlers():
    crawlers = [VnExpressCrawler(), BBCCrawler()]
    all_articles = []

    logging.info('--- STEP 1: STARTING PARALLEL INGESTION ---')
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(crawlers)) as executor:
        future_to_crawler = {executor.submit(crawler.crawl_articles): crawler for crawler in crawlers}
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

    initialize_database()
    raw_data = run_parallel_crawlers()

    if not raw_data:
        logging.warning('No articles were collected. Pipeline stopped.')
        return

    cleaned_data = clean_articles_pipeline(raw_data)
    analyzed_data = apply_sentiment_analysis(cleaned_data)
    save_articles_to_db(analyzed_data)
    export_database_to_files()
    generate_trend_predictions(analyzed_data, output_path='trend_predictions.json', horizon_days=14)
    generate_analytics_dashboard()
    generate_daily_report()

    end_time = time.time()
    logging.info(f'========== PIPELINE COMPLETED IN {end_time - start_time:.2f} SECONDS ==========')


if __name__ == '__main__':
    main()
