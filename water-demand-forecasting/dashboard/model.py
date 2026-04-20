import pickle
import os
import numpy as np
from xgboost import XGBRegressor
from datetime import datetime

MODEL_FILE = "models/xgb_model.pkl"

class Model:

    def train(self, df):
        df['day'] = df['date'].dt.dayofweek
        df['region'] = df['region'].map({'North':0,'South':1,'East':2,'West':3})

        df['lag1'] = df['daily_usage'].shift(1)
        df['lag2'] = df['daily_usage'].shift(2)
        df = df.dropna()

        X = df[['day','region','lag1','lag2']]
        y = df['daily_usage']

        model = XGBRegressor()
        model.fit(X, y)

        os.makedirs("models", exist_ok=True)
        pickle.dump(model, open(MODEL_FILE, "wb"))

    def load(self):
        if os.path.exists(MODEL_FILE):
            return pickle.load(open(MODEL_FILE, "rb"))
        return None

    def predict(self, model, df):
        last = df.iloc[-1]
        lag1 = last['daily_usage']
        lag2 = df.iloc[-2]['daily_usage']

        region_map = {'North':0,'South':1,'East':2,'West':3}

        X = np.array([[datetime.now().weekday(),
                       region_map[last['region']],
                       lag1, lag2]])

        return model.predict(X)[0]
