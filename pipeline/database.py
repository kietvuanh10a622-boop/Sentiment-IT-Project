# pipeline/database.py
import os
import sqlite3
import logging
import csv
import json

DB_FILENAME = 'news_database.db'
CSV_BACKUP = 'articles_backup.csv'
JSON_BACKUP = 'articles_backup.json'


def get_database_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', DB_FILENAME))


def initialize_database():
    """Initialize SQLite schema for Sources, Articles, Keywords, and relations."""
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
            source_id INTEGER,
            FOREIGN KEY (source_id) REFERENCES Sources(id)
        )
    ''')

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
    """Persist articles and keyword relations in SQLite."""
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
                INSERT OR IGNORE INTO Articles (title, link, content, date, category, sentiment_score, source_id)
                VALUES (?, ?, ?, ?, ?, ?, (SELECT id FROM Sources WHERE name = ?))
            ''', (
                article.get('title'),
                article.get('link'),
                article.get('content'),
                article.get('date'),
                article.get('category'),
                article.get('sentiment_score', 0.0),
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
        except sqlite3.Error as e:
            logging.error(f'SP3 SQLite error for article {article.get("link")}: {e}')

    conn.commit()
    conn.close()
    logging.info(f'SP3: Saved {saved_count} new articles into SQLite.')


def export_database_to_files():
    """Export normalized CSV and JSON backups from SQLite."""
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

    fieldnames = ['id', 'date', 'title', 'link', 'source_name', 'category', 'sentiment_score', 'keywords']
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

    records = [dict(zip(fieldnames, row)) for row in rows]
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(records, json_file, ensure_ascii=False, indent=4)

    logging.info(f'SP3/SP6: Exported normalized {CSV_BACKUP} and {JSON_BACKUP}.')
