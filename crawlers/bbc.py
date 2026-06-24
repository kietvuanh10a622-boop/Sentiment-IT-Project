# crawlers/bbc.py
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler

class BBCCrawler(BaseCrawler):  # <-- Đảm bảo viết HOA 3 chữ BBC đầu tiên
    """Crawler cho trang động dùng Selenium"""
    def __init__(self):
        super().__init__(base_url="https://www.bbc.com/news", source_name="BBC")

    def crawl_articles(self):
        logging.info(f"Đang thu thập: {self.source_name} (Trang động Selenium)...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

        driver = webdriver.Chrome(options=chrome_options)
        articles = []

        try:
            driver.get(self.base_url)
            time.sleep(4)
            
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