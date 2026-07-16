# pipeline/text_processor.py
import logging

# Semiconductor Market Intelligence Taxonomy
SEMICONDUCTOR_TAXONOMY = {
    "Supply Chain & Foundry": [
        "tsmc", "samsung", "fab", "supply chain", "intel", 
        "foundry", "nvidia", "asml", "chuỗi cung ứng", "đúc chip"
    ],
    "Geopolitics & Export Control": [
        "export control", "chips act", "geopolitics", "trade war", 
        "cấm vận", "đạo luật chip", "địa chính trị", "thương chiến"
    ],
    "Technology & R&D": [
        "euv", "packaging", "semiconductor materials", "nanometer", 
        "r&d", "gpu", "ai chip", "vật liệu bán dẫn", "tiến trình", "vi mạch"
    ]
}

def extract_insights(article):
    """
    Extracts keywords from the article content/title and assigns a specific category.
    Returns None if the article is considered noise (no relevant keywords).
    """
    # Combine title and content for a comprehensive search
    content = str(article.get('content', '') + ' ' + article.get('title', '')).lower()
    
    found_keywords = []
    assigned_category = "General"

    # Scan through the taxonomy to match industry keywords
    for category, keywords in SEMICONDUCTOR_TAXONOMY.items():
        matched = [kw for kw in keywords if kw in content]
        if matched:
            found_keywords.extend(matched)
            assigned_category = category
            break # Assign the first matched category to avoid overlap
            
    # Signal-to-Noise Ratio check: Drop the article if no keywords matched
    if not found_keywords:
        return None

    # Update the article dictionary with extracted metadata
    article['category'] = assigned_category
    article['keywords'] = found_keywords
    
    return article

def clean_articles_pipeline(raw_articles):
    """
    Cleans and categorizes raw articles using map, filter, and lambda functions.
    Ensures that only high-value semiconductor intelligence reaches the database.
    """
    logging.info(f"SP2: Starting text processing for {len(raw_articles)} raw articles...")
    
    # 1. Use map() to apply the extraction function to all articles concurrently
    processed_articles = list(map(extract_insights, raw_articles))
    
    # 2. Use filter() and lambda to discard noise (None values)
    cleaned_articles = list(filter(lambda x: x is not None, processed_articles))
    
    noise_count = len(raw_articles) - len(cleaned_articles)
    logging.info(f"SP2: Pipeline finished. Retained {len(cleaned_articles)} signal articles. Dropped {noise_count} noise articles.")
    
    return cleaned_articles