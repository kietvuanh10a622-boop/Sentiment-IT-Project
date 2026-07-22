import time
import logging
import concurrent.futures
from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import datetime

# Cấu hình logging để theo dõi tiến độ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

# ==========================================
# BƯỚC 1: LỚP TRỪU TƯỢNG (ABSTRACT BASE CLASS)
# ==========================================
class BaseCrawler(ABC):
    FALLBACK_CACHE = {
        "VnExpress": [
            {
                "title": "TSMC mở rộng năng lực sản xuất chip AI",
                "link": "https://vnexpress.net/fallback-tsmc",
                "source_name": "VnExpress",
                "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                "content": "TSMC mở rộng năng lực sản xuất chip AI nhằm đáp ứng nhu cầu toàn cầu." 
            }
        ],
        "BBC": [
            {
                "title": "Export controls đẩy căng thẳng thị trường bán dẫn toàn cầu",
                "link": "https://www.bbc.com/fallback-chip-export",
                "source_name": "BBC",
                "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                "content": "BBC fallback story about export controls and semiconductor geopolitics."
            }
        ]
    }

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

    def load_fallback_articles(self):
        """Load fallback articles when scraping fails."""
        cached = self.FALLBACK_CACHE.get(self.source_name, [])
        if cached:
            logging.warning(f"Sử dụng dữ liệu dự phòng cho {self.source_name}: {len(cached)} bài.")
            return [dict(item) for item in cached]

        fallback_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fallback_cache.json')
        if os.path.exists(fallback_path):
            try:
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    return [article for article in raw if article.get('source_name') == self.source_name]
            except Exception as e:
                logging.error(f"Không đọc được fallback_cache.json: {e}")
        return []

    def parse_published_date(self, soup, fallback_date=None):
        """Extract a published date from article markup, with safe fallback."""
        fallback_date = fallback_date or datetime.datetime.utcnow().strftime('%Y-%m-%d')
        date_candidates = []
        for selector, attr in [
            ('meta[property="article:published_time"]', 'content'),
            ('meta[name="pubdate"]', 'content'),
            ('meta[name="publish-date"]', 'content'),
            ('meta[name="DC.date.issued"]', 'content'),
            ('time[datetime]', 'datetime'),
            ('span.date', 'datetime'),
            ('meta[name="date"]', 'content')
        ]:
            el = soup.select_one(selector)
            if el and el.get(attr):
                date_candidates.append(el.get(attr).strip())

        if not date_candidates:
            return fallback_date

        for candidate in date_candidates:
            candidate = candidate.split('T')[0]
            match = re.search(r'(\d{4}-\d{2}-\d{2})', candidate)
            if match:
                return match.group(1)
            try:
                parsed = datetime.datetime.fromisoformat(candidate)
                return parsed.strftime('%Y-%m-%d')
            except Exception:
                continue

        return fallback_date

    def extract_article_content(self, soup):
        """Extract the article body text from common semantic containers."""
        for selector in ['article', 'div.story-body', 'div.article-body', 'main', 'section']:
            node = soup.select_one(selector)
            if node:
                paragraphs = [p.get_text(' ', strip=True) for p in node.find_all('p')]
                if paragraphs:
                    return ' '.join(paragraphs)

        description = soup.select_one('meta[name="description"]') or soup.select_one('meta[property="og:description"]')
        return description.get('content', '').strip() if description and description.get('content') else ''

    def fetch_article_metadata(self, article):
        """Enrich raw article metadata with date and content."""
        link = article.get('link')
        if not link:
            return article

        html = self.fetch_html(link)
        if not html:
            return article

        soup = BeautifulSoup(html, 'html.parser')
        article['date'] = self.parse_published_date(soup, fallback_date=datetime.datetime.utcnow().strftime('%Y-%m-%d'))
        article['content'] = article.get('content') or self.extract_article_content(soup) or article.get('title', '')
        article['source_name'] = self.source_name
        return article

    @abstractmethod
    def crawl_articles(self):
        """Bắt buộc các class con phải định nghĩa cách cào bài"""
        pass
