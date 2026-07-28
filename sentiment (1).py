# ai_module/sentiment.py
import json
import logging
import os
import time

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None

# Environment configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-1.5-flash')

if genai is not None and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as exc:  # pragma: no cover
        logging.warning(f'Unable to configure Gemini SDK: {exc}')
        genai = None
elif GEMINI_API_KEY:
    logging.warning('Google Generative AI SDK is unavailable; using keyword fallback sentiment analysis.')
else:
    logging.info('No Gemini API key configured; using keyword fallback sentiment analysis.')

# Strict English System Prompt forcing multi-layered structured output
SYSTEM_PROMPT = """
You are an expert Intelligence Analyst in technology, semiconductor, and IT markets.
Analyze the provided news article (Title and Content) and extract deep insights including:
1. Sensationalism & Clickbait Index (Score 0.0 to 10.0 and clear reasons)
2. Framing Analysis (Primary frame, tone, summary bias)
3. Entity-Level Sentiment Analysis (Extract individual entities like companies, products, executives, and evaluate sentiment for EACH entity separately).

ALL text explanations, reasons, bias summaries, and key claims MUST BE WRITTEN IN ENGLISH.

MUST return STRICTLY JSON matching this exact schema:
{
  "sensationalism": {
    "score": float (0.0 to 10.0),
    "level": "LOW" | "MEDIUM" | "HIGH",
    "headline_clickbait_rating": float (0.0 to 10.0),
    "reasons": [
      "string (Clear evidence in English explaining the sensationalism score)"
    ]
  },
  "framing_analysis": {
    "primary_frame": "string (UPPERCASE_ENUM, e.g., FEAR_MONGERING, ECONOMIC_GROWTH, INNOVATION_HYPE, NEUTRAL_REPORTING)",
    "tone": "string (UPPERCASE_ENUM, e.g., ALARMIST, OPTIMISTIC, NEUTRAL, CRITICAL)",
    "summary_bias": "string (Summary of article bias/framing in English)"
  },
  "overall_sentiment": {
    "score": float (-1.0 to 1.0),
    "label": "Positive" | "Negative" | "Neutral"
  },
  "entities": [
    {
      "name": "string (Entity Name)",
      "type": "ORGANIZATION" | "PERSON" | "LOCATION" | "PRODUCT",
      "sentiment": {
        "score": float (-1.0 to 1.0),
        "label": "Positive" | "Negative" | "Neutral",
        "confidence": float (0.0 to 1.0)
      },
      "key_claims": [
        "string (Claims or facts mentioned about this entity in English)"
      ]
    }
  ]
}
"""


def call_gemini_advanced_analysis(title, content=""):
    """Calls Gemini API for deep English sentiment, sensationalism, and entity analysis."""
    if genai is None or not GEMINI_API_KEY:
        return None

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json", "temperature": 0.2}
        )

        user_input = f"""
        TITLE: {title}
        CONTENT/SUMMARY: {content if content else "N/A (Title only provided)"}
        """

        response = model.generate_content(user_input)
        result = json.loads(response.text)
        return result

    except Exception as exc:
        logging.warning(f'Gemini API error, falling back to internal keyword analyzer: {exc}')
        return None


def _keyword_fallback_sentiment(text):
    """Internal English fallback mechanism when Gemini API is unavailable."""
    if not text:
        return {
            "overall_sentiment": {"score": 0.0, "label": "Neutral"},
            "sensationalism": {"score": 0.0, "level": "LOW", "reasons": ["Fallback mode active"]},
            "entities": []
        }
    
    lower_text = text.lower()
    positive_words = ['surge', 'growth', 'profit', 'up', 'build', 'new', 'innovation', 'invest', 'revenue', 'success', 'expand']
    negative_words = ['drop', 'fall', 'shortage', 'crisis', 'down', 'loss', 'delay', 'cut', 'ban', 'risk', 'recession']

    pos_count = sum(1 for word in positive_words if word in lower_text)
    neg_count = sum(1 for word in negative_words if word in lower_text)

    label = "Neutral"
    score = 0.0
    if pos_count > neg_count:
        label, score = "Positive", 0.65
    elif neg_count > pos_count:
        label, score = "Negative", -0.65

    return {
        "overall_sentiment": {"score": score, "label": label},
        "sensationalism": {"score": 3.0, "level": "LOW", "reasons": ["Estimated via keyword fallback"]},
        "entities": []
    }


def analyze_article(article):
    """Processes a single article."""
    title = article.get('title', '')
    content = article.get('content', article.get('summary', ''))
    source_name = article.get('source_name', 'Unknown')

    if not title and not content:
        return _keyword_fallback_sentiment("")

    # Primary: Deep AI Analysis with Gemini
    ai_result = call_gemini_advanced_analysis(title, content)
    if ai_result:
        logging.debug(f'Gemini Advanced Analysis succeeded for source: {source_name}')
        return ai_result

    # Fallback: Keyword Analysis
    logging.debug(f'Using keyword fallback for source: {source_name}')
    return _keyword_fallback_sentiment(title)


def apply_sentiment_analysis(articles):
    """Main pipeline entry point: Enriches input articles list with deep sentiment metadata."""
    logging.info('--- STEP C2: CONNECTING TO GOOGLE GEMINI DEEP ANALYSIS ---')
    analyzed_articles = []
    total = len(articles)

    for index, article in enumerate(articles):
        if (index + 1) % 5 == 0 or index == 0:
            logging.info(f'Analyzing article {index + 1}/{total}...')

        analysis = analyze_article(article)

        # Append advanced analysis fields to article dictionary
        article['sentiment_score'] = analysis.get('overall_sentiment', {}).get('score', 0.0)
        article['sentiment_label'] = analysis.get('overall_sentiment', {}).get('label', 'Neutral')
        article['sensationalism_score'] = analysis.get('sensationalism', {}).get('score', 0.0)
        article['sensationalism_level'] = analysis.get('sensationalism', {}).get('level', 'LOW')
        article['sensationalism_reasons'] = analysis.get('sensationalism', {}).get('reasons', [])
        article['framing_analysis'] = analysis.get('framing_analysis', {})
        article['entities_analysis'] = analysis.get('entities', [])

        analyzed_articles.append(article)

        if total > 50:
            time.sleep(0.2)

    logging.info('--- COMPLETED GEMINI DEEP ANALYSIS ---')
    return analyzed_articles