import sqlite3

connection = sqlite3.connect("market_data.db")


connection.execute("""
    CREATE TABLE IF NOT EXISTS book_events (
        id INTEGER NOT NULL,
        session_id INTEGER NOT NULL,
        message_id INTEGER NOT NULL,
        event_index INTEGER NOT NULL,
        product_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        event_time TEXT NOT NULL,
        side TEXT NOT NULL,
        price TEXT NOT NULL,
        quantity TEXT NOT NULL,
        PRIMARY KEY (session_id, id),
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
""")

connection.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY,
        label TEXT,
        product_id TEXT NOT NULL,
        started_at TEXT,
        ended_at TEXT,
        status TEXT NOT NULL,
        message_count INTEGER,
        snapshot_row_count INTEGER,
        update_row_count INTEGER
    )
""")

connection.commit()


def insert_events_batch(connection, batch):
    with connection:
        connection.executemany("""
            INSERT INTO book_events (
                id, session_id, message_id, event_index,
                product_id, event_type, event_time,
                side, price, quantity
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)


def insert_session(connection, session):
    """Insert (label, product_id, started_at) and return the new session ID."""
    with connection:
        cursor = connection.execute("""
            INSERT INTO sessions (
                label, product_id, started_at, status
            )
            VALUES (?, ?, ?, 'recording')
        """, session)
    return cursor.lastrowid

def count_session_rows(connection, session_id, row_type: str | None = None) -> int:
    query = "SELECT COUNT(*) FROM book_events WHERE session_id = ?"
    parameters = [session_id]

    if row_type is not None:
        query += " AND event_type = ?"
        parameters.append(row_type)

    result = connection.execute(query, parameters)
    return result.fetchone()[0]

def get_boundary_time(connection, session_id, boundary):
    if boundary == "start":
        direction = "ASC"
        event_filter = "AND event_type = 'snapshot'"
    elif boundary == "end":
        direction = "DESC"
        event_filter = ""
    else:
        raise ValueError(f"Unknown boundary: {boundary!r}")

    row = connection.execute(
        f"""
        SELECT event_time
        FROM book_events
        WHERE session_id = ?
        {event_filter}
        ORDER BY id {direction}
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()

    return row[0] if row else None




def finish_collection(connection, session_id: int, snapshot_count: int, 
                      update_count: int, message_count: int):

    data_start = get_boundary_time(connection, session_id, boundary="start")
    data_end = get_boundary_time(connection, session_id, boundary="end")

    connection.execute(
    """UPDATE sessions
            SET snapshot_row_count = ?, 
                update_row_count = ?,
                started_at = ?,
                ended_at = ?,
                message_count = ?,
                status = "complete"
            WHERE id = ?
            """, 
            (snapshot_count, update_count, data_start, data_end, message_count, session_id)
    )
    connection.commit()




