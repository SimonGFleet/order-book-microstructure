- address market orders affecting how 
- works fine for limit orders


- when we submit a market order, the effective cash should not change immediately. 
- we need to not spend more than we can spend.
- we need to work out how much we have spent.
- maybe when we are placing a market order we say how much we can spend? default to none then if we dont specify this we can go negative.


- we already ahve something to update the cash properly, we just go through the trades we have made.


- check market asks too.





- we could pass in max_spend to the matching engine. Then we reduce it as we go through. I think this is a problem for tomorrow.