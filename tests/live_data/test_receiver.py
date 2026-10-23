import sqlite3
import threading

import pytest

from receiver import dataReceiver
import storage


@pytest.fixture
def database(tmp_path, monkeypatch):
    # Use the real schema, but keep all collection writes in a temporary DB.
    schema = storage.connection.execute(
        "SELECT sql FROM sqlite_master WHERE name IN ('sessions', 'book_events')"
    ).fetchall()
    monkeypatch.chdir(tmp_path)
    with sqlite3.connect("market_data.db") as connection:
        for (statement,) in schema:
            connection.execute(statement)
    return tmp_path / "market_data.db"


def message(update_count):
    return {
        "channel": "l2_data",
        "events": [{
            "product_id": "BTC-USD",
            "type": "snapshot",
            "updates": [{
                "event_time": "2026-01-01T00:00:00+00:00",
                "side": "bid",
                "price_level": str(100 + index),
                "new_quantity": "1",
            } for index in range(update_count)],
        }],
    }


@pytest.mark.parametrize("update_count, batch_lengths", [
    (4, [2, 2]),
    (5, [2, 2, 1]),
])
def test_run_saves_ordered_batches_and_finishes(database, monkeypatch,
                                               update_count, batch_lengths):
    receiver = dataReceiver("BTC-USD", batch_size=2)
    batches = []
    writer_threads = []
    insert = storage.insert_events_batch

    def save(connection, batch):
        batches.append(batch)
        writer_threads.append(threading.get_ident())
        insert(connection, batch)

    monkeypatch.setattr(storage, "insert_events_batch", save)
    monkeypatch.setattr(receiver, "fetch_updates",
                        lambda: receiver.messages.put(message(update_count)))

    receiver.run()

    # Retained references must still contain their original rows after shutdown.
    assert [len(batch) for batch in batches] == batch_lengths
    assert len({id(batch) for batch in batches}) == len(batches)
    assert all(batch is not receiver.batch for batch in batches)
    assert all(thread != threading.get_ident() for thread in writer_threads)
    assert len(set(writer_threads)) <= 1
    assert receiver.messages.unfinished_tasks == 0
    assert receiver.batches.unfinished_tasks == 0

    with sqlite3.connect(database) as connection:
        rows = connection.execute(
            "SELECT id, session_id, price FROM book_events ORDER BY id"
        ).fetchall()
        session = connection.execute(
            "SELECT status, snapshot_row_count FROM sessions WHERE id = ?",
            (receiver.session_id,),
        ).fetchone()

    assert rows == [(index, receiver.session_id, str(100 + index))
                    for index in range(update_count)]
    assert session == ("complete", update_count)


def test_empty_stream_stops_both_workers(database):
    receiver = dataReceiver("BTC-USD", batch_size=2)
    writer = threading.Thread(target=receiver.save_batches)
    processor = threading.Thread(target=receiver.process_updates)
    receiver.messages.put(None)

    writer.start()
    processor.start()
    processor.join(timeout=5)
    writer.join(timeout=5)

    assert not processor.is_alive()
    assert not writer.is_alive()
    assert receiver.worker_errors.empty()
    assert receiver.messages.unfinished_tasks == 0
    assert receiver.batches.unfinished_tasks == 0


@pytest.mark.parametrize("failing_worker", ["writer", "processor"])
def test_worker_failure_reaches_caller_without_completing_session(
        database, monkeypatch, failing_worker):
    receiver = dataReceiver("BTC-USD", batch_size=2)
    failure = ValueError("worker failed")

    def fail(*args):
        raise failure

    if failing_worker == "writer":
        monkeypatch.setattr(storage, "insert_events_batch", fail)
    else:
        monkeypatch.setattr(receiver, "process_message", fail)
    monkeypatch.setattr(receiver, "fetch_updates",
                        lambda: receiver.messages.put(message(5)))

    with pytest.raises(RuntimeError, match="Data collection failed") as caught:
        receiver.run()

    assert caught.value.__cause__ is failure
    with sqlite3.connect(database) as connection:
        status = connection.execute(
            "SELECT status FROM sessions WHERE id = ?", (receiver.session_id,)
        ).fetchone()[0]
    assert status == "recording"
