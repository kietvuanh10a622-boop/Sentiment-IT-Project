import sqlite3
import pandas as pd
import json
import os
import logging
from datetime import datetime

def generate_daily_report():
    """SP6: Generates automated daily summaries in JSON/CSV and drafts the Technical Report."""
    logging.info("--- STEP G: START AUTOMATED DAILY REPORTING (SP6) ---")
    if not os.path.exists('reports'):
        os.makedirs('reports')

    try:
        # Connect to Database
        conn = sqlite3.connect('news_database.db')
        df = pd.read_sql_query("SELECT * FROM Articles", conn)
        conn.close()

        if df.empty:
            logging.warning("Database is empty. Cannot generate daily report.")
            return

        # 1. CALCULATE DAILY STATISTICS
        today_str = datetime.now().strftime('%Y-%m-%d')
        source_col = next((col for col in ['source_name', 'source', 'Source'] if col in df.columns), 'Unknown_Source')
        total_articles = len(df)
        
        # Ensure sentiment data exists for calculations
        if 'sentiment_score' in df.columns:
            df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
            
            def categorize(score):
                if pd.isna(score): return 'Neutral'
                if score > 0.1: return 'Positive'
                elif score < -0.1: return 'Negative'
                return 'Neutral'
                
            if 'sentiment_label' not in df.columns:
                df['sentiment_label'] = df['sentiment_score'].apply(categorize)
                
            positive_count = len(df[df['sentiment_label'] == 'Positive'])
            negative_count = len(df[df['sentiment_label'] == 'Negative'])
            neutral_count = len(df[df['sentiment_label'] == 'Neutral'])
            avg_score = df['sentiment_score'].mean()
        else:
            positive_count = negative_count = neutral_count = 0
            avg_score = 0.0

        source_stats = df.groupby(source_col).size().to_dict() if source_col != 'Unknown_Source' else {}

        # 2. EXPORT TO JSON (SP6 Requirement)
        daily_summary = {
            "date": today_str,
            "total_articles_crawled": total_articles,
            "sentiment_breakdown": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            },
            "average_sentiment_score": round(avg_score, 3),
            "articles_by_source": source_stats
        }

        json_path = f'reports/daily_summary_{today_str}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(daily_summary, f, ensure_ascii=False, indent=4)
        logging.info(f"Exported JSON daily summary to: {json_path}")

        # 3. EXPORT TO CSV (SP6 Requirement - Daily Highlights)
        if 'sentiment_score' in df.columns:
            sorted_df = df.sort_values(by='sentiment_score', ascending=False)
            top_positive = sorted_df.head(10)
            top_negative = sorted_df.tail(10)
            
            highlights_df = pd.concat([top_positive, top_negative])
            csv_path = f'reports/daily_highlights_{today_str}.csv'
            highlights_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            logging.info(f"Exported CSV highlights to: {csv_path}")

        # 4. AUTO-GENERATE TECHNICAL REPORT DRAFT (Bonus for Top Grade)
        report_draft_path = 'reports/Technical_Report_Draft.txt'
        with open(report_draft_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("TECHNICAL REPORT - AUTO-GENERATED RESULTS SECTION\n")
            f.write("="*60 + "\n\n")
            f.write("4. Results and Evaluation\n")
            f.write("-" * 25 + "\n")
            f.write("4.1. Data Collection Results\n")
            f.write(f"The web scraping module successfully crawled a total of {total_articles} articles ")
            if source_stats:
                sources_str = ", ".join([f"{k} ({v} articles)" for k, v in source_stats.items()])
                f.write(f"from multiple sources including: {sources_str}.\n\n")
            else:
                f.write(".\n\n")
                
            f.write("4.2. Sentiment Analysis Results\n")
            f.write("Using the NLP pipeline and translation APIs, the system analyzed the sentiment of all crawled articles. ")
            f.write(f"The overall average sentiment score across all articles is {avg_score:.3f}. ")
            f.write("The distribution of sentiment is as follows:\n")
            
            if total_articles > 0:
                f.write(f"- Positive Articles: {positive_count} ({positive_count/total_articles*100:.1f}%)\n")
                f.write(f"- Negative Articles: {negative_count} ({negative_count/total_articles*100:.1f}%)\n")
                f.write(f"- Neutral Articles: {neutral_count} ({neutral_count/total_articles*100:.1f}%)\n\n")
            
            f.write("4.3. Visual Aids and Charts Integration\n")
            f.write("Please copy the generated images from the 'reports/' folder into your Word document:\n")
            f.write("- Insert '01_source_comparison.png' to show the contrast between news sources.\n")
            f.write("- Insert '02_sentiment_distribution.png' to illustrate the overall mood.\n")
            f.write("- Insert '03_topic_wordcloud.png' to highlight the most frequent keywords in the news.\n\n")
            
            f.write("4.4. Conclusion on Experimental Findings\n")
            if avg_score > 0.05:
                f.write("Based on the experimental findings, the general public opinion and news coverage currently lean towards a POSITIVE sentiment.\n")
            elif avg_score < -0.05:
                f.write("Based on the experimental findings, the general public opinion and news coverage currently lean towards a NEGATIVE sentiment.\n")
            else:
                f.write("Based on the experimental findings, the general public opinion and news coverage remain largely NEUTRAL.\n")
            
        logging.info(f"Generated Technical Report Draft at: {report_draft_path}")

    except Exception as e:
        logging.error(f"Error in SP6 module: {e}")