import datetime
import json
import logging
import os
import random
import re
import time
from abc import ABC, abstractmethod
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')


class BaseCrawler(ABC):
    FALLBACK_CACHE = {
        "VnExpress": [
            {
                "title": "TSMC expands advanced packaging and AI chip capacity",
                "link": "https://vnexpress.net/fallback-tsmc",
                "source_name": "VnExpress",
                "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                "content": "TSMC expands advanced packaging and AI chip capacity to meet rising global demand.",
                "category_hint": "Semiconductor Supply Chain"
            },
            {
                "title": "Vietnam attracts new electronics investment amid export growth",
                "link": "https://vnexpress.net/fallback-vietnam-electronics",
                "source_name": "VnExpress",
                "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                "content": "Vietnam attracts new electronics investment as manufacturers diversify supply chains.",
                "category_hint": "Logistics"
            }
        ],
        "BBC": [
            {
                "title": "Export controls reshape the global semiconductor supply chain",
                "link": "https://www.bbc.com/fallback-chip-export",
                "source_name": "BBC",
                "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                "content": "BBC fallback article about export controls and semiconductor geopolitics.",
                "category_hint": "Geopolitics"
            },
            {
                "title": "Energy transition and battery investment accelerate across Europe",
                "link": "https://www.bbc.com/fallback-energy-transition",
                "source_name": "BBC",
                "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                "content": "Europe accelerates battery and renewable investment to support the energy transition.",
                "category_hint": "Energy & Climate"
            }
        ]
    }

    def __init__(self, base_url, source_name):
        self.base_url = base_url.rstrip('/')
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update(self.build_headers())

    def build_headers(self):
        return {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
            ]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': self.base_url,
            'Upgrade-Insecure-Requests': '1',
        }

    def fetch_html(self, url, timeout=20, retries=4, backoff=1.5):
        if not url:
            return None
        last_error = None
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=timeout, allow_redirects=True)
                if response.status_code in {403, 429, 500, 502, 503, 504} and attempt < retries - 1:
                    wait_time = backoff * (attempt + 1)
                    logging.warning(f"Transient HTTP {response.status_code} for {url}; retrying in {wait_time:.1f}s")
                    time.sleep(wait_time)
                    continue
                response.raise_for_status()
                return response.text
            except requests.exceptions.Timeout as exc:
                last_error = exc
                if attempt < retries - 1:
                    time.sleep(backoff * (attempt + 1))
                    continue
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt < retries - 1:
                    time.sleep(backoff * (attempt + 1))
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

    def normalize_article_date(self, value, fallback_date=None):
        if value is None:
            return fallback_date

        if isinstance(value, datetime.datetime):
            return value.strftime('%Y-%m-%d')
        if isinstance(value, datetime.date):
            return value.strftime('%Y-%m-%d')

        text = str(value).strip()
        if not text:
            return fallback_date

        if re.search(r'\d{4}-\d{2}-\d{2}', text):
            match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
            if match:
                return match.group(1)

        try:
            parsed = parsedate_to_datetime(text)
            if parsed:
                return parsed.astimezone(datetime.timezone.utc).strftime('%Y-%m-%d')
        except Exception:
            pass

        for fmt in ('%d/%m/%Y', '%d/%m/%y', '%B %d, %Y', '%b %d, %Y', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
            try:
                parsed = datetime.datetime.strptime(text, fmt)
                return parsed.strftime('%Y-%m-%d')
            except Exception:
                continue

        try:
            parsed = datetime.datetime.fromisoformat(text.replace('Z', '+00:00'))
            return parsed.strftime('%Y-%m-%d')
        except Exception:
            return fallback_date

    def parse_published_date(self, soup, fallback_date=None):
        fallback_date = fallback_date or datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
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
            ('div[class*="date"]', 'datetime'),
        ]:
            element = soup.select_one(selector)
            if element and element.get(attr):
                date_candidates.append(element.get(attr).strip())

        if not date_candidates:
            return fallback_date

        for candidate in date_candidates:
            normalized = self.normalize_article_date(candidate, fallback_date=fallback_date)
            if normalized:
                return normalized
        return fallback_date

    def extract_article_content(self, soup):
        for selector in ['article', 'div.story-body', 'div.article-body', 'main', 'section', 'div[class*="content"]']:
            node = soup.select_one(selector)
            if node:
                paragraphs = [p.get_text(' ', strip=True) for p in node.find_all('p') if p.get_text(' ', strip=True)]
                if paragraphs:
                    return ' '.join(paragraphs[:20])

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
        if '/video/' in link or '/live/' in link or '/av/' in link or '/gallery/' in link:
            return False
        return True

    def is_article_url(self, link):
        if not link:
            return False
        parsed = urlparse(link)
        path = parsed.path or ''
        if path.startswith('/news/articles/') and re.search(r'/news/articles/[a-z0-9]+$', path):
            return True
        if path.endswith('.html') and re.search(r'-\d{5,}\.html$', path):
            return True
        if '/news/' in path and re.search(r'-\d+', path):
            return True
        if re.search(r'/\d{4}/\d{2}/\d{2}/', path):
            return True
        return False

    def normalize_link(self, href, page_url):
        if not href:
            return ''
        href = href.strip()
        if href.startswith('/'):
            return urljoin(self.base_url, href)
        if href.startswith('http'):
            return href
        return urljoin(page_url, href)

    def extract_article_links_from_html(self, html, page_url, category_hint, limit=16):
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        anchors = []
        seen = set()
        for anchor in soup.find_all('a', href=True):
            href = self.normalize_link(anchor.get('href', '').strip(), page_url)
            if not self.is_article_link(href) or not self.is_article_url(href) or href in seen:
                continue
            text = ' '.join(anchor.get_text(' ', strip=True).split())
            if not text:
                text = anchor.get('title', '')
            if not text or len(text) < 8:
                continue
            seen.add(href)
            anchors.append({'title': text, 'link': href, 'category_hint': category_hint})
            if len(anchors) >= limit:
                break
        return anchors

    def _coerce_reference_date(self, now):
        if isinstance(now, datetime.datetime):
            return now.date()
        if isinstance(now, datetime.date):
            return now
        if isinstance(now, str):
            text = now.strip()
            if not text:
                return datetime.datetime.now(datetime.timezone.utc).date()
            try:
                return datetime.datetime.fromisoformat(text).date()
            except ValueError:
                match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
                if match:
                    return datetime.datetime.strptime(match.group(1), '%Y-%m-%d').date()
        return datetime.datetime.now(datetime.timezone.utc).date()

    def is_recent_article(self, article, now=None, max_age_days=2):
        if not article:
            return False

        date_value = article.get('date') or article.get('published') or article.get('published_at') or article.get('pubDate')
        if date_value is None or date_value == '':
            return True

        normalized_date = self.normalize_article_date(date_value)
        if not normalized_date:
            return True

        reference_date = self._coerce_reference_date(now)
        try:
            article_date = datetime.datetime.strptime(normalized_date, '%Y-%m-%d').date()
        except ValueError:
            return True

        return (reference_date - article_date).days <= max_age_days

    def fetch_article_metadata(self, article):
        link = article.get('link')
        if not link:
            return article

        html = self.fetch_html(link)
        if not html:
            return article

        soup = BeautifulSoup(html, 'html.parser')
        article['date'] = self.parse_published_date(soup, fallback_date=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d'))
        article['content'] = article.get('content') or self.extract_article_content(soup) or article.get('title', '')
        article['source_name'] = self.source_name
        return article

    @abstractmethod
    def crawl_articles(self):
        pass
