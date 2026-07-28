# This file resets data when a bug occurs.






import os
import shutil
import logging
from main import main as run_main_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

def reset_and_run():
    logging.info("========== STARTING FULL PIPELINE RESET PROCESS ==========")

    # 1. Define the paths that need to be cleaned up
    db_file = "news_database.db"
    reports_dir = "reports"

    # 2. Remove the old SQLite database file
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            logging.info(f"[OK] Successfully removed the old database: '{db_file}'")
        except Exception as e:
            logging.error(f"[ERROR] Unable to delete database file: {e}. Please close any applications connected to the DB.")
    else:
        logging.info(f"[INFO] Database file not found: '{db_file}' (the system is already clean).")

    # 3. Clean up the old reports and charts directory (reports/)
    if os.path.exists(reports_dir):
        try:
            # Iterate through and remove all files inside the reports directory
            for filename in os.listdir(reports_dir):
                file_path = os.path.join(reports_dir, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            logging.info(f"[OK] Cleaned up the old files in directory: '{reports_dir}/'")
        except Exception as e:
            logging.error(f"[ERROR] Error cleaning the reports directory: {e}")
    else:
        logging.info(f"[INFO] Directory '{reports_dir}' does not exist (the system will create it automatically when run).")

    logging.info("[OK] THE SYSTEM HAS BEEN RESET TO ITS INITIAL STATE!")
    logging.info("==============================================================")
    
    # 4. Automatically call main() from main.py to start the new pipeline
    try:
        run_main_pipeline()
    except Exception as e:
        logging.error(f"[ERROR] An error occurred while triggering main.py again: {e}")

if __name__ == "__main__":
    reset_and_run()