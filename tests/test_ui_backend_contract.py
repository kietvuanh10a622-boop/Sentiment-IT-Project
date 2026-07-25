import unittest
from pathlib import Path


class UiBackendContractTests(unittest.TestCase):
    def test_index_html_uses_backend_compatible_trend_and_sentiment_handling(self):
        html_path = Path(__file__).resolve().parents[1] / 'index.html'
        html = html_path.read_text(encoding='utf-8')

        self.assertIn('function normalizeSentimentLabel', html)
        self.assertIn('function resolveTrendData', html)
        self.assertNotIn("new Chart(trendCanvas", html)


if __name__ == '__main__':
    unittest.main()
