import psycopg2
import os

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        self.cursor = self.conn.cursor()

    def fetch_data(self, user_id):
        self.cursor.execute(
            "SELECT * FROM water_usage WHERE user_id=%s ORDER BY date",
            (user_id,)
        )
        return self.cursor.fetchall()

    def insert_data(self, user_id, date, reading, usage, region):

        # 🔥 enforce single region per user
        self.cursor.execute(
            "SELECT region FROM water_usage WHERE user_id=%s LIMIT 1",
            (user_id,)
        )
        existing = self.cursor.fetchone()

        if existing and existing[0] != region:
            raise Exception(f"User already assigned to {existing[0]}")

        self.cursor.execute(
            "INSERT INTO water_usage VALUES (%s,%s,%s,%s,%s)",
            (user_id, date, reading, usage, region)
        )
        self.conn.commit()

    def delete_user(self, user_id):
        self.cursor.execute(
            "DELETE FROM water_usage WHERE user_id=%s",
            (user_id,)
        )
        self.conn.commit()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_usage (
                user_id INTEGER,
                date TEXT,
                meter_reading REAL,
                daily_usage REAL,
                region TEXT
            )
        """)
        self.conn.commit()
