import json
import os
import tempfile
import unittest

from pipeline.forecasting import generate_trend_predictions
from pipeline.text_processor import clean_articles_pipeline


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
        self.assertEqual(cleaned[0]['category'], 'Supply Chain')
        self.assertEqual(cleaned[0]['date'], '2026-07-24')

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
