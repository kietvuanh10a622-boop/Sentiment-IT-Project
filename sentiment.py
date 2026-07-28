# ai_module/sentiment.py
import json
import logging
import os
import time

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - environment-dependent
    genai = None

# Use environment variables to avoid hardcoded secrets and keep the pipeline safe when no API key is available.
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-1.5-flash')

if genai is not None and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as exc:  # pragma: no cover - network/config dependent
        logging.warning(f'Unable to configure Gemini SDK: {exc}')
        genai = None
elif GEMINI_API_KEY:
    logging.warning('Google Generative AI SDK is unavailable; using keyword fallback sentiment analysis.')
else:
    logging.info('No Gemini API key configured; using keyword fallback sentiment analysis.')


def call_gemini_sentiment_api(text_to_analyze):
    """Call the Gemini API when the SDK and API key are available; otherwise return None to use fallback logic."""
    if genai is None or not GEMINI_API_KEY:
        return None

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config={"response_mime_type": "application/json"}
        )

        prompt = f"""
        You are an expert in technology and semiconductor market analysis.
        Analyze the sentiment of the following article title.
        Return the JSON payload with exactly these 2 keys and no extra explanation:
        - "label": Choose exactly one of "Positive", "Negative", or "Neutral".
        - "score": A float from -1.0 to 1.0.

        Article title: "{text_to_analyze}"
        """

        response = model.generate_content(prompt)
        result = json.loads(response.text)

        label = str(result.get('label', 'Neutral')).strip().title()
        if label == 'Neutral'.title():
            label = 'Neutral'
        score = float(result.get('score', 0.0))

        # Validate sentiment label against allowed values
        if label not in ['Positive', 'Negative', 'Neutral']:
            label = 'Neutral'
        
        # Ensure score is within valid range
        score = max(-1.0, min(1.0, float(score)))

        return {"score": score, "label": label}

    except Exception as exc:
        logging.warning(f'Gemini API unavailable, using internal fallback: {exc}')
        return None


def _keyword_fallback_sentiment(text):
    """Internal fallback when the API is unavailable; optimized for a non-server pipeline."""
    if not text:
        return {"score": 0.0, "label": "Neutral"}

    lower_text = text.lower()
    positive_words = [
        'surge', 'growth', 'profit', 'up', 'build', 'new', 'innovation', 'invest', 'revenue',
        'increase', 'gain', 'breakthrough', 'develop', 'expand', 'success'
    ]
    negative_words = [
        'drop', 'fall', 'shortage', 'crisis', 'down', 'loss', 'delay', 'cut', 'ban', 'risk',
        'decline', 'decrease', 'impact', 'restrict'
    ]

    pos_count = sum(1 for word in positive_words if word in lower_text)
    neg_count = sum(1 for word in negative_words if word in lower_text)
    total_signal = pos_count + neg_count

    if total_signal == 0:
        return {"score": 0.0, "label": "Neutral"}

    raw_score = (pos_count - neg_count) / total_signal
    score = round(raw_score, 2)

    if score > 0:
        return {"score": score, "label": "Positive"}
    if score < 0:
        return {"score": score, "label": "Negative"}
    return {"score": 0.0, "label": "Neutral"}


def get_sentiment(text, source_name):
    """Main processing function; prioritize Gemini when available, otherwise use keyword-based fallback."""
    if not text:
        return {"score": 0.0, "label": "Neutral"}

    try:
        api_result = call_gemini_sentiment_api(text)
        if api_result:
            logging.debug(f'Gemini API succeeded for source {source_name}')
            return api_result

        # Fallback to keyword-based sentiment if API is unavailable
        logging.debug(f'Using keyword fallback for source {source_name}')
        return _keyword_fallback_sentiment(text)

    except Exception as exc:
        logging.error(f'Pipeline sentiment error: {exc}')
        logging.info(f'Falling back to keyword sentiment for source {source_name}')
        return _keyword_fallback_sentiment(text)


def apply_sentiment_analysis(articles):
    """Receive a list of articles and apply sentiment analysis with safe fallback logic."""
    logging.info('--- STEP C2: CONNECT TO GOOGLE GEMINI 1.5 API ---')
    analyzed_articles = []

    total_articles = len(articles)
    for index, article in enumerate(articles):
        if (index + 1) % 5 == 0 or index == 0:
            logging.info(f'Sending article {index + 1}/{total_articles} to Google AI Cloud...')

        text_to_analyze = article.get('title', '')
        source_name = article.get('source_name', 'Unknown')

        sentiment_result = get_sentiment(text_to_analyze, source_name)
        article['sentiment_score'] = sentiment_result['score']
        article['sentiment_label'] = sentiment_result['label']
        analyzed_articles.append(article)

        # Reduce pipeline delay to avoid slowing down the run when the dataset is large.
        if total_articles > 50:
            time.sleep(0.25)

    logging.info('--- GEMINI API CALL COMPLETED ---')
    return analyzed_articles