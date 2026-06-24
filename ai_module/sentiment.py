# ai_module/sentiment.py
import logging
import time
import json
import google.generativeai as genai

# ĐIỀN GEMINI API KEY CỦA BẠN VÀO ĐÂY (Lấy miễn phí tại aistudio.google.com)
GEMINI_API_KEY = "AQ.Ab8RN6LbmruohNrKxSHoi-GavGHz_E9eMRehz1blUc6EjILKDg"
genai.configure(api_key=GEMINI_API_KEY)

# Sử dụng gemini-1.5-flash (Tốc độ cực nhanh, giá rẻ/miễn phí, hoàn hảo cho Data Pipeline)
# Hoặc đổi thành 'gemini-1.5-pro' nếu bạn muốn suy luận cực sâu
MODEL_NAME = 'gemini-1.5-flash'

def call_gemini_sentiment_api(text_to_analyze):
    """
    Gọi Gemini API để phân tích cảm xúc bài báo với JSON Schema nghiêm ngặt.
    """
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            # Ép Gemini bắt buộc phải trả về JSON để không làm vỡ Data Pipeline
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Thiết kế Prompt đóng vai chuyên gia tài chính/công nghệ
        prompt = f"""
        Bạn là một chuyên gia phân tích thị trường công nghệ và bán dẫn. 
        Hãy phân tích cảm xúc (sentiment) của tiêu đề bài báo sau đây.
        Trả về kết quả ĐÚNG định dạng JSON với 2 key sau, không kèm giải thích gì thêm:
        - "label": Chỉ chọn 1 trong 3 chữ "Positive", "Negative", hoặc "Neutral".
        - "score": Điểm số (float) từ -1.0 (rất tiêu cực) đến 1.0 (rất tích cực). 0.0 là trung tính.
        
        Tiêu đề báo: "{text_to_analyze}"
        """
        
        response = model.generate_content(prompt)
        
        # Chuyển đổi chuỗi JSON mà Gemini trả về thành Dictionary của Python
        result = json.loads(response.text)
        
        label = result.get('label', 'Neutral').capitalize()
        score = float(result.get('score', 0.0))
        
        # Chuẩn hóa để chống lỗi nếu Gemini lỡ sinh ra nhãn lạ
        if label not in ['Positive', 'Negative', 'Neutral']:
            label = 'Neutral'
            
        return {"score": score, "label": label}
        
    except Exception as e:
        logging.error(f"Lỗi khi gọi Gemini API: {e}")
        return None

def get_sentiment(text, source_name):
    """
    Hàm xử lý chính (Đã lược bỏ khâu dịch thuật vì Gemini hiểu tiếng Việt xuất sắc)
    """
    if not text:
        return {"score": 0.0, "label": "Neutral"}

    try:
        # BỎ QUA BƯỚC DỊCH THUẬT: Đưa thẳng văn bản gốc (cả Anh lẫn Việt) vào Gemini
        api_result = call_gemini_sentiment_api(text)
        
        if api_result:
            return api_result
            
        # FALLBACK: Nếu API Google quá tải hoặc hết Quota, dùng thuật toán Keyword nội bộ
        else:
            logging.info("Sử dụng Fallback Keyword-based do Gemini API lỗi...")
            lower_text = text.lower()
            positive_words = ['surge', 'growth', 'profit', 'up', 'build', 'new', 'innovation', 'invest', 'revenue', 'tăng', 'lãi', 'đột phá', 'phát triển', 'xây']
            negative_words = ['drop', 'fall', 'shortage', 'crisis', 'down', 'loss', 'delay', 'cut', 'ban', 'risk', 'giảm', 'lỗ', 'khủng hoảng', 'cấm', 'thiếu hụt']
            
            pos_count = sum(1 for word in positive_words if word in lower_text)
            neg_count = sum(1 for word in negative_words if word in lower_text)
            
            if pos_count > neg_count:
                return {"score": 0.65, "label": "Positive"}
            elif neg_count > pos_count:
                return {"score": -0.65, "label": "Negative"}
            else:
                return {"score": 0.0, "label": "Neutral"}

    except Exception as e:
        logging.error(f"Lỗi Pipeline Sentiment: {e}")
        return {"score": 0.0, "label": "Neutral"}

def apply_sentiment_analysis(articles):
    """
    Nhận danh sách bài báo, áp dụng phân tích cảm xúc từ Gemini cho từng bài.
    """
    logging.info("--- BƯỚC C2: KẾT NỐI GOOGLE GEMINI 1.5 API ---")
    analyzed_articles = []
    
    total_articles = len(articles)
    for index, article in enumerate(articles):
        if (index + 1) % 5 == 0 or index == 0:
            logging.info(f"Đang gửi bài {index + 1}/{total_articles} lên Google AI Cloud...")
        
        text_to_analyze = article.get('title', '')
        source_name = article.get('source_name', 'Unknown')
        
        sentiment_result = get_sentiment(text_to_analyze, source_name)
        
        article['sentiment_score'] = sentiment_result['score']
        article['sentiment_label'] = sentiment_result['label'] 
        
        analyzed_articles.append(article)
        
        # Tránh bị Rate Limit (Tối đa 15 request/phút với tier miễn phí của Gemini)
        # Khuyên dùng time.sleep(4) nếu dữ liệu quá nhiều
        time.sleep(2) 
        
    logging.info("--- HOÀN THÀNH GỌI GEMINI API ---")
    return analyzed_articles