import logging
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime

from .base_crawler import BaseCrawler


class BBCCrawler(BaseCrawler):
    """Crawler chuyên biệt cho BBC với phạm vi đa ngành rộng hơn."""

    ROUTES = [
        ('Technology', ['/news/technology', '/news/science-and-environment']),
        ('Business', ['/news/business', '/news/business/economy']),
        ('Macro Economy', ['/news/business/economy', '/news/business']),
        ('World', ['/news/world', '/news/world/europe']),
        ('Science', ['/news/science-and-environment', '/news/technology']),
        ('Real Estate', ['/news/business', '/news/uk']),
    ]

    def __init__(self):
        super().__init__(base_url='https://www.bbc.com', source_name='BBC')

    def crawl_articles(self, max_articles=400, max_age_days=2):
        logging.info(f'Starting {self.source_name} crawl across {len(self.ROUTES)} target routes')
        candidate_articles = []
        seen_links = set()
        now = datetime.datetime.now(datetime.timezone.utc)

        tasks = []
        for category, paths in self.ROUTES:
            for path in paths:
                for page in range(1, 6):
                    tasks.append((category, self.build_url(path, page), page))

        with ThreadPoolExecutor(max_workers=min(12, len(tasks))) as executor:
            futures = {executor.submit(self.fetch_route_articles, category, url, page): (category, url) for category, url, page in tasks}
            for future in as_completed(futures):
                try:
                    batch = future.result() or []
                    for article in batch:
                        link = article.get('link')
                        if not link or link in seen_links:
                            continue
                        seen_links.add(link)
                        candidate_articles.append(article)
                        if len(candidate_articles) >= max_articles:
                            break
                    if len(candidate_articles) >= max_articles:
                        break
                except Exception as exc:
                    logging.warning(f'BBC route failed: {exc}')

        if not candidate_articles:
            return self.load_fallback_articles()

        enriched_articles = []
        with ThreadPoolExecutor(max_workers=min(12, len(candidate_articles))) as executor:
            future_to_article = {executor.submit(self.fetch_article_metadata, article): article for article in candidate_articles[:max_articles]}
            for future in as_completed(future_to_article):
                try:
                    article = future.result()
                    if article and self.is_recent_article(article, now=now, max_age_days=max_age_days):
                        enriched_articles.append(article)
                except Exception as exc:
                    logging.warning(f'BBC metadata fetch failed: {exc}')
        
        logging.info(f'Completed {self.source_name}: {len(enriched_articles)} articles')
        return enriched_articles

    def build_url(self, path, page):
        if path.startswith('http://') or path.startswith('https://'):
            url = path
        else:
            url = f'{self.base_url}{path}'
        if page == 1:
            return url
        separator = '&' if '?' in url else '?'
        return f'{url}{separator}page={page}'

    def fetch_route_articles(self, category, url, page):
        try:
            html = self.fetch_html(url)
        except Exception as exc:
            logging.warning(f'BBC fetch error for {url}: {exc}')
            return []

        if not html:
            return []

        if url.endswith('.rss') or '/rss/' in url:
            return self.parse_rss_articles(html, category, url)

        anchors = self.extract_article_links_from_html(html, url, category_hint=category, limit=24)
        articles = []
        for anchor in anchors:
            title = anchor.get('title', '').strip()
            link = anchor.get('link', '').strip()
            if not title or not link:
                continue
            articles.append({
                'title': title,
                'link': link,
                'content': title,
                'date': '',
                'source_name': self.source_name,
                'category_hint': category,
            })
        return articles

    def parse_rss_articles(self, html, category, url):
        try:
            root = ET.fromstring(html)
        except ET.ParseError:
            return []

        articles = []
        for item in root.findall('.//item'):
            title = (item.findtext('title') or '').strip()
            link = (item.findtext('link') or '').strip()
            description = (item.findtext('description') or '').strip()
            if not title or not link:
                continue
            articles.append({
                'title': title,
                'link': link,
                'content': description or title,
                'date': '',
                'source_name': self.source_name,
                'category_hint': category,
            })
        return articles