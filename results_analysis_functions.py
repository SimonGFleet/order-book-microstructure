from statistics import mean, stdev



def sharpe_ratio(wealths) -> float:
    returns = [
        (current - previous) / previous
        for previous, current in zip(wealths, wealths[1:])
    ]

    sharpe_ratio = None

    if len(returns) >= 2:
        volatility = stdev(returns)
        if volatility > 0:
            sharpe_ratio = mean(returns) / volatility

    return sharpe_ratio


def max_drawdown(wealths) -> float:
    peak = wealths[0]
    max_drawdown = 0.0

    for wealth in wealths[1:]:
        peak = max(peak, wealth)
        drawdown = (peak - wealth) / peak
        max_drawdown = max(max_drawdown, drawdown)

    return max_drawdown