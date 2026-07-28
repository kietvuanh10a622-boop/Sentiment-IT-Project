import importlib
import sys
import types
import unittest


class SentimentFallbackTests(unittest.TestCase):
    def test_import_without_google_dependency_uses_fallback(self):
        sys.modules.pop('ai_module.sentiment', None)
        monkey_google = types.ModuleType('google')
        monkey_generativeai = types.ModuleType('google.generativeai')
        monkey_generativeai.configure = lambda *args, **kwargs: None
        monkey_google.generativeai = monkey_generativeai
        sys.modules['google'] = monkey_google
        sys.modules['google.generativeai'] = None

        module = importlib.import_module('ai_module.sentiment')
        result = module.get_sentiment('TSMC expands AI chip capacity', 'TestSource')

        self.assertIn(result['label'], {'Positive', 'Negative', 'Neutral'})
        self.assertIsInstance(result['score'], float)


if __name__ == '__main__':
    unittest.main()
