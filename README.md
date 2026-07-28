GlobalPulse AI: Multilingual News Aggregator & Sentiment Analysis Dashboard

Project ID: TEC004/02
Domain: Semiconductor Supply Chain Intelligence

1. Overview

GlobalPulse AI is an enterprise-grade data pipeline that automatically crawls, cleans, analyzes, and visualizes global news related to the semiconductor industry. It utilizes multi-threading for rapid ingestion, Generative AI for sentiment scoring, and a Zero-Server Single Page Application (SPA) for the frontend dashboard.

2. System Requirements & Dependencies

OS: Windows / macOS / Linux

Python: Version 3.9 or higher

Key Dependencies: requests, beautifulsoup4, pandas, matplotlib, google-generativeai (Refer to requirements.txt for the full list).

3. Installation Steps

Extract the ZIP archive: GlobalPulse_TEC004_02.zip

Open your terminal/command prompt and navigate to the extracted directory.

Install the required Python packages:

pip install -r requirements.txt


4. Execution Procedures

There are two ways to execute the backend pipeline:

Option A: Full System Reset (Recommended for clean run)
This will wipe the existing database and reports, then run a fresh extraction:

python reset_and_run.py


Option B: Standard Execution
This will run the pipeline and append new data to the existing database:

python main.py


5. Sample Usage & Frontend Dashboard

Upon running the backend pipeline, the crawlers/ module will fetch targeted articles.

Processed relational data is saved to news_database.db.

Automated CSV/JSON backups and charts will be generated in the reports/ folder.

To view the Dashboard: Simply double-click index.html to open it in any modern web browser (Chrome/Edge). The dashboard uses Vanilla JS to fetch the exported JSON/CSV data directly, requiring no local backend server.
