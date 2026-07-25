# ai_module/sentiment.py
import json
import logging
import os
import time

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - environment-dependent
    genai = None

# Sử dụng biến môi trường để tránh hardcode secret và giữ pipeline an toàn khi không có API key.
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-1.5-flash')

if genai is not None and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as exc:  # pragma: no cover - network/config dependent
        logging.warning(f'Unable to configure Gemini SDK: {exc}')
        genai = None
elif GEMINI_API_KEY:
    logging.warning('Google Generative AI SDK is unavailable; using keyword fallback sentiment analysis.')
else:
    logging.info('No Gemini API key configured; using keyword fallback sentiment analysis.')


def call_gemini_sentiment_api(text_to_analyze):
    """Gọi Gemini API khi SDK và API key sẵn sàng; nếu không thì trả về None để dùng fallback."""
    if genai is None or not GEMINI_API_KEY:
        return None

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config={"response_mime_type": "application/json"}
        )

        prompt = f"""
        Bạn là một chuyên gia phân tích thị trường công nghệ và bán dẫn.
        Hãy phân tích cảm xúc (sentiment) của tiêu đề bài báo sau đây.
        Trả về đúng định dạng JSON với 2 key sau, không kèm giải thích gì thêm:
        - "label": Chỉ chọn 1 trong 3 chữ "Positive", "Negative", hoặc "Neutral".
        - "score": Điểm số (float) từ -1.0 đến 1.0.

        Tiêu đề báo: "{text_to_analyze}"
        """

        response = model.generate_content(prompt)
        result = json.loads(response.text)

        label = str(result.get('label', 'Neutral')).strip().title()
        if label == 'Neutral'.title():
            label = 'Neutral'
        score = float(result.get('score', 0.0))

        # Validate sentiment label against allowed values
        if label not in ['Positive', 'Negative', 'Neutral']:
            label = 'Neutral'
        
        # Ensure score is within valid range
        score = max(-1.0, min(1.0, float(score)))

        return {"score": score, "label": label}

    except Exception as exc:
        logging.warning(f'Gemini API unavailable, using internal fallback: {exc}')
        return None


def _keyword_fallback_sentiment(text):
    """Fallback nội bộ cho trường hợp API không khả dụng; tối ưu cho pipeline không-server."""
    if not text:
        return {"score": 0.0, "label": "Neutral"}

    lower_text = text.lower()
    positive_words = [
        'surge', 'growth', 'profit', 'up', 'build', 'new', 'innovation', 'invest', 'revenue',
        'tăng', 'lãi', 'đột phá', 'phát triển', 'xây', 'thành công', 'mở rộng'
    ]
    negative_words = [
        'drop', 'fall', 'shortage', 'crisis', 'down', 'loss', 'delay', 'cut', 'ban', 'risk',
        'giảm', 'lỗ', 'khủng hoảng', 'cấm', 'thiếu hụt', 'ảnh hưởng', 'sụt'
    ]

    pos_count = sum(1 for word in positive_words if word in lower_text)
    neg_count = sum(1 for word in negative_words if word in lower_text)
    total_signal = pos_count + neg_count

    if total_signal == 0:
        return {"score": 0.0, "label": "Neutral"}

    raw_score = (pos_count - neg_count) / total_signal
    score = round(raw_score, 2)

    if score > 0:
        return {"score": score, "label": "Positive"}
    if score < 0:
        return {"score": score, "label": "Negative"}
    return {"score": 0.0, "label": "Neutral"}


def get_sentiment(text, source_name):
    """Hàm xử lý chính; ưu tiên Gemini khi có sẵn, còn lại dùng fallback keyword-based."""
    if not text:
        return {"score": 0.0, "label": "Neutral"}

    try:
        api_result = call_gemini_sentiment_api(text)
        if api_result:
            logging.debug(f'Gemini API succeeded for source {source_name}')
            return api_result

        # Fallback to keyword-based sentiment if API is unavailable
        logging.debug(f'Using keyword fallback for source {source_name}')
        return _keyword_fallback_sentiment(text)

    except Exception as exc:
        logging.error(f'Pipeline sentiment error: {exc}')
        logging.info(f'Falling back to keyword sentiment for source {source_name}')
        return _keyword_fallback_sentiment(text)


def apply_sentiment_analysis(articles):
    """Nhận danh sách bài báo, áp dụng phân tích cảm xúc với fallback an toàn."""
    logging.info('--- BƯỚC C2: KẾT NỐI GOOGLE GEMINI 1.5 API ---')
    analyzed_articles = []

    total_articles = len(articles)
    for index, article in enumerate(articles):
        if (index + 1) % 5 == 0 or index == 0:
            logging.info(f'Đang gửi bài {index + 1}/{total_articles} lên Google AI Cloud...')

        text_to_analyze = article.get('title', '')
        source_name = article.get('source_name', 'Unknown')

        sentiment_result = get_sentiment(text_to_analyze, source_name)
        article['sentiment_score'] = sentiment_result['score']
        article['sentiment_label'] = sentiment_result['label']
        analyzed_articles.append(article)

        # Giảm độ trễ cho pipeline để tránh kéo dài thời gian chạy khi dữ liệu lớn.
        if total_articles > 50:
            time.sleep(0.25)

    logging.info('--- HOÀN THÀNH GỌI GEMINI API ---')
    return analyzed_articles