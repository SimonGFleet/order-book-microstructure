import sqlite3

connection = sqlite3.connect("market_data.db")


connection.execute("""
    CREATE TABLE IF NOT EXISTS updates (
        id INTEGER PRIMARY KEY,
        session_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        event_time TEXT NOT NULL,
        side TEXT NOT NULL,
        price TEXT NOT NULL,
        quantity TEXT NOT NULL
    )
""")
connection.commit()


def insert_update_batch(connection, batch):
    with connection:
        connection.executemany("""
            INSERT INTO updates (
            session_id, product_id, event_type,
            event_time, side, price, quantity) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, batch)



