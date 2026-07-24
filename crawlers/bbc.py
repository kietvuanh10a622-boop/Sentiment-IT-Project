import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_crawler import BaseCrawler


class BBCCrawler(BaseCrawler):
    """Multi-domain crawler for BBC using category landing pages and pagination."""

    ROUTES = [
        ('Technology', '/news/technology'),
        ('Business', '/news/business'),
        ('World/Geopolitics', '/news/world'),
        ('Science', '/news/science_and_environment'),
        ('Economy', '/news/business/economy'),
        ('Logistics', '/news/transport'),
        ('Healthcare', '/news/health'),
        ('Environment', '/news/science_and_environment'),
    ]

    def __init__(self):
        super().__init__(base_url='https://www.bbc.com', source_name='BBC')

    def crawl_articles(self, max_articles=250):
        logging.info(f"Starting {self.source_name} crawl across {len(self.ROUTES)} route families")
        candidate_articles = []
        seen_links = set()

        tasks = []
        for category, path in self.ROUTES:
            for page in range(1, 6):
                url = f"{self.base_url}{path}" if page == 1 else f"{self.base_url}{path}?page={page}"
                tasks.append((category, url, page))

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
                    logging.warning(f"BBC route failed: {exc}")

        if not candidate_articles:
            return self.load_fallback_articles()

        enriched_articles = []
        with ThreadPoolExecutor(max_workers=min(10, len(candidate_articles))) as executor:
            future_to_article = {executor.submit(self.fetch_article_metadata, article): article for article in candidate_articles[:max_articles]}
            for future in as_completed(future_to_article):
                try:
                    article = future.result()
                    if article:
                        enriched_articles.append(article)
                except Exception as exc:
                    logging.warning(f"BBC metadata fetch failed: {exc}")

        if not enriched_articles:
            return self.load_fallback_articles()

        logging.info(f"Completed {self.source_name}: {len(enriched_articles)} articles")
        return enriched_articles

    def fetch_route_articles(self, category, url, page):
        html = self.fetch_html(url)
        if not html:
            return []
        anchors = self.extract_article_links_from_html(html, url, limit=12)
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
