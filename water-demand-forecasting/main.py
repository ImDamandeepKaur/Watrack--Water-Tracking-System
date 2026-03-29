import joblib 
import pandas as pd

model = joblib.load("../models/water_forecast_model.pkl")
def predict_tomorrow(input_data):

    df = pd.DataFrame([input_data])

    prediction = model.predict(df)

    return prediction[0]
    
input_data = {
    "day_of_week":2,
    "month":3,
    "week_of_year":12,
    "is_weekend":0,
    "lag_1":12000,
    "lag_2":11500,
    "lag_7":11800,
    "lag_14":11000,
    "rolling_3":11800,
    "rolling_7":11750,
    "rolling_14":11600,
    "region_East":0,
    "region_North":1,
    "region_South":0,
    "region_West":0
}
    
prediction = predict_tomorrow(input_data)

print("Predicted Water Consumption Tomorrow:", prediction, "liters")