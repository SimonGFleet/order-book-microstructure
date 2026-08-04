from order_book import OrderBook



class Strategy:
    def __init__(self):
        self.agent_state = None
        self.open_orders = []


    def decide(self, agent_state, book: OrderBook):
        pass



# maybe at each timestep we are deciding what to do so we should then 