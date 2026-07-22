# pipeline/database.py
import sqlite3
import logging

def initialize_database():
    """
    Initializes the SQLite database and creates necessary relational tables 
    (Sources, Articles, Keywords, Article_Keyword) if they do not exist.
    """
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    # Enforce Foreign Key constraints in SQLite
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # 1. Create Sources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # 2. Create Articles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT UNIQUE NOT NULL,
            content TEXT,
            date TEXT,
            category TEXT,
            sentiment_score REAL,
            source_id INTEGER,
            FOREIGN KEY (source_id) REFERENCES Sources(id)
        )
    ''')
    
    # 3. Create Keywords table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL
        )
    ''')
    
    # 4. Create Article_Keyword junction table (Many-to-Many)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Article_Keyword (
            article_id INTEGER,
            keyword_id INTEGER,
            PRIMARY KEY (article_id, keyword_id),
            FOREIGN KEY (article_id) REFERENCES Articles(id),
            FOREIGN KEY (keyword_id) REFERENCES Keywords(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logging.info("SP3: Relational Database schema initialized successfully.")

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
            # First, ensure the source exists in Sources table
            source_name = article.get('source_name', 'Unknown')
            cursor.execute('INSERT OR IGNORE INTO Sources (name) VALUES (?)', (source_name,))
            
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
                source_name
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

def export_database_to_files():
    """
    Placeholder for SP6 Export functionality. 
    Prevents ImportError in main.py.
    """
    # Logic to export SQLite data to CSV/JSON will be handled here or in SP6 telemetry
    logging.info("SP6: Database export function called.")
    pass