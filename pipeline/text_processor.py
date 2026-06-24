# pipeline/text_processor.py
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Decorator: Đo lường thời gian thực thi của hàm (Yêu cầu SP2)
def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logging.info(f"Hàm '{func.__name__}' chạy mất {end - start:.4f} giây.")
        return result
    return wrapper

@timing_decorator
def clean_articles_pipeline(raw_articles):
    """Sử dụng lambda, map và filter để làm sạch dữ liệu (Yêu cầu SP2)"""
    logging.info("Bắt đầu đường ống làm sạch dữ liệu (SP2)...")
    
    # Lọc: Bỏ qua các bài báo không có tiêu đề (title rỗng)
    valid_articles = list(filter(lambda x: len(x.get('title', '').strip()) > 0, raw_articles))
    
    # Map: Làm sạch khoảng trắng thừa và chuẩn hóa chuỗi
    def clean_text(article):
        article['title'] = " ".join(article['title'].split())
        article['sentiment_score'] = None  # Chuẩn bị sẵn cột trống cho SP4 (AI)
        return article
        
    cleaned_articles = list(map(clean_text, valid_articles))
    logging.info(f"Đã làm sạch {len(cleaned_articles)} bài báo hợp lệ.")
    return cleaned_articles