# db_writer.py
import sqlite3

def init_db(db_path="european_food_prices.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Countries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Main table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_id INTEGER,
            product_id INTEGER,
            price_local REAL,
            price_eur REAL,
            date TEXT,
            FOREIGN KEY(country_id) REFERENCES countries(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
    conn.close()


def get_or_create_id(conn, table, name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    
    cursor.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
    conn.commit()
    return cursor.lastrowid


def insert_dataframe(df, db_path="european_food_prices.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        country_id = get_or_create_id(conn, "countries", row["Country"])
        product_id = get_or_create_id(conn, "products", row["Product"])
        cursor.execute("""
            INSERT INTO food_prices (country_id, product_id, price_local, price_eur, date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            country_id,
            product_id,
            row["Price (Local Currency)"],
            row["Price (EUR)"],
            row["Date"]
        ))

    conn.commit()
    conn.close()
    print(f"🗃 Saved to Sqlite db.")
