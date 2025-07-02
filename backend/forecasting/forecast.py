import pandas as pd
import xgboost as xgb
import os
import joblib
import datetime
import matplotlib.pyplot as plt
import seaborn as sns

MODEL_PATH = "xgb_model.joblib"

def train_model(historical_df):
    df = historical_df.copy()
    df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
    df['past_7_day_avg'] = df.groupby(['store_id', 'sku_id'])['units_sold'].transform(
        lambda x: x.shift(1).rolling(7).mean()
    )
    df = df.dropna()
    features = ['day_of_week', 'past_7_day_avg', 'temperature', 'social_mentions', 'news_mentions']
    X = df[features]
    y = df['units_sold']
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, max_depth=5)
    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)

def forecast_sku_demand(sku_id, context_docs, historical_df):
    temperature = extract_signal("temperature", context_docs)
    social_mentions = extract_signal("social", context_docs)
    news_mentions = extract_signal("news", context_docs)
    temperature = temperature or 25
    social_mentions = social_mentions or 1
    news_mentions = news_mentions or 1
    sku_history = historical_df[historical_df["sku_id"] == sku_id].copy()
    sku_history = sku_history.sort_values("date")

    if len(sku_history) < 7:
        past_7_day_avg = sku_history['units_sold'].mean()
        confidence = 20
    else:
        past_7_day_avg = sku_history.tail(7)['units_sold'].mean()
        confidence = min(100, len(sku_history) * 2)
    today = datetime.datetime.today()
    day_of_week = today.weekday()
    features = pd.DataFrame([{
        "day_of_week": day_of_week,
        "past_7_day_avg": past_7_day_avg,
        "temperature": temperature,
        "social_mentions": social_mentions,
        "news_mentions": news_mentions
    }])
    
    if not os.path.exists(MODEL_PATH):
        train_model(historical_df)
    model = joblib.load(MODEL_PATH)
    prediction = model.predict(features)[0]
    return round(prediction), round(confidence)

def extract_signal(signal_type, context_docs):
    signal = 0
    for doc in context_docs:
        text = doc.payload.get("text", "").lower()
        source = doc.payload.get("source", "")
        if signal_type == "temperature" and "temperature" in text:
            try:
                temp = int("".join(filter(str.isdigit, text.split("temperature")[1][:5])))
                signal = max(signal, temp)
            except: pass
        elif signal_type == "social" and source == "reddit":
            signal += 1
        elif signal_type == "news" and source == "news":
            signal += 1
    return signal or 1
