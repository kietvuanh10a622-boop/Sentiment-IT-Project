import time
import logging
import concurrent.futures
from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Cấu hình logging để theo dõi tiến độ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

# ==========================================
# BƯỚC 1: LỚP TRỪU TƯỢNG (ABSTRACT BASE CLASS)
# ==========================================
class BaseCrawler(ABC):
    def __init__(self, base_url, source_name):
        self.base_url = base_url
        self.source_name = source_name

    def fetch_html(self, url):
        """Hàm dùng chung để tải mã HTML cho các trang tĩnh"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Lỗi tải HTML từ {url}: {e}")
            return None

    @abstractmethod
    def crawl_articles(self):
        """Bắt buộc các class con phải định nghĩa cách cào bài"""
        pass

# ==========================================
# BƯỚC 2 & 3: CÁC CLASS CON KẾ THỪA
# ==========================================
class VnExpressCrawler(BaseCrawler):
    """Crawler cho trang tĩnh dùng BeautifulSoup"""
    def __init__(self):
        super().__init__(base_url="https://vnexpress.net", source_name="VnExpress")

    def crawl_articles(self):
        logging.info(f"Đang thu thập: {self.source_name} (Trang tĩnh)...")
        html = self.fetch_html(self.base_url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        articles = []

        # Bóc tách thẻ h3 chứa class 'title-news'
        for item in soup.find_all('h3', class_='title-news'):
            a_tag = item.find('a')
            if a_tag and a_tag.get('href') and a_tag.get('title'):
                title = a_tag.get('title').strip()
                link = a_tag.get('href').strip()
                
                if link.startswith("https://"):
                    articles.append({
                        'title': title,
                        'link': link,
                        'source': self.source_name
                    })
        
        logging.info(f"Xong {self.source_name}: {len(articles)} bài báo.")
        return articles

class BBCCrawler(BaseCrawler):
    """Crawler cho trang động dùng Selenium"""
    def __init__(self):
        super().__init__(base_url="https://www.bbc.com/news", source_name="BBC")

    def crawl_articles(self):
        logging.info(f"Đang thu thập: {self.source_name} (Trang động Selenium)...")
        
        # Cấu hình chạy ngầm (Headless)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

        driver = webdriver.Chrome(options=chrome_options)
        articles = []

        try:
            driver.get(self.base_url)
            time.sleep(4) # Chờ JS render
            
            # Bóc tách bằng CSS Selector
            elements = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='edgel-text-container'] a")
            
            for el in elements:
                title = el.text.strip()
                link = el.get_attribute('href')
                
                if title and link and link.startswith("https://"):
                    article_data = {
                        'title': title,
                        'link': link,
                        'source': self.source_name
                    }
                    if article_data not in articles:
                        articles.append(article_data)
                        
        except Exception as e:
            logging.error(f"Lỗi Selenium tại {self.source_name}: {e}")
        finally:
            driver.quit()
            
        logging.info(f"Xong {self.source_name}: {len(articles)} bài báo.")
        return articles

# ==========================================
# BƯỚC 4: ĐỘNG CƠ ĐA LUỒNG (MULTI-THREADING)
# ==========================================
def run_parallel_crawlers():
    crawlers = [VnExpressCrawler(), BBCCrawler()]
    all_articles = []

    logging.info("=== KHỞI ĐỘNG CÀO ĐA LUỒNG ===")
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(crawlers)) as executor:
        future_to_crawler = {executor.submit(crawler.crawl_articles): crawler for crawler in crawlers}

        for future in concurrent.futures.as_completed(future_to_crawler):
            crawler = future_to_crawler[future]
            try:
                data = future.result()
                all_articles.extend(data)
            except Exception as exc:
                logging.error(f"{crawler.source_name} bị lỗi: {exc}")

    end_time = time.time()
    logging.info(f"Hoàn tất trong: {end_time - start_time:.2f} giây. Tổng bài: {len(all_articles)}")
    
    return all_articles

if __name__ == "__main__":
    results = run_parallel_crawlers()
    
    print("\n--- Preview 3 bài báo đầu tiên ---")
    for idx, article in enumerate(results[:3], 1):
        print(f"{idx}. [{article['source']}] {article['title']}")
        print(f"   Link: {article['link']}\n")


import sqlite3
import json
import csv
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# ==========================================
# SP2: ADVANCED FUNCTIONS (DECORATORS & TEXT PROCESSING)
# ==========================================

# 1. Decorator: Đo lường thời gian thực thi của hàm
def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logging.info(f"Hàm '{func.__name__}' chạy mất {end - start:.4f} giây.")
        return result
    return wrapper

@timing_decorator
def clean_articles_pipeline(raw_articles):
    """Sử dụng lambda, map và filter để làm sạch dữ liệu"""
    logging.info("Bắt đầu đường ống làm sạch dữ liệu (SP2)...")
    
    # Lọc: Bỏ qua các bài báo không có tiêu đề (title rỗng)
    valid_articles = list(filter(lambda x: len(x.get('title', '').strip()) > 0, raw_articles))
    
    # Map: Làm sạch khoảng trắng thừa và chuẩn hóa chuỗi
    def clean_text(article):
        article['title'] = " ".join(article['title'].split())
        article['sentiment_score'] = None # Chuẩn bị sẵn cột trống cho SP4 (AI)
        return article
        
    cleaned_articles = list(map(clean_text, valid_articles))
    logging.info(f"Đã làm sạch {len(cleaned_articles)} bài báo hợp lệ.")
    return cleaned_articles


# ==========================================
# SP3: SQLITE DATABASE & FILE EXPORT
# ==========================================

@timing_decorator
def setup_database_and_save(articles, db_name="news_database.db"):
    """Tạo bảng SQLite và lưu trữ dữ liệu"""
    logging.info("Khởi tạo kết nối cơ sở dữ liệu SQLite (SP3)...")
    
    # Kết nối SQLite (tự động tạo file nếu chưa có)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Thiết kế schema chuẩn hóa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            category TEXT,
            sentiment_score REAL
        )
    ''')
    
    # Chèn dữ liệu (Sử dụng INSERT OR IGNORE để không bị lỗi nếu trùng link)
    insert_count = 0
    for art in articles:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO Articles (title, link, source, category, sentiment_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (art['title'], art['link'], art.get('source', 'Unknown'), art.get('category', 'General'), art['sentiment_score']))
            if cursor.rowcount > 0:
                insert_count += 1
        except sqlite3.Error as e:
            logging.error(f"Lỗi database khi chèn bài báo: {e}")
            
    conn.commit()
    conn.close()
    logging.info(f"Đã lưu thành công {insert_count} bài báo MỚI vào database.")

@timing_decorator
def export_to_files(articles):
    """Xuất file backup ra định dạng JSON và CSV"""
    # Xuất JSON
    with open('articles_backup.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
        
    # Xuất CSV
    if articles:
        keys = articles[0].keys()
        with open('articles_backup.csv', 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(articles)
    logging.info("Đã xuất bản sao lưu ra file JSON và CSV.")


# ==========================================
# KHU VỰC CHẠY TÍCH HỢP
# ==========================================
if __name__ == "__main__":
    # GIẢ LẬP DỮ LIỆU ĐẦU VÀO TỪ SP1 (news_crawler.py)
    mock_raw_data_from_sp1 = [
        {'title': '   VN-Index tăng vọt   ', 'link': 'https://vnexpress.net/1', 'source': 'VnExpress'},
        {'title': '', 'link': 'https://vnexpress.net/loi', 'source': 'VnExpress'}, # Sẽ bị loại bỏ bởi filter
        {'title': ' Tech giants face new rules', 'link': 'https://bbc.com/2', 'source': 'BBC'}
    ]
    
    # 1. Chạy đường ống SP2
    clean_data = clean_articles_pipeline(mock_raw_data_from_sp1)
    
    # 2. Chạy lưu trữ SP3
    setup_database_and_save(clean_data)
    export_to_files(clean_data)
    
    print("\n[Hoàn tất Phase 1] Dữ liệu đã sẵn sàng trong file news_database.db!")