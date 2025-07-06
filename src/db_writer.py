# db_writer.py
import sqlite3

def init_db(db_path="european_food_prices.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT,
            product TEXT,
            price_local REAL,
            price_eur REAL,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_dataframe(df, db_path="european_food_prices.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO food_prices (country, product, price_local, price_eur, date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            row["Country"],
            row["Product"],
            row["Price (Local Currency)"],
            row["Price (EUR)"],
            row["Date"]
        ))
    conn.commit()
    conn.close()
    print(f"🗃 Данные сохранены в базу данных: {db_path}")
