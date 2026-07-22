# pipeline/text_processor.py
import logging
import datetime
import re

TAXONOMY_MAP = {
    'Supply Chain & Foundry': [
        'semiconductor', 'chip', 'foundry', 'fabrication', 'wafer', 'tsmc', 'intel',
        'tsmc', 'qualcomm', 'fab', 'factory', 'nvidia', 'asml', 'chipmaking', 'ic'
    ],
    'Geopolitics & Export Control': [
        'geopolitics', 'export control', 'export ban', 'sanction', 'trade war',
        'tariff', 'shipment', 'export restriction', 'us export', 'china export', 'export rules'
    ],
    'Technology & R&D': [
        'technology', 'research', 'innovation', 'r&d', 'ai', 'machine learning',
        'artificial intelligence', 'processor', 'gpu', 'cpu', 'research', 'development',
        'product launch', 'architecture'
    ],
    'Market Economy': [
        'market', 'economy', 'investment', 'revenue', 'earnings', 'stock', 'profit',
        'demand', 'supply', 'shortage', 'inflation', 'growth', 'sale', 'investment'
    ],
}

STRICT_CATEGORIES = list(TAXONOMY_MAP.keys())

KEEP_KEYWORDS = set(sum(TAXONOMY_MAP.values(), []))

FALLBACK_CATEGORY = None

DATE_PATTERNS = [
    r'(\d{4}-\d{2}-\d{2})',
    r'(\d{2}/\d{2}/\d{4})',
    r'([A-Za-z]{3,9} \d{1,2}, \d{4})',
]


def normalize_date(value):
    if not value:
        return datetime.datetime.utcnow().strftime('%Y-%m-%d')

    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.strftime('%Y-%m-%d')

    raw = str(value).strip()
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, raw)
        if not match:
            continue
        date_text = match.group(1)
        try:
            if '/' in date_text:
                parsed = datetime.datetime.strptime(date_text, '%d/%m/%Y')
            elif ',' in date_text:
                parsed = datetime.datetime.strptime(date_text, '%B %d, %Y')
            else:
                parsed = datetime.datetime.fromisoformat(date_text)
            return parsed.strftime('%Y-%m-%d')
        except Exception:
            continue

    try:
        parsed = datetime.datetime.fromisoformat(raw)
        return parsed.strftime('%Y-%m-%d')
    except Exception:
        logging.warning(f'Unable to normalize date: {raw}. Using current date.')
        return datetime.datetime.utcnow().strftime('%Y-%m-%d')


def categorize_article(article):
    text = ' '.join([str(article.get('title', '')), str(article.get('content', ''))]).lower()
    scores = {category: 0 for category in TAXONOMY_MAP}

    for category, terms in TAXONOMY_MAP.items():
        for term in terms:
            if term in text:
                scores[category] += 1

    if all(score == 0 for score in scores.values()):
        return None

    return max(scores, key=scores.get)


def is_relevant_article(article):
    text = ' '.join([str(article.get('title', '')), str(article.get('content', ''))]).lower()
    return any(keyword in text for keyword in KEEP_KEYWORDS)


def extract_keywords(article):
    text = ' '.join([str(article.get('title', '')), str(article.get('content', ''))]).lower()
    found = set()
    for keywords in TAXONOMY_MAP.values():
        for keyword in keywords:
            if keyword in text:
                found.add(keyword)
    return sorted(found)


def clean_articles_pipeline(raw_articles):
    logging.info(f'SP2: Starting text processing for {len(raw_articles)} raw articles...')
    cleaned_articles = []

    for raw in raw_articles:
        title = str(raw.get('title', '')).strip()
        if not title:
            continue

        content = ' '.join(str(raw.get('content', '') or '').split())
        if not content:
            content = title

        cleaned = {
            'title': ' '.join(title.split()),
            'link': raw.get('link', '').strip(),
            'content': content,
            'source_name': raw.get('source_name') or raw.get('source') or 'Unknown',
            'date': normalize_date(raw.get('date')),
            'category': None,
            'sentiment_score': raw.get('sentiment_score', 0.0),
            'sentiment_label': raw.get('sentiment_label', 'Neutral'),
            'keywords': []
        }

        if not is_relevant_article(cleaned):
            continue

        cleaned['category'] = categorize_article(cleaned)
        if not cleaned['category']:
            continue

        cleaned['keywords'] = extract_keywords(cleaned)
        cleaned_articles.append(cleaned)

    logging.info(f'SP2: Pipeline finished. Cleaned {len(cleaned_articles)} relevant semiconductor/tech articles.')
    return cleaned_articles
