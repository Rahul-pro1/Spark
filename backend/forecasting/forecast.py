import pandas as pd
import xgboost as xgb
import os
import joblib
import datetime
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json
import json

MODEL_PATH_XGB = "xgb_model.joblib"
MODEL_PATH_PROPHET_TEMPLATE = "prophet_model_{}.json"

def train_xgb_model(historical_df):
    df = historical_df.copy()
    df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
    df['past_7_day_avg'] = df.groupby(['store_id', 'product_id'])['quantity'].transform(
        lambda x: x.shift(1).rolling(7).mean()
    )
    df = df.dropna()
    features = ['day_of_week', 'past_7_day_avg', 'temperature', 'social_mentions', 'news_mentions']
    X = df[features]
    y = df['quantity']
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, max_depth=5)
    model.fit(X, y)
    joblib.dump(model, MODEL_PATH_XGB)

def train_prophet_model(historical_df, sku_id):
    sku_df = historical_df[historical_df["product_id"] == sku_id].copy()
    if len(sku_df) < 7:
        return None
    df = sku_df[["date", "quantity", "temperature", "social_mentions", "news_mentions"]].copy()
    df["ds"] = pd.to_datetime(df["date"])
    df["y"] = df["quantity"]
    df = df[["ds", "y", "temperature", "social_mentions", "news_mentions"]]
    model = Prophet()
    model.add_regressor("temperature")
    model.add_regressor("social_mentions")
    model.add_regressor("news_mentions")
    model.fit(df)
    model_path = MODEL_PATH_PROPHET_TEMPLATE.format(sku_id)
    with open(model_path, "w") as f:
        f.write(model_to_json(model))
    return model

def forecast_sku_demand(sku_id, signals, historical_df):
    temperature = signals.get("temperature", 25)
    social_mentions = signals.get("social_mentions", 1)
    news_mentions = signals.get("news_mentions", 1)
    today = pd.to_datetime(datetime.datetime.today().date())
    model_path = MODEL_PATH_PROPHET_TEMPLATE.format(sku_id)

    try:
        if not os.path.exists(model_path):
            model = train_prophet_model(historical_df, sku_id)
        else:
            with open(model_path, "r") as f:
                model = model_from_json(json.load(f))

        future = pd.DataFrame([{
            "ds": today,
            "temperature": temperature,
            "social_mentions": social_mentions,
            "news_mentions": news_mentions
        }])

        forecast = model.predict(future)
        yhat = forecast["yhat"].iloc[0]
        return round(yhat), 90

    except Exception as e:
        if not os.path.exists(MODEL_PATH_XGB):
            train_xgb_model(historical_df)
        df = historical_df.copy()
        df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
        df['past_7_day_avg'] = df.groupby(['store_id', 'product_id'])['quantity'].transform(
            lambda x: x.shift(1).rolling(7).mean()
        )
        df = df.dropna()
        sku_df = df[df["product_id"] == sku_id].sort_values("date")
        if len(sku_df) < 7:
            past_7_day_avg = sku_df["quantity"].mean()
            confidence = 20
        else:
            past_7_day_avg = sku_df.tail(7)["quantity"].mean()
            confidence = min(100, len(sku_df) * 2)
        day_of_week = today.weekday()
        features = pd.DataFrame([{
            "day_of_week": day_of_week,
            "past_7_day_avg": past_7_day_avg,
            "temperature": temperature,
            "social_mentions": social_mentions,
            "news_mentions": news_mentions
        }])
        model = joblib.load(MODEL_PATH_XGB)
        prediction = model.predict(features)[0]
        return round(prediction), round(confidence)
