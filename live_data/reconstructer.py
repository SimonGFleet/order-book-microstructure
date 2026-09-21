from dataclasses import dataclass
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from sortedcontainers import SortedDict
from storage import get_boundary_time
from live_book import liveBook, bookObvservation



class sessionReplay:
    def __init__(self, session_id: int, path: str):
        self.session_id = session_id
        self.path = path
        self.book = liveBook()
        self.start_time: datetime | None = None


    def get_book_events(self,
        connection: sqlite3.Connection,
        session_id: int,
        event_type: str,
        ) -> sqlite3.Cursor:
        return connection.execute(
            """
            SELECT *
            FROM book_events
            WHERE session_id = ?
            AND event_type = ?
            ORDER BY id
            """,
            (session_id, event_type),
        )


    def generate_replay(self, interval: int) -> list[bookObvservation]:
        '''Starts with the book after snapshots.
        fetches initial observation, processes updates, then gets next at a timely rate.'''
        if interval <= 0:
            raise ValueError("Use a positive interval!")
        
        next_observation = self.start_time
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row

        observations: list[bookObvservation] = []

        try: 
            cursor = self.get_book_events(connection=connection,
                                        session_id=self.session_id,
                                        event_type="update")

            for row in cursor:
                event_time = datetime.fromisoformat(row["event_time"])
                # check to see if we need to observe
                while next_observation < event_time:
                    observations.append(self.book.get_observation(next_observation))
                    next_observation += timedelta(milliseconds=interval)

                # then apply the update to the book
                self.book.apply_level(
                    side=row["side"], 
                    price=Decimal(row["price"]), 
                    quantity=Decimal(row["quantity"]),
                    )

        finally:
            connection.close()

        return observations


    def get_snapshots(self):
        '''returns a list of snapshots for the initial book
        then initialises them into the book'''
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            cursor = self.get_book_events(connection=connection,
                                          session_id=self.session_id,
                                          event_type="snapshot")

            

            # clear then apply snapshots
            self.book.reconstruct_initial(cursor)
            start = get_boundary_time(connection, self.session_id, "start")
            self.start_time = datetime.fromisoformat(start)

        finally:
            connection.close()


    def replay(self, interval: int):
        self.get_snapshots()
        observations = self.generate_replay(interval)

        return observations