1. need to address how market orders affect effective cash. when we do a market bid, the effective cash just jumps to zero, but then when we process this we will still ahve zero effective cash and not be able to buy anything

2. Agents are able to trade with themselves



3. fix how orders get their ids. to cancel an order we need to know the id - maybe make the simulation generate the order ids?
top down structure of where order id generation comes from:
    1. We run get requests  in the simulation layer - this goes through each agent and creates a request object if they want it
    2. this calls agent.decide action
    3. the agent then calls its instance of a strategy and decides what to do



4. when deciding action, the agent should have an idea of what open orders they have