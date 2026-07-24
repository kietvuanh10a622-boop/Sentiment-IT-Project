import json
import logging
from datetime import timedelta

import numpy as np
import pandas as pd


def calculate_daily_nsr(df):
    if df.empty:
        return pd.DataFrame(columns=['category', 'date', 'positive', 'negative', 'neutral', 'nsr'])

    frame = df.copy()
    frame['date'] = pd.to_datetime(frame['date'], errors='coerce').dt.date
    frame = frame.dropna(subset=['date'])
    frame['sentiment_label'] = frame['sentiment_label'].fillna('Neutral')

    summary = (
        frame.groupby(['category', 'date'])
        .agg(
            positive=('sentiment_label', lambda s: int((s == 'Positive').sum())),
            negative=('sentiment_label', lambda s: int((s == 'Negative').sum())),
            neutral=('sentiment_label', lambda s: int((s == 'Neutral').sum())),
        )
        .reset_index()
    )
    summary['total'] = summary['positive'] + summary['negative'] + summary['neutral']
    summary['nsr'] = summary.apply(lambda row: ((row['positive'] - row['negative']) / row['total']) if row['total'] else 0.0, axis=1)
    summary = summary[['category', 'date', 'positive', 'negative', 'neutral', 'nsr']]
    return summary


def forecast_category(category_df, horizon_days=14):
    if category_df.empty:
        return []

    data = category_df.sort_values('date').copy()
    data['ordinal'] = data['date'].map(lambda day: day.toordinal())

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

    required = {'category', 'date', 'sentiment_label'}
    if not required.issubset(df.columns):
        logging.error('Forecasting input data missing required columns.')
        return {}

    daily_nsr = calculate_daily_nsr(df)
    categories = sorted(daily_nsr['category'].dropna().unique().tolist()) or ['Other']
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

    with open(output_path, 'w', encoding='utf-8') as handle:
        json.dump(output, handle, ensure_ascii=False, indent=4)

    logging.info(f'SP5 Advanced: Exported trend forecasts to {output_path}.')
    return output
