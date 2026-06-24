# main.py
import logging
import time
import concurrent.futures

# 1. Import các Module từ thư mục crawlers (SP1)
from crawlers.vnexpress import VnExpressCrawler
from crawlers.bbc import BBCCrawler

# 2. Import các Module từ thư mục pipeline (SP2 & SP3)
from pipeline.text_processor import clean_articles_pipeline
from pipeline.database import initialize_database, save_articles_to_db, export_database_to_files

# 3. Import Module AI (SP4)
from ai_module.sentiment import apply_sentiment_analysis

# 4. Import Module Analytics & Dashboard (SP5)
from analytics_module.dashboard import generate_analytics_dashboard

# 5. Import Module Reporting (SP6 - MỚI THÊM)
from reporting_module.daily_report import generate_daily_report

# Cấu hình log để theo dõi toàn bộ hệ thống
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

def run_parallel_crawlers():
    """
    Hàm điều phối đa luồng (Multi-threading) từ SP1
    """
    crawlers = [VnExpressCrawler(), BBCCrawler()]
    all_articles = []

    logging.info("--- BƯỚC 1: KHỞI ĐỘNG CÀO TIN ĐA LUỒNG (SP1) ---")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(crawlers)) as executor:
        future_to_crawler = {executor.submit(crawler.crawl_articles): crawler for crawler in crawlers}

        for future in concurrent.futures.as_completed(future_to_crawler):
            crawler = future_to_crawler[future]
            try:
                data = future.result()
                all_articles.extend(data)
            except Exception as exc:
                logging.error(f"Crawler {crawler.source_name} gặp lỗi nghiêm trọng: {exc}")
                
    return all_articles

def main():
    start_time = time.time()
    logging.info("========== KHỞI ĐỘNG HỆ THỐNG NEWS AGGREGATOR ==========")
    
    # BƯỚC A: Khởi tạo cấu trúc Database (SP3)
    initialize_database()
    
    # BƯỚC B: Chạy hệ thống thu thập dữ liệu đa luồng (SP1)
    raw_data = run_parallel_crawlers()
    
    if not raw_data:
        logging.warning("Không thu thập được dữ liệu nào. Hệ thống tạm dừng.")
        return

    # BƯỚC C: Truyền dữ liệu thô sang đường ống làm sạch (SP2)
    cleaned_data = clean_articles_pipeline(raw_data)
    
    # BƯỚC C2 (SP4): Áp dụng AI để phân tích cảm xúc Đa ngôn ngữ
    analyzed_data = apply_sentiment_analysis(cleaned_data)
    
    # BƯỚC D: Lưu trữ dữ liệu đã có điểm cảm xúc vào Database SQLite (SP3)
    save_articles_to_db(analyzed_data)
    
    # BƯỚC E: Xuất file backup JSON/CSV để dự phòng (SP3)
    export_database_to_files()
    
    # BƯỚC F (SP5): Phân tích dữ liệu bằng Pandas và xuất Dashboard (Matplotlib)
    generate_analytics_dashboard()
    
    # BƯỚC G (MỚI - SP6): Xuất báo cáo ngày & Tự động viết nháp Technical Report
    generate_daily_report()
    
    end_time = time.time()
    logging.info(f"========== HỆ THỐNG HOÀN THÀNH TOÀN BỘ PHIÊN TRONG {end_time - start_time:.2f} GIÂY ==========")

if __name__ == "__main__":
    main()