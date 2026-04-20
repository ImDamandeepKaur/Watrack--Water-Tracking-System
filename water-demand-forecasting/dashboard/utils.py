import pandas as pd

class Analytics:

    def preprocess(self, df):
        df['date'] = pd.to_datetime(df['date'])
        return df

    def kpis(self, df):
        return {
            "total": df['daily_usage'].sum(),
            "avg": df['daily_usage'].mean(),
            "days": len(df),
            "latest": df.iloc[-1]['daily_usage']
        }

    def insights(self, df):
        max_day = df.loc[df['daily_usage'].idxmax()]
        min_day = df.loc[df['daily_usage'].idxmin()]
        return max_day, min_day
