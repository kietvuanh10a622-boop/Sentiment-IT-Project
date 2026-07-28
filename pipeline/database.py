import csv
import json
import logging
import os
import sqlite3

DB_FILENAME = 'news_database.db'
CSV_BACKUP = 'articles_backup.csv'
JSON_BACKUP = 'articles_backup.json'


def get_database_path():
    """Get absolute path to database file, ensuring consistent location regardless of working directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, DB_FILENAME)


def initialize_database():
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT UNIQUE NOT NULL,
            content TEXT,
            date TEXT,
            category TEXT,
            sentiment_score REAL,
            sentiment_label TEXT,
            source_id INTEGER,
            FOREIGN KEY (source_id) REFERENCES Sources(id)
        )
    ''')

    cursor.execute("PRAGMA table_info(Articles)")
    columns = {row[1] for row in cursor.fetchall()}
    if 'sentiment_score' not in columns:
        cursor.execute('ALTER TABLE Articles ADD COLUMN sentiment_score REAL')
    if 'sentiment_label' not in columns:
        cursor.execute('ALTER TABLE Articles ADD COLUMN sentiment_label TEXT')
    if 'source_id' not in columns:
        cursor.execute('ALTER TABLE Articles ADD COLUMN source_id INTEGER')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL
        )
    ''')

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
    logging.info('SP3: Relational database schema initialized successfully.')


def save_articles_to_db(articles):
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')

    saved_count = 0
    for article in articles:
        try:
            source_name = article.get('source_name') or article.get('source') or 'Unknown'
            cursor.execute('INSERT OR IGNORE INTO Sources (name) VALUES (?)', (source_name,))

            cursor.execute('''
                INSERT OR IGNORE INTO Articles (title, link, content, date, category, sentiment_score, sentiment_label, source_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, (SELECT id FROM Sources WHERE name = ?))
            ''', (
                article.get('title'),
                article.get('link'),
                article.get('content'),
                article.get('date'),
                article.get('category'),
                article.get('sentiment_score', 0.0),
                article.get('sentiment_label', 'Neutral'),
                source_name,
            ))

            if cursor.rowcount > 0:
                saved_count += 1

            cursor.execute('SELECT id FROM Articles WHERE link = ?', (article.get('link'),))
            row = cursor.fetchone()
            if not row:
                continue
            article_id = row[0]

            for kw in article.get('keywords', []):
                cursor.execute('INSERT OR IGNORE INTO Keywords (word) VALUES (?)', (kw,))
                cursor.execute('SELECT id FROM Keywords WHERE word = ?', (kw,))
                kw_row = cursor.fetchone()
                if not kw_row:
                    continue
                kw_id = kw_row[0]
                cursor.execute('INSERT OR IGNORE INTO Article_Keyword (article_id, keyword_id) VALUES (?, ?)', (article_id, kw_id))
        except sqlite3.Error as exc:
            logging.error(f'SP3 SQLite error for article {article.get("link")}: {exc}')

    conn.commit()
    conn.close()
    logging.info(f'SP3: Saved {saved_count} new articles into SQLite.')


def export_database_to_files():
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            Articles.id,
            Articles.date,
            Articles.title,
            Articles.link,
            Sources.name as source_name,
            Articles.category,
            Articles.sentiment_score,
            Articles.sentiment_label,
            COALESCE(group_concat(Keywords.word, ', '), '') as keywords
        FROM Articles
        LEFT JOIN Sources ON Articles.source_id = Sources.id
        LEFT JOIN Article_Keyword ON Articles.id = Article_Keyword.article_id
        LEFT JOIN Keywords ON Article_Keyword.keyword_id = Keywords.id
        GROUP BY Articles.id
        ORDER BY Articles.date ASC, Articles.id ASC
    ''')

    rows = cursor.fetchall()
    conn.close()

    fieldnames = ['id', 'date', 'title', 'link', 'source_name', 'category', 'sentiment_score', 'sentiment_label', 'keywords']
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    if not rows:
        logging.warning('SP3/SP6: No rows found to export.')
        return

    csv_path = os.path.join(backup_dir, CSV_BACKUP)
    json_path = os.path.join(backup_dir, JSON_BACKUP)

    with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(fieldnames)
        writer.writerows(rows)

    records = []
    for row in rows:
        record = dict(zip(fieldnames, row))
        if not record.get('date'):
            record['date'] = 'Unknown'
        if not record.get('category'):
            record['category'] = 'Supply Chain'
        records.append(record)

    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(records, json_file, ensure_ascii=False, indent=4)

    logging.info(f'SP3/SP6: Exported normalized {CSV_BACKUP} and {JSON_BACKUP}.')
