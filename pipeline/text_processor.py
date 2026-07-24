import datetime
import logging
import re
from collections import defaultdict

TAXONOMY_MAP = {
    'Technology': [
        'technology', 'tech', 'ai', 'artificial intelligence', 'chip', 'semiconductor', 'gpu', 'cpu',
        'software', 'startup', 'innovation', 'research', 'robot', 'quantum', 'cyber', 'cloud', 'data', 'app'
    ],
    'Business': [
        'business', 'company', 'ceo', 'merger', 'acquisition', 'executive', 'enterprise', 'retail',
        'brand', 'investment', 'expansion', 'strategy', 'restructuring', 'supply chain', 'partner'
    ],
    'World/Geopolitics': [
        'world', 'geopolitics', 'war', 'election', 'diplomacy', 'sanction', 'trade war', 'tariff',
        'export', 'foreign policy', 'military', 'conflict', 'policy', 'diplomatic'
    ],
    'Science': [
        'science', 'scientist', 'research', 'discovery', 'space', 'biology', 'physics', 'lab', 'study',
        'astronomy', 'genetics', 'materials', 'medical'
    ],
    'Economy': [
        'economy', 'inflation', 'gdp', 'consumer', 'price', 'unemployment', 'growth', 'recession',
        'rate', 'fiscal', 'monetary', 'market', 'financial'
    ],
    'Logistics': [
        'logistics', 'shipping', 'port', 'transport', 'freight', 'warehouse', 'delivery', 'cargo',
        'truck', 'rail', 'container', 'supply chain'
    ],
    'Finance': [
        'finance', 'stock', 'bond', 'trade', 'investment', 'trading', 'earnings', 'revenue', 'profit',
        'shareholder', 'bank', 'equity', 'market'
    ],
    'Energy': [
        'energy', 'oil', 'gas', 'renewable', 'electricity', 'battery', 'grid', 'coal', 'nuclear', 'hydrogen'
    ],
    'Healthcare': [
        'healthcare', 'health', 'medical', 'pharma', 'vaccine', 'hospital', 'drug', 'patient', 'clinic'
    ],
    'Environment': [
        'environment', 'climate', 'emissions', 'green', 'sustainability', 'carbon', 'weather', 'pollution', 'forest'
    ],
}

KEEP_KEYWORDS = set(sum(TAXONOMY_MAP.values(), []))
DATE_PATTERNS = [
    r'(\d{4}-\d{2}-\d{2})',
    r'(\d{2}/\d{2}/\d{4})',
    r'(\d{1,2}/\d{1,2}/\d{2,4})',
    r'([A-Za-z]{3,9} \d{1,2}, \d{4})',
    r'([A-Za-z]{3,9} \d{1,2} \d{4})',
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
    scores = defaultdict(int)

    for category, terms in TAXONOMY_MAP.items():
        for term in terms:
            if term in text:
                scores[category] += 2 if ' ' in term else 1

    category_hint = str(article.get('category_hint') or '').lower()
    if category_hint:
        for category in TAXONOMY_MAP:
            if category.lower() in category_hint:
                scores[category] += 1

    if not scores:
        return 'Other'

    return max(scores, key=scores.get)


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
            'link': str(raw.get('link', '') or '').strip(),
            'content': content,
            'source_name': raw.get('source_name') or raw.get('source') or 'Unknown',
            'date': normalize_date(raw.get('date')),
            'category': 'Other',
            'category_hint': raw.get('category_hint') or '',
            'sentiment_score': raw.get('sentiment_score', 0.0),
            'sentiment_label': raw.get('sentiment_label', 'Neutral'),
            'keywords': []
        }

        cleaned['category'] = categorize_article(cleaned)
        cleaned['keywords'] = extract_keywords(cleaned)
        cleaned_articles.append(cleaned)

    logging.info(f'SP2: Pipeline finished. Cleaned {len(cleaned_articles)} articles into dynamic taxonomy buckets.')
    return cleaned_articles
