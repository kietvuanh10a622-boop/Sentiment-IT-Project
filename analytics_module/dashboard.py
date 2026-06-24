import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
import logging
from wordcloud import WordCloud

# Configure font and style for Matplotlib to make charts look professional
plt.style.use('ggplot')
plt.rcParams['figure.figsize'] = (10, 6)

def ensure_report_dir():
    """Create 'reports' directory to save charts if it doesn't exist."""
    if not os.path.exists('reports'):
        os.makedirs('reports')

def fetch_and_clean_data():
    """Use Pandas to read data from SQLite and clean it (SP5 - Data Pipeline)"""
    try:
        # Connect to DB
        conn = sqlite3.connect('news_database.db')
        
        # Read data into Pandas DataFrame
        df = pd.read_sql_query("SELECT * FROM Articles", conn)
        conn.close()

        if df.empty:
            logging.warning("Database is empty, cannot analyze.")
            return None

        # Clean data (Pandas Pipeline)
        # 1. Remove duplicate articles (Deduplication)
        if 'title' in df.columns:
            df = df.drop_duplicates(subset=['title'])
        
        # 2. Handle missing values in sentiment_score column
        if 'sentiment_score' in df.columns:
            df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
            df = df.dropna(subset=['sentiment_score'])

            # 3. Create Sentiment Label column from Score
            def categorize(score):
                if score > 0.1: return 'Positive'
                elif score < -0.1: return 'Negative'
                else: return 'Neutral'
                
            df['sentiment_label'] = df['sentiment_score'].apply(categorize)
        else:
            logging.error(f"Missing 'sentiment_score' column. Available columns: {list(df.columns)}")
            return None
            
        return df
    except Exception as e:
        logging.error(f"Error processing Pandas: {e}")
        return None

def plot_source_comparison(df):
    """Bar chart comparing sentiment between news sources (VnExpress vs BBC)"""
    # Dynamically check for the source column name to prevent KeyError
    source_col = None
    for col in ['source_name', 'source', 'Source', 'SourceName']:
        if col in df.columns:
            source_col = col
            break
            
    if not source_col:
        logging.error(f"Cannot plot source comparison. Missing source column. Available columns: {list(df.columns)}")
        return

    if 'sentiment_label' not in df.columns:
        logging.error("Missing 'sentiment_label' column.")
        return

    # Group by news source and sentiment label
    source_sentiment = df.groupby([source_col, 'sentiment_label']).size().unstack(fill_value=0)
    
    # Draw stacked bar chart
    ax = source_sentiment.plot(kind='bar', stacked=True, colormap='viridis')
    plt.title('Sentiment Distribution by News Source', fontsize=14, fontweight='bold')
    plt.xlabel('News Source', fontsize=12)
    plt.ylabel('Number of Articles', fontsize=12)
    plt.xticks(rotation=0)
    plt.legend(title='Sentiment')
    
    # Save high-quality image for the Technical Report
    plt.tight_layout()
    plt.savefig('reports/01_source_comparison.png', dpi=300)
    plt.close()
    logging.info("Successfully exported chart: reports/01_source_comparison.png")

def plot_sentiment_distribution(df):
    """Overall sentiment score distribution chart"""
    if 'sentiment_score' not in df.columns:
        return

    plt.hist(df['sentiment_score'], bins=20, color='skyblue', edgecolor='black')
    plt.title('Overall Sentiment Score Distribution', fontsize=14, fontweight='bold')
    plt.xlabel('Sentiment Score (-1.0 to 1.0)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    
    plt.tight_layout()
    plt.savefig('reports/02_sentiment_distribution.png', dpi=300)
    plt.close()
    logging.info("Successfully exported chart: reports/02_sentiment_distribution.png")

def plot_topic_wordcloud(df):
    """Generate Word Cloud from article titles"""
    if 'title' not in df.columns:
        logging.error("Missing 'title' column for WordCloud.")
        return

    text = " ".join(title for title in df['title'].astype(str))
    
    # Generate WordCloud
    wordcloud = WordCloud(width=800, height=400, background_color='white', 
                          colormap='inferno', max_words=100).generate(text)
    
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off') # Turn off axis
    plt.title('Trending Topics Word Cloud', fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('reports/03_topic_wordcloud.png', dpi=300)
    plt.close()
    logging.info("Successfully exported chart: reports/03_topic_wordcloud.png")

def generate_analytics_dashboard():
    """Main function to run the entire SP5 pipeline"""
    logging.info("--- STEP F: START DATA ANALYSIS & VISUALIZATION (SP5) ---")
    ensure_report_dir()
    
    df = fetch_and_clean_data()
    if df is not None and not df.empty:
        plot_source_comparison(df)
        plot_sentiment_distribution(df)
        plot_topic_wordcloud(df)
        
        # Dynamically find the source column for statistical summary
        source_col = None
        for col in ['source_name', 'source', 'Source', 'SourceName']:
            if col in df.columns:
                source_col = col
                break
        
        if source_col and 'sentiment_score' in df.columns:
            summary_stats = df.groupby(source_col)['sentiment_score'].describe()
            summary_stats.to_csv('reports/04_statistical_summary.csv')
        
        logging.info("--- FINISHED EXPORTING ANALYTICS DASHBOARD TO 'reports/' FOLDER ---")
    else:
        logging.warning("Not enough data to draw charts.")