# crawlers/vnexpress.py
import logging
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base_crawler import BaseCrawler

class VnExpressCrawler(BaseCrawler):
    """Crawler for targeted VnExpress RSS feeds focused on business, technology, and geopolitics."""

    RSS_FEEDS = [
        ('Supply Chain & Foundry', '/rss/kinh-doanh.rss'),
        ('Technology & R&D', '/rss/cong-nghe.rss'),
        ('Geopolitics & Export Control', '/rss/the-gioi.rss'),
    ]

    def __init__(self):
        super().__init__(base_url='https://vnexpress.net', source_name='VnExpress')

    def crawl_articles(self):
        logging.info(f'Bắt đầu thu thập: {self.source_name} (RSS targeted feeds)')
        candidate_articles = []
        seen_links = set()

        for category, path in self.RSS_FEEDS:
            feed_url = urljoin(self.base_url, path)
            items = self.parse_rss_feed(feed_url, category)
            if not items:
                logging.warning(f'Không tải được RSS feed: {feed_url}')
                continue

            for item in items:
                link = item.get('link')
                if not link or link in seen_links or '/video/' in link:
                    continue

                seen_links.add(link)
                candidate_articles.append(item)
                if len(candidate_articles) >= 60:
                    break

            if len(candidate_articles) >= 60:
                break

        if not candidate_articles:
            return self.load_fallback_articles()

        enriched_articles = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_article = {
                executor.submit(self.fetch_article_metadata, article): article for article in candidate_articles[:40]
            }
            for future in as_completed(future_to_article):
                try:
                    enriched = future.result()
                    if enriched:
                        enriched_articles.append(enriched)
                except Exception as exc:
                    logging.warning(f'VnExpress metadata fetch failed: {exc}')

        if not enriched_articles:
            return self.load_fallback_articles()

        logging.info(f'Xong {self.source_name}: {len(enriched_articles)} bài báo.')
        return enriched_articles

    def parse_rss_feed(self, feed_url, category_hint):
        html = self.fetch_html(feed_url)
        if not html:
            return []

        try:
            root = ET.fromstring(html)
        except ET.ParseError as exc:
            logging.error(f'Lỗi phân tích RSS VnExpress: {exc}')
            return []

        items = []
        for item in root.findall('.//item'):
            title = (item.findtext('title') or '').strip()
            link = (item.findtext('link') or '').strip()
            description = (item.findtext('description') or '').strip()
            pubdate = (item.findtext('pubDate') or '').strip()
            if not title or not link:
                continue

            items.append({
                'title': title,
                'link': urljoin(self.base_url, link),
                'content': description,
                'date': self.parse_pubdate(pubdate),
                'source_name': self.source_name,
                'category_hint': category_hint,
            })

            if len(items) >= 25:
                break

        return items

    @staticmethod
    def parse_pubdate(pubdate):
        if not pubdate:
            return ''
        try:
            from email.utils import parsedate_to_datetime
            parsed = parsedate_to_datetime(pubdate)
            return parsed.strftime('%Y-%m-%d')
        except Exception:
            return ''
