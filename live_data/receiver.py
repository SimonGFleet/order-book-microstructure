from coinbase.websocket import WSClient
import threading
from collections import deque
from queue import Queue 
import json
from decimal import Decimal



class dataReceiver:
    def __init__(self, product_id: str, session_id: str, batch_size: int = 1000):
        self.product_id = product_id    # ie "BTC-USD"
        self.session_id = session_id    # can be either numeric string or descriptor
        self.event_id = 0   # increments one for each row we send to db
        self.messages = Queue()
        self.batch = []
        self.batch_size = batch_size

    def on_message(self, msg):
        self.messages.put(json.loads(msg))

    def next_event_id(self):
        event_id = self.event_id
        self.event_id += 1
        return event_id

    def fetch_updates(self):
        client = WSClient(on_message=self.on_message)
        client.open()

        try: 
            client.level2(product_ids=["BTC-USD"])
            client.heartbeats()

            while True:
                command = input("Type stop to finish: ")

                if command.strip().lower() == "stop":
                    break

        finally:
            client.close()


    def process_message(self, update: dict, event_id: int):
        # (session_id, product_id, event_type, event_time, side, price, quantity)
        # message 
        
        #processed_message = (self.session_id, self.next_event_id())
        pass

    def process_updates(self):
        event_id = 0
        batch = []
        while True:
            msg = self.messages.get()
            try:
                self.process_message(msg)

            finally:
                self.messages.task_done()


