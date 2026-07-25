import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from base_crawler import BaseCrawler


class VnExpressCrawler(BaseCrawler):
    """Specialized crawler for VnExpress technology, business, and world news."""

    ROUTES = [
        ('Technology', '/cong-nghe'),
        ('Market Economy', '/kinh-doanh'),
        ('Geopolitics', '/the-gioi'),
    ]

    def __init__(self):
        super().__init__(base_url='https://vnexpress.net', source_name='VnExpress')

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
                    logging.warning(f'VnExpress route failed: {exc}')

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
                    logging.warning(f'VnExpress metadata fetch failed: {exc}')

        logging.info(f'Completed {self.source_name}: {len(enriched_articles)} articles')
        return enriched_articles

    def fetch_route_articles(self, category, url, page):
        html = self.fetch_html(url)
        if not html:
            return []

        anchors = self.extract_article_links_from_html(html, url, category_hint=category, limit=12)
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
