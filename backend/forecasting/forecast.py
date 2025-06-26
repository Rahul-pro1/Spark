import pandas as pd
import xgboost as xgb
import os
import joblib
import datetime

MODEL_PATH = "xgb_model.joblib"

def train_model(historical_df):
    """
    historical_df: pd.DataFrame with features like:
    ['store_id', 'sku_id', 'date', 'units_sold', 'temperature', 'social_mentions', 'news_mentions']
    """

    df = historical_df.copy()

    df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
    df['past_7_day_avg'] = df.groupby(['store_id', 'sku_id'])['units_sold'].transform(lambda x: x.shift(1).rolling(7).mean())
    df = df.dropna()

    features = ['day_of_week', 'past_7_day_avg', 'temperature', 'social_mentions', 'news_mentions']
    X = df[features]
    y = df['units_sold']

    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, max_depth=5)
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)


def forecast_sku_demand(sku_id, context_docs, historical_df):
    """
    Forecast demand for a SKU based on historical + RAG-based external data.
    """
    temperature = extract_signal("temperature", context_docs)
    social_mentions = extract_signal("social", context_docs)
    news_mentions = extract_signal("news", context_docs)

    sku_history = historical_df[historical_df["sku_id"] == sku_id].copy()
    sku_history = sku_history.sort_values("date")

    if len(sku_history) < 7:
        return 0, 0  

    past_7_day_avg = sku_history.tail(7)['units_sold'].mean()
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
        return 0, 0  

    model = joblib.load(MODEL_PATH)
    prediction = model.predict(features)[0]

    confidence = min(100, len(sku_history) * 2)  

    return round(prediction), round(confidence)


def extract_signal(signal_type, context_docs):
    signal = 0
    for doc in context_docs:
        text = doc.payload.get("text", "").lower()
        if signal_type == "temperature" and "°f" in text:
            try:
                temp_val = int("".join(filter(str.isdigit, text.split("°f")[0][-3:])))
                signal = max(signal, temp_val)
            except:
                continue
        elif signal_type == "social" and "tweet" in text:
            signal += 1
        elif signal_type == "news":
            signal += "breaking" in text or "alert" in text
    return signal

if __name__ == "__main__":
    historical_df = pd.read_csv("pos_data/pos_data.csv")
    train_model(historical_df)