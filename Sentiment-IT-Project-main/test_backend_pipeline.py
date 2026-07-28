import json
import os
import tempfile
import unittest

from forecasting import generate_trend_predictions
from text_processor import clean_articles_pipeline


class BackendPipelineTests(unittest.TestCase):
    def test_clean_articles_pipeline_filters_irrelevant_news_and_normalizes_dates(self):
        raw_articles = [
            {
                'title': 'TSMC expands advanced packaging for AI chips',
                'content': 'The foundry is adding capacity for high-bandwidth memory and advanced packaging.',
                'link': 'https://example.com/1',
                'source_name': 'VnExpress',
                'date': '2026-07-24',
                'category_hint': 'Technology'
            },
            {
                'title': 'Local football league update',
                'content': 'A football match ended in a dramatic win.',
                'link': 'https://example.com/2',
                'source_name': 'BBC',
                'date': '2026-07-24',
                'category_hint': 'General'
            }
        ]

        cleaned = clean_articles_pipeline(raw_articles)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0]['category'], 'Semiconductor')
        self.assertEqual(cleaned[0]['date'], '2026-07-24')

    def test_extract_article_links_from_html_filters_non_article_urls(self):
        from base_crawler import BaseCrawler

        class DummyCrawler(BaseCrawler):
            def crawl_articles(self):
                return []

        crawler = DummyCrawler(base_url='https://vnexpress.net', source_name='VnExpress')
        html = '''<html><body>
            <a href="/technology-science">Technology science</a>
            <a href="https://vnexpress.net/gioi-chuyen-gia-noi-gi-khi-moonshot-bi-to-chung-cat-ai-my-5101167.html">Try crawling a VnExpress article</a>
            <a href="https://www.bbc.com/news/technology-5101445">BBC article example</a>
        </body></html>'''
        anchors = crawler.extract_article_links_from_html(html, 'https://vnexpress.net/cong-nghe', 'Technology', limit=10)
        self.assertEqual(len(anchors), 2)
        self.assertEqual(anchors[0]['link'], 'https://vnexpress.net/gioi-chuyen-gia-noi-gi-khi-moonshot-bi-to-chung-cat-ai-my-5101167.html')
        self.assertEqual(anchors[1]['link'], 'https://www.bbc.com/news/technology-5101445')

    def test_is_article_url_recognizes_bbc_article_paths(self):
        from base_crawler import BaseCrawler

        class DummyCrawler(BaseCrawler):
            def crawl_articles(self):
                return []

        crawler = DummyCrawler(base_url='https://www.bbc.com', source_name='BBC')
        self.assertTrue(crawler.is_article_url('https://www.bbc.com/news/articles/cd9w22n9e4go'))
        self.assertTrue(crawler.is_article_url('/news/articles/cd9w22n9e4go'))
        self.assertFalse(crawler.is_article_url('/news/technology'))

    def test_recent_articles_filter_keeps_today_and_yesterday_only(self):
        from base_crawler import BaseCrawler

        class DummyCrawler(BaseCrawler):
            def crawl_articles(self):
                return []

        crawler = DummyCrawler(base_url='https://vnexpress.net', source_name='VnExpress')
        now = '2026-07-25'

        self.assertTrue(crawler.is_recent_article({'date': '2026-07-25'}, now=now, max_age_days=1))
        self.assertTrue(crawler.is_recent_article({'date': '2026-07-24'}, now=now, max_age_days=1))
        self.assertFalse(crawler.is_recent_article({'date': '2026-07-23'}, now=now, max_age_days=1))
        self.assertTrue(crawler.is_recent_article({'date': '2026-07-23'}, now=now, max_age_days=2))

    def test_trend_predictions_export_has_historical_and_forecast_blocks(self):
        articles = [
            {'date': '2026-07-18', 'category': 'Supply Chain', 'sentiment_label': 'Positive'},
            {'date': '2026-07-19', 'category': 'Supply Chain', 'sentiment_label': 'Negative'},
            {'date': '2026-07-20', 'category': 'Supply Chain', 'sentiment_label': 'Positive'},
            {'date': '2026-07-21', 'category': 'Supply Chain', 'sentiment_label': 'Neutral'},
            {'date': '2026-07-22', 'category': 'Supply Chain', 'sentiment_label': 'Positive'},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'trend_predictions.json')
            result = generate_trend_predictions(articles, output_path=output_path, horizon_days=3)

            self.assertIn('All', result)
            self.assertIn('historical', result['All'])
            self.assertIn('forecast', result['All'])

            with open(output_path, 'r', encoding='utf-8') as handle:
                exported = json.load(handle)
            self.assertIn('All', exported)


if __name__ == '__main__':
    unittest.main()
