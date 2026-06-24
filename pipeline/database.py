# pipeline/database.py
import sqlite3
import json
import csv
import logging
from pipeline.text_processor import timing_decorator

DB_NAME = "news_database.db"

@timing_decorator
def initialize_database():
    """Khởi tạo cấu trúc các bảng với khóa ngoại (Foreign Keys) """
    logging.info("Đang thiết lập Lược đồ Cơ sở dữ liệu chuẩn hóa...")
    conn = sqlite3.connect(DB_NAME)
    
    # Bật tính năng ràng buộc khóa ngoại trong SQLite
    conn.execute("PRAGMA foreign_keys = 1")
    cursor = conn.cursor()
    
    # 1. Tạo bảng Sources
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            base_url TEXT
        )
    ''')
    
    # 2. Tạo bảng Articles (Có khóa ngoại source_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            content TEXT,
            date TEXT,
            category TEXT,
            sentiment_score REAL,
            source_id INTEGER,
            FOREIGN KEY (source_id) REFERENCES Sources(id) ON DELETE CASCADE
        )
    ''')

    # 3. Tạo bảng Keywords
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL
        )
    ''')

    # 4. Tạo bảng trung gian Article_Keyword (Quan hệ Nhiều - Nhiều)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Article_Keyword (
            article_id INTEGER,
            keyword_id INTEGER,
            PRIMARY KEY (article_id, keyword_id),
            FOREIGN KEY (article_id) REFERENCES Articles(id) ON DELETE CASCADE,
            FOREIGN KEY (keyword_id) REFERENCES Keywords(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    logging.info("Khởi tạo Database thành công!")

@timing_decorator
def save_articles_to_db(articles):
    """Lưu bài báo vào DB và tự động xử lý các bảng liên kết"""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = 1")
    cursor = conn.cursor()
    
    insert_count = 0
    
    for art in articles:
        try:
            # Bước A: Xử lý bảng Sources trước
            source_name = art.get('source', 'Unknown')
            cursor.execute("INSERT OR IGNORE INTO Sources (name) VALUES (?)", (source_name,))
            cursor.execute("SELECT id FROM Sources WHERE name = ?", (source_name,))
            source_id = cursor.fetchone()[0]
            
            # Bước B: Xử lý chèn bài báo vào bảng Articles
            cursor.execute('''
                INSERT OR IGNORE INTO Articles (title, link, content, category, sentiment_score, source_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (art['title'], art['link'], art.get('content', ''), art.get('category', 'General'), art.get('sentiment_score'), source_id))
            
            if cursor.rowcount > 0:
                insert_count += 1
                article_id = cursor.lastrowid
                
                # Bước C: (Tùy chọn) Xử lý Keywords nếu có
                keywords = art.get('keywords', [])
                for kw in keywords:
                    cursor.execute("INSERT OR IGNORE INTO Keywords (word) VALUES (?)", (kw,))
                    cursor.execute("SELECT id FROM Keywords WHERE word = ?", (kw,))
                    kw_id = cursor.fetchone()[0]
                    cursor.execute("INSERT OR IGNORE INTO Article_Keyword (article_id, keyword_id) VALUES (?, ?)", (article_id, kw_id))

        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lưu bài báo '{art['title']}': {e}")
            
    conn.commit()
    conn.close()
    logging.info(f"Hoàn tất! Đã chèn {insert_count} bài báo mới vào hệ thống.")

@timing_decorator
def export_database_to_files(json_file='articles_backup.json', csv_file='articles_backup.csv'):
    """Xuất file JSON/CSV từ CSDL """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Cho phép truy cập cột bằng tên
    cursor = conn.cursor()
    
    # Dùng câu lệnh JOIN để gom thông tin từ bảng Articles và Sources
    cursor.execute('''
        SELECT a.title, a.link, a.category, a.sentiment_score, s.name as source_name
        FROM Articles a
        JOIN Sources s ON a.source_id = s.id
    ''')
    rows = cursor.fetchall()
    
    # Chuyển đổi dữ liệu sang dạng List of Dictionaries
    data = [dict(row) for row in rows]
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    if data:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
    conn.close()
    logging.info("Đã xuất bản sao lưu ra file JSON và CSV thành công.")