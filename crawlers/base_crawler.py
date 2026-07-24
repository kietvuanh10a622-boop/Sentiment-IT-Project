import logging
import os
import re
import time
import datetime
import json
from abc import ABC, abstractmethod
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')


class BaseCrawler(ABC):
    FALLBACK_CACHE = {
        "VnExpress": [
            {
                "title": "TSMC mở rộng năng lực sản xuất chip AI",
                "link": "https://vnexpress.net/fallback-tsmc",
                "source_name": "VnExpress",
                "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                "content": "TSMC mở rộng năng lực sản xuất chip AI nhằm đáp ứng nhu cầu toàn cầu.",
                "category_hint": "Technology"
            }
        ],
        "BBC": [
            {
                "title": "Export controls đẩy căng thẳng thị trường bán dẫn toàn cầu",
                "link": "https://www.bbc.com/fallback-chip-export",
                "source_name": "BBC",
                "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                "content": "BBC fallback story about export controls and semiconductor geopolitics.",
                "category_hint": "World/Geopolitics"
            }
        ]
    }

    def __init__(self, base_url, source_name):
        self.base_url = base_url.rstrip('/')
        self.source_name = source_name

    def build_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': self.base_url,
        }

    def fetch_html(self, url, timeout=20, retries=3):
        if not url:
            return None
        last_error = None
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.build_headers(), timeout=timeout, allow_redirects=True)
                if response.status_code in {403, 429, 500, 502, 503, 504} and attempt < retries - 1:
                    wait_time = (attempt + 1) * 2.0
                    logging.warning(f"Transient HTTP {response.status_code} for {url}; retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                response.raise_for_status()
                return response.text
            except requests.exceptions.Timeout as exc:
                last_error = exc
                if attempt < retries - 1:
                    time.sleep((attempt + 1) * 1.5)
                    continue
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt < retries - 1:
                    time.sleep((attempt + 1) * 1.5)
                    continue
        logging.warning(f"Unable to fetch HTML from {url}: {last_error}")
        return None

    def load_fallback_articles(self):
        cached = self.FALLBACK_CACHE.get(self.source_name, [])
        if cached:
            logging.warning(f"Using fallback data for {self.source_name}: {len(cached)} articles")
            return [dict(item) for item in cached]

        fallback_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fallback_cache.json')
        if os.path.exists(fallback_path):
            try:
                with open(fallback_path, 'r', encoding='utf-8') as handle:
                    raw = json.load(handle)
                    return [article for article in raw if article.get('source_name') == self.source_name]
            except Exception as exc:
                logging.error(f"Unable to read fallback_cache.json: {exc}")
        return []

    def parse_published_date(self, soup, fallback_date=None):
        fallback_date = fallback_date or datetime.datetime.utcnow().strftime('%Y-%m-%d')
        date_candidates = []
        for selector, attr in [
            ('meta[property="article:published_time"]', 'content'),
            ('meta[name="pubdate"]', 'content'),
            ('meta[name="publish-date"]', 'content'),
            ('meta[name="DC.date.issued"]', 'content'),
            ('meta[name="date"]', 'content'),
            ('time[datetime]', 'datetime'),
            ('span.date', 'datetime'),
            ('p[data-datetime]', 'data-datetime'),
        ]:
            element = soup.select_one(selector)
            if element and element.get(attr):
                date_candidates.append(element.get(attr).strip())

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
                pass
            try:
                parsed = datetime.datetime.strptime(candidate, '%d/%m/%Y')
                return parsed.strftime('%Y-%m-%d')
            except Exception:
                pass
            try:
                parsed = datetime.datetime.strptime(candidate, '%B %d, %Y')
                return parsed.strftime('%Y-%m-%d')
            except Exception:
                pass

        return fallback_date

    def extract_article_content(self, soup):
        for selector in ['article', 'div.story-body', 'div.article-body', 'main', 'section']:
            node = soup.select_one(selector)
            if node:
                paragraphs = [paragraph.get_text(' ', strip=True) for paragraph in node.find_all('p') if paragraph.get_text(' ', strip=True)]
                if paragraphs:
                    return ' '.join(paragraphs)

        description = soup.select_one('meta[name="description"]') or soup.select_one('meta[property="og:description"]')
        if description and description.get('content'):
            return description.get('content', '').strip()
        return ''

    def is_article_link(self, link):
        if not link:
            return False
        parsed = urlparse(link)
        if parsed.scheme and parsed.scheme not in {'http', 'https'}:
            return False
        if any(token in link for token in ('mailto:', 'tel:', 'javascript:', '#')):
            return False
        if '/video/' in link or '/live/' in link or '/av/' in link:
            return False
        return True

    def normalize_link(self, href, page_url):
        if not href:
            return ''
        if href.startswith('/'):
            return urljoin(self.base_url, href)
        if href.startswith('http'):
            return href
        return urljoin(page_url, href)

    def extract_article_links_from_html(self, html, page_url, limit=12):
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        anchors = []
        seen = set()
        for anchor in soup.find_all('a', href=True):
            href = self.normalize_link(anchor.get('href', '').strip(), page_url)
            if not self.is_article_link(href) or href in seen:
                continue
            text = ' '.join(anchor.get_text(' ', strip=True).split())
            if not text:
                text = anchor.get('title', '')
            if not text:
                continue
            seen.add(href)
            anchors.append({'title': text, 'link': href})
            if len(anchors) >= limit:
                break
        return anchors

    def fetch_article_metadata(self, article):
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
        pass
