# pipeline/database.py
import sqlite3
import logging

def save_articles_to_db(articles):
    """
    Saves articles and establishes a Many-to-Many relationship between Articles and Keywords.
    Ensures foreign key constraints and prevents data duplication (Deduplication).
    """
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    # Enforce Foreign Key constraints in SQLite for data integrity
    cursor.execute("PRAGMA foreign_keys = ON")
    
    for article in articles:
        try:
            # 1. Insert into Articles table (Ignore if URL already exists to prevent duplication)
            cursor.execute('''
                INSERT OR IGNORE INTO Articles (title, link, content, date, category, sentiment_score, source_id)
                VALUES (?, ?, ?, ?, ?, ?, (SELECT id FROM Sources WHERE name = ?))
            ''', (
                article.get('title'), 
                article.get('link'), 
                article.get('content'), 
                article.get('date'), 
                article.get('category'), 
                article.get('sentiment_score', 0.0), 
                article.get('source_name')
            ))
            
            # 2. Retrieve the ID of the inserted (or existing) article
            cursor.execute('SELECT id FROM Articles WHERE link = ?', (article.get('link'),))
            article_result = cursor.fetchone()
            if not article_result:
                continue
            article_id = article_result[0]
            
            # 3. Process extracted keywords and map them in the junction table
            keywords = article.get('keywords', [])
            for kw in keywords:
                # Insert keyword into Keywords table (Ignore if it already exists)
                cursor.execute('INSERT OR IGNORE INTO Keywords (word) VALUES (?)', (kw,))
                
                # Retrieve the keyword ID
                cursor.execute('SELECT id FROM Keywords WHERE word = ?', (kw,))
                keyword_result = cursor.fetchone()
                if not keyword_result:
                    continue
                keyword_id = keyword_result[0]
                
                # Establish the Many-to-Many relationship in Article_Keyword table
                cursor.execute('''
                    INSERT OR IGNORE INTO Article_Keyword (article_id, keyword_id) 
                    VALUES (?, ?)
                ''', (article_id, keyword_id))
                
        except sqlite3.Error as e:
            logging.error(f"SP3 SQLite Error for article {article.get('link')}: {e}")
            
    conn.commit()
    conn.close()
    logging.info("SP3: Successfully synchronized Articles and Keywords with Relational Database mappings.")