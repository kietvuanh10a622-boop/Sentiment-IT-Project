# File này dùng để reset data khi gặp bug






import os
import shutil
import logging
from main import main as run_main_pipeline

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

def reset_and_run():
    logging.info("========== BẮT ĐẦU QUY TRÌNH RESET TOÀN BỘ PIPELINE ==========")

    # 1. Định nghĩa các đường dẫn cần dọn dẹp
    db_file = "news_database.db"
    reports_dir = "reports"

    # 2. Tiến hành xóa File Database SQLite cũ
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            logging.info(f"✔ Đã xóa thành công cơ sở dữ liệu cũ: '{db_file}'")
        except Exception as e:
            logging.error(f"❌ Không thể xóa file database: {e}. Vui lòng tắt các ứng dụng đang kết nối vào DB.")
    else:
        logging.info(f"ℹ Không tìm thấy cơ sở dữ liệu '{db_file}' (Hệ thống đã sạch).")

    # 3. Tiến hành dọn dẹp thư mục chứa báo cáo & biểu đồ cũ (reports/)
    if os.path.exists(reports_dir):
        try:
            # Duyệt qua và xóa toàn bộ file bên trong thư mục reports
            for filename in os.listdir(reports_dir):
                file_path = os.path.join(reports_dir, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            logging.info(f"✔ Đã dọn dẹp sạch sẽ các tệp tin cũ trong thư mục: '{reports_dir}/'")
        except Exception as e:
            logging.error(f"❌ Gặp lỗi khi dọn dẹp thư mục reports: {e}")
    else:
        logging.info(f"ℹ Thư mục '{reports_dir}' chưa tồn tại (Hệ thống sẽ tự động tạo mới khi chạy).")

    logging.info("✔ HỆ THỐNG ĐÃ ĐƯỢC RESET VỀ TRẠNG THÁI BAN ĐẦU!")
    logging.info("==============================================================")
    
    # 4. Tự động gọi hàm main() từ main.py để bắt đầu chạy pipeline mới
    try:
        run_main_pipeline()
    except Exception as e:
        logging.error(f"❌ Lỗi xảy ra khi kích hoạt chạy lại main.py: {e}")

if __name__ == "__main__":
    reset_and_run()