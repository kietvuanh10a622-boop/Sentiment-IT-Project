import json
import logging
import numpy as np
import pandas as pd
from datetime import timedelta


def calculate_daily_nsr(df):
    if df.empty:
        return pd.DataFrame(columns=['category', 'date', 'positive', 'negative', 'neutral', 'nsr'])

    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    df = df.dropna(subset=['date'])
    df['sentiment_label'] = df['sentiment_label'].fillna('Neutral')

    def nsr(group):
        total = len(group)
        if total == 0:
            return 0.0
        pos = (group['sentiment_label'] == 'Positive').sum()
        neg = (group['sentiment_label'] == 'Negative').sum()
        return float(pos - neg) / total

    grouped = df.groupby(['category', 'date']).apply(lambda g: pd.Series({
        'positive': (g['sentiment_label'] == 'Positive').sum(),
        'negative': (g['sentiment_label'] == 'Negative').sum(),
        'neutral': (g['sentiment_label'] == 'Neutral').sum(),
        'nsr': nsr(g)
    })).reset_index()

    return grouped


def forecast_category(category_df, horizon_days=14):
    if category_df.empty:
        return []

    data = category_df.sort_values('date').copy()
    data['ordinal'] = data['date'].map(lambda d: d.toordinal())

    if len(data) >= 3:
        x = data['ordinal'].values.reshape(-1, 1)
        y = data['nsr'].values
        slope, intercept = np.polyfit(x.flatten(), y, 1)
        last_date = data['date'].max()
        forecasts = []
        for i in range(1, horizon_days + 1):
            future_date = last_date + timedelta(days=i)
            pred = slope * future_date.toordinal() + intercept
            forecasts.append({
                'date': future_date.strftime('%Y-%m-%d'),
                'predicted_nsr': float(np.clip(pred, -1.0, 1.0))
            })
        return forecasts

    last_nsr = float(data['nsr'].iloc[-1])
    forecasts = []
    last_date = data['date'].max()
    for i in range(1, horizon_days + 1):
        future_date = last_date + timedelta(days=i)
        forecasts.append({
            'date': future_date.strftime('%Y-%m-%d'),
            'predicted_nsr': last_nsr
        })
    return forecasts


def generate_trend_predictions(articles, output_path='trend_predictions.json', horizon_days=14):
    if not articles:
        logging.warning('No articles available for trend forecasting.')
        return {}

    df = pd.DataFrame(articles)
    if df.empty:
        logging.warning('Forecasting skipped because DataFrame is empty.')
        return {}

    if 'category' not in df.columns or 'date' not in df.columns or 'sentiment_label' not in df.columns:
        logging.error('Forecasting input data missing required columns.')
        return {}

    daily_nsr = calculate_daily_nsr(df)
    categories = daily_nsr['category'].unique()
    output = {}

    for category in categories:
        category_df = daily_nsr[daily_nsr['category'] == category].copy()
        category_df['date'] = pd.to_datetime(category_df['date']).dt.date
        historical = [
            {'date': row['date'].strftime('%Y-%m-%d'), 'nsr': float(row['nsr'])}
            for _, row in category_df.iterrows()
        ]
        forecast = forecast_category(category_df, horizon_days=horizon_days)
        output[category] = {
            'historical': historical,
            'forecast': forecast
        }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    logging.info(f'SP5 Advanced: Exported trend forecasts to {output_path}.')
    return output
