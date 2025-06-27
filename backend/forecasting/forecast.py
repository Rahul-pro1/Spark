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
    print("[TRAIN] Original data shape:", df.shape)

    df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
    df['past_7_day_avg'] = df.groupby(['store_id', 'sku_id'])['units_sold'].transform(
        lambda x: x.shift(1).rolling(7).mean()
    )

    print("[TRAIN] Before dropna shape:", df.shape)
    df = df.dropna()
    print("[TRAIN] After dropna shape:", df.shape)

    features = ['day_of_week', 'past_7_day_avg', 'temperature', 'social_mentions', 'news_mentions']
    X = df[features]
    y = df['units_sold']

    print("[TRAIN] Feature sample:\n", X.head())

    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, max_depth=5)
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)
    print(f"[TRAIN] Model saved to {MODEL_PATH}")

    corr = df[features + ['units_sold']].corr()
    sns.heatmap(corr, annot=True)
    plt.title("Feature Correlation with Units Sold")
    plt.tight_layout()
    plt.savefig("feature_correlation.png")
    print("[TRAIN] Saved correlation heatmap to feature_correlation.png")


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
        print(f"[FORECAST] Not enough history for SKU {sku_id}. Only {len(sku_history)} rows found.")
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

    print("[FORECAST] Features for prediction:\n", features)

    if not os.path.exists(MODEL_PATH):
        print("[FORECAST] Model not found. Train the model first.")
        return 0, 0

    model = joblib.load(MODEL_PATH)
    prediction = model.predict(features)[0]
    confidence = min(100, len(sku_history) * 2)

    print(f"[FORECAST] Predicted demand: {prediction:.2f}, Confidence: {confidence}%")

    return round(prediction), round(confidence)


def extract_signal(signal_type, context_docs):
    signal = 0
    for doc in context_docs:
        text = doc.payload.get("text", "").lower()
        if signal_type == "temperature" and "°" in text:
            try:
                temp_val = int("".join(filter(str.isdigit, text.split("°")[0][-3:])))
                signal = max(signal, temp_val)
            except Exception as e:
                continue
        elif signal_type == "social" and "tweet" in text:
            signal += 1
        elif signal_type == "news":
            if "breaking" in text or "alert" in text:
                signal += 1
    return signal


if __name__ == "__main__":
    print("[MAIN] Loading historical POS data...")
    historical_df = pd.read_csv("pos_data/pos_data.csv")
    print("[MAIN] Training model...")
    train_model(historical_df)
