import datetime
import logging
import re
from collections import defaultdict

ALLOWED_CATEGORIES = ['Supply Chain', 'Geopolitics', 'R&D', 'Market Economy']

TAXONOMY_MAP = {
    'Supply Chain': [
        'supply chain', 'semiconductor supply chain', 'foundry', 'fab', 'packaging', 'wafer', 'ship', 'shipment',
        'logistics', 'supply', 'capacity', 'inventory', 'manufacturing', 'assembly', 'outsourcing', 'chip supply'
    ],
    'Geopolitics': [
        'geopolitics', 'export control', 'export controls', 'sanction', 'sanctions', 'trade war', 'policy', 'regulation',
        'embargo', 'tariff', 'diplomacy', 'government', 'china', 'us', 'eu'
    ],
    'R&D': [
        'research', 'r&d', 'design', 'chip design', 'ai chip', 'gpu', 'cpu', 'advanced packaging', 'process node',
        'innovation', 'lab', 'semiconductor design', 'architecture', 'ip', 'fabrication'
    ],
    'Market Economy': [
        'market', 'economy', 'investment', 'capex', 'earnings', 'revenue', 'profit', 'demand', 'pricing', 'forecast',
        'stock', 'valuation', 'growth', 'downturn', 'recession', 'consumer'
    ],
}

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
            for fmt in ('%d/%m/%Y', '%d/%m/%y', '%B %d, %Y', '%b %d, %Y', '%Y/%m/%d'):
                try:
                    parsed = datetime.datetime.strptime(date_text, fmt)
                    return parsed.strftime('%Y-%m-%d')
                except Exception:
                    continue
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
            if term.lower() in text:
                scores[category] += 2 if ' ' in term else 1

    category_hint = str(article.get('category_hint') or '').lower()
    if category_hint:
        for category in TAXONOMY_MAP:
            if category.lower() in category_hint:
                scores[category] += 2

    if not scores:
        return None

    # Ưu tiên các thuật ngữ supply-chain cho các bài báo về packaging/fab/capacity.
    supply_chain_boost = ['packaging', 'fab', 'foundry', 'wafer', 'capacity', 'supply chain', 'inventory', 'shipment', 'manufacturing']
    text_lower = text.lower()
    if any(term in text_lower for term in supply_chain_boost):
        scores['Supply Chain'] += 3

    best_category = max(scores, key=scores.get)
    if scores[best_category] < 2:
        return None
    return best_category


def extract_keywords(article):
    text = ' '.join([str(article.get('title', '')), str(article.get('content', ''))]).lower()
    found = set()
    for keywords in TAXONOMY_MAP.values():
        for keyword in keywords:
            if keyword.lower() in text:
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
            'category': None,
            'category_hint': raw.get('category_hint') or '',
            'sentiment_score': raw.get('sentiment_score', 0.0),
            'sentiment_label': raw.get('sentiment_label', 'Neutral'),
            'keywords': []
        }

        cleaned['category'] = categorize_article(cleaned)
        cleaned['keywords'] = extract_keywords(cleaned)

        if not cleaned['category']:
            continue

        cleaned_articles.append(cleaned)

    logging.info(f'SP2: Pipeline finished. Cleaned {len(cleaned_articles)} semiconductor-relevant articles.')
    return cleaned_articles
