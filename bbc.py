import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET

from base_crawler import BaseCrawler


class BBCCrawler(BaseCrawler):
    """Crawler chuyên biệt cho BBC về công nghệ, kinh doanh và thế giới."""

    ROUTES = [
        ('Technology', '/news/technology'),
        ('Market Economy', '/news/business'),
        ('Geopolitics', '/news/world'),
    ]
    RSS_FEEDS = {
        'Technology': 'https://feeds.bbci.co.uk/news/technology/rss.xml',
        'Market Economy': 'https://feeds.bbci.co.uk/news/business/rss.xml',
        'Geopolitics': 'https://feeds.bbci.co.uk/news/world/rss.xml',
    }

    def __init__(self):
        super().__init__(base_url='https://www.bbc.com', source_name='BBC')

    def crawl_articles(self, max_articles=200, max_age_days=2):
        logging.info(f'Starting {self.source_name} crawl across {len(self.ROUTES)} target routes')
        candidate_articles = []
        seen_links = set()

        tasks = []
        for category, path in self.ROUTES:
            for page in range(1, 4):
                url = f'{self.base_url}{path}' if page == 1 else f'{self.base_url}{path}?page={page}'
                tasks.append((category, url, page))

        with ThreadPoolExecutor(max_workers=min(8, len(tasks))) as executor:
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

        for category, feed_url in self.RSS_FEEDS.items():
            try:
                for article in self.fetch_feed_articles(category, feed_url):
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
                logging.warning(f'BBC RSS feed failed for {category}: {exc}')

        if not candidate_articles:
            return self.load_fallback_articles()

        enriched_articles = []
        with ThreadPoolExecutor(max_workers=min(8, len(candidate_articles))) as executor:
            future_to_article = {executor.submit(self.fetch_article_metadata, article): article for article in candidate_articles[:max_articles]}
            for future in as_completed(future_to_article):
                try:
                    article = future.result()
                    if article and self.is_recent_article(article, max_age_days=max_age_days):
                        enriched_articles.append(article)
                except Exception as exc:
                    logging.warning(f'BBC metadata fetch failed: {exc}')

        logging.info(f'Completed {self.source_name}: {len(enriched_articles)} articles')
        return enriched_articles

    def fetch_feed_articles(self, category, feed_url):
        html = self.fetch_html(feed_url)
        if not html:
            return []

        try:
            root = ET.fromstring(html)
        except ET.ParseError:
            return []

        items = []
        for entry in root.findall('.//{*}item'):
            title = ''.join(entry.findtext('{*}title', default='') or '').strip()
            link = ''.join(entry.findtext('{*}link', default='') or '').strip()
            description = ''.join(entry.findtext('{*}description', default='') or '').strip()
            published = ''.join(entry.findtext('{*}pubDate', default='') or '').strip()
            if not title or not link:
                continue
            items.append({
                'title': title,
                'link': link,
                'content': description or title,
                'date': published,
                'source_name': self.source_name,
                'category_hint': category,
            })
        return items

    def fetch_route_articles(self, category, url, page):
        html = self.fetch_html(url)
        if not html:
            return []

        anchors = self.extract_article_links_from_html(html, url, category_hint=category, limit=18)
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
