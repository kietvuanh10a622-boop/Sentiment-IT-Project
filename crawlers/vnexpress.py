# crawlers/vnexpress.py
import logging
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler

class VnExpressCrawler(BaseCrawler):  # Viết chính xác từng ký tự hoa thường
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